# Diseño: Numeración Outline y Reporte Jerárquico

**Fecha:** 2025-02-09
**Versión:** 1.2.0
**Estado:** Validado - Listo para implementar

## Resumen

Implementar sistema de numeración automática tipo outline (1, 1.1, 1.2, 2, 2.1, etc.) para segmentos de presupuesto y reporte de impresión con jerarquía visual.

## Objetivos

1. **Numeración automática visible**: Cada segmento tiene un número único que refleja su posición jerárquica
2. **Diferenciación clara**: Segmentos con mismo nombre pero diferente padre se distinguen por número (1.1. Diseño vs 2.1. Diseño)
3. **Impresión profesional**: PDF con tabla indentada mostrando jerarquía y totales destacados
4. **Actualización automática**: Números se recalculan al reordenar o mover segmentos

## Componente 1: Campo Outline Number

### Modelo: `sale.order.segment`

**Nuevo campo:**
```python
outline_number = fields.Char(
    string='Nº',
    compute='_compute_outline_number',
    store=True,
    recursive=True,
    help='Numeración automática tipo outline (1, 1.1, 1.2, etc.)',
)
```

**Método de cálculo:**
```python
@api.depends('parent_id', 'parent_id.outline_number', 'sequence', 'order_id')
def _compute_outline_number(self):
    """Calcula número outline basado en jerarquía y sequence."""
    for segment in self:
        if not segment.parent_id:
            # Segmento raíz: contar posición entre hermanos raíz
            siblings = segment.order_id.segment_ids.filtered(
                lambda s: not s.parent_id
            ).sorted('sequence')
            position = siblings.ids.index(segment.id) + 1
            segment.outline_number = str(position)
        else:
            # Hijo: padre.número + "." + posición entre hermanos
            siblings = segment.parent_id.child_ids.sorted('sequence')
            position = siblings.ids.index(segment.id) + 1
            segment.outline_number = f"{segment.parent_id.outline_number}.{position}"
```

**Ordenamiento por defecto:**
```python
_order = 'outline_number, sequence, id'  # Actualizar en modelo
```

**Display name mejorado:**
```python
def _compute_display_name(self):
    """Display como 'SO001 / 1.1. Segment Name'."""
    for segment in self:
        if segment.outline_number and segment.order_id:
            segment.display_name = f'{segment.order_id.name} / {segment.outline_number}. {segment.name}'
        elif segment.order_id:
            segment.display_name = f'{segment.order_id.name} / {segment.name}'
        else:
            segment.display_name = segment.name
```

## Componente 2: Vistas de Edición

### Vista Tree Jerárquica

**Archivo:** `views/sale_order_segment_views.xml`

```xml
<record id="view_sale_order_segment_tree" model="ir.ui.view">
    <field name="name">sale.order.segment.tree</field>
    <field name="model">sale.order.segment</field>
    <field name="arch" type="xml">
        <tree string="Segmentos" default_order="outline_number">
            <field name="outline_number" string="Nº" width="80px"/>
            <field name="name"/>
            <field name="product_count" string="Items"/>
            <field name="subtotal" sum="Subtotal"/>
            <field name="total" sum="Total"
                   decoration-bf="1"
                   decoration-info="level == 1"
                   decoration-primary="level == 2"/>
            <field name="level" invisible="1"/>
        </tree>
    </field>
</record>
```

**Resultado visual:**
```
Nº    Nombre              Items    Subtotal    Total
1     Fase 1              5        500€        5.000€
1.1   Diseño              3        200€        2.000€
1.2   Desarrollo          2        300€        3.000€
2     Fase 2              4        400€        3.000€
2.1   Diseño              2        200€        1.000€
```

## Componente 3: Reporte de Impresión

### Archivos a crear:

1. **report/sale_order_segment_report.xml** - Definición del reporte
2. **report/sale_order_segment_template.xml** - Template QWeb

### Template Principal

```xml
<template id="report_saleorder_document_segment">
    <t t-call="web.external_layout">
        <div class="page">
            <h2>Presupuesto: <span t-field="doc.name"/></h2>
            <p><strong>Cliente:</strong> <span t-field="doc.partner_id.name"/></p>
            <p><strong>Fecha:</strong> <span t-field="doc.date_order"/></p>

            <table class="table table-sm o_report_block_table">
                <thead>
                    <tr style="border-bottom: 2px solid black;">
                        <th style="width: 8%">Nº</th>
                        <th style="width: 47%">Descripción</th>
                        <th class="text-right" style="width: 10%">Cant.</th>
                        <th class="text-right" style="width: 15%">Precio Unit.</th>
                        <th class="text-right" style="width: 20%">Total</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Segmentos raíz ordenados -->
                    <t t-foreach="doc.segment_ids.filtered(lambda s: not s.parent_id).sorted('outline_number')" t-as="segment">
                        <t t-call="spora_segment.segment_line_recursive"/>
                    </t>

                    <!-- Total general -->
                    <tr style="border-top: 2px solid black; font-weight: bold; font-size: 14pt;">
                        <td colspan="4" class="text-right">TOTAL PRESUPUESTO:</td>
                        <td class="text-right">
                            <span t-field="doc.amount_total"
                                  t-options='{"widget": "monetary", "display_currency": doc.currency_id}'/>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </t>
</template>
```

### Template Recursivo

```xml
<template id="segment_line_recursive">
    <!-- Línea del segmento (bold, fondo gris, total destacado) -->
    <tr style="font-weight: bold; background-color: #f5f5f5;">
        <td style="vertical-align: top;">
            <span t-field="segment.outline_number"/>
        </td>
        <td t-att-style="'padding-left: %spx; vertical-align: top;' % (segment.level * 15)">
            <span t-field="segment.name"/>
        </td>
        <td></td>
        <td></td>
        <td class="text-right" style="vertical-align: top;">
            <strong>
                <span t-field="segment.total"
                      t-options='{"widget": "monetary", "display_currency": segment.currency_id}'/>
            </strong>
        </td>
    </tr>

    <!-- Productos del segmento (indentados con bullet) -->
    <t t-foreach="segment.line_ids.sorted(lambda l: l.sequence)" t-as="line">
        <tr>
            <td></td>
            <td t-att-style="'padding-left: %spx;' % ((segment.level + 1) * 15)">
                <span style="color: #666;">• </span>
                <span t-field="line.product_id.name"/>
            </td>
            <td class="text-right">
                <span t-field="line.product_uom_qty"/>
                <span t-field="line.product_uom" groups="uom.group_uom"/>
            </td>
            <td class="text-right">
                <span t-field="line.price_unit"
                      t-options='{"widget": "monetary", "display_currency": line.currency_id}'/>
            </td>
            <td class="text-right">
                <span t-field="line.price_subtotal"
                      t-options='{"widget": "monetary", "display_currency": line.currency_id}'/>
            </td>
        </tr>
    </t>

    <!-- Recursión: procesar hijos ordenados por outline_number -->
    <t t-foreach="segment.child_ids.sorted('outline_number')" t-as="segment">
        <t t-call="spora_segment.segment_line_recursive"/>
    </t>
</template>
```

### Definición del Reporte

```xml
<record id="action_report_sale_order_segment" model="ir.actions.report">
    <field name="name">Presupuesto Jerárquico</field>
    <field name="model">sale.order</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">spora_segment.report_saleorder_document_segment</field>
    <field name="report_file">spora_segment.report_saleorder_document_segment</field>
    <field name="binding_model_id" ref="sale.model_sale_order"/>
    <field name="binding_type">report</field>
</record>
```

## Componente 4: Tests

**Archivo:** `tests/test_outline_numbering.py`

```python
def test_outline_number_root_segments(self):
    """Verify root segments get sequential numbers 1, 2, 3."""
    seg1 = self.env['sale.order.segment'].create({
        'name': 'Fase 1',
        'order_id': self.order.id,
        'sequence': 10,
    })
    seg2 = self.env['sale.order.segment'].create({
        'name': 'Fase 2',
        'order_id': self.order.id,
        'sequence': 20,
    })

    self.assertEqual(seg1.outline_number, '1')
    self.assertEqual(seg2.outline_number, '2')

def test_outline_number_nested(self):
    """Verify nested segments get hierarchical numbers 1.1, 1.2."""
    parent = self.env['sale.order.segment'].create({
        'name': 'Parent',
        'order_id': self.order.id,
        'sequence': 10,
    })
    child1 = self.env['sale.order.segment'].create({
        'name': 'Child 1',
        'order_id': self.order.id,
        'parent_id': parent.id,
        'sequence': 10,
    })
    child2 = self.env['sale.order.segment'].create({
        'name': 'Child 2',
        'order_id': self.order.id,
        'parent_id': parent.id,
        'sequence': 20,
    })

    self.assertEqual(parent.outline_number, '1')
    self.assertEqual(child1.outline_number, '1.1')
    self.assertEqual(child2.outline_number, '1.2')

def test_outline_number_resequence(self):
    """Verify numbers update when sequence changes."""
    seg1 = self.env['sale.order.segment'].create({
        'name': 'First',
        'order_id': self.order.id,
        'sequence': 10,
    })
    seg2 = self.env['sale.order.segment'].create({
        'name': 'Second',
        'order_id': self.order.id,
        'sequence': 20,
    })

    # Swap order
    seg2.sequence = 5

    self.assertEqual(seg2.outline_number, '1')
    self.assertEqual(seg1.outline_number, '2')

def test_outline_number_three_levels(self):
    """Verify deep hierarchy 1.1.1, 1.1.2."""
    level1 = self.env['sale.order.segment'].create({
        'name': 'L1',
        'order_id': self.order.id,
    })
    level2 = self.env['sale.order.segment'].create({
        'name': 'L2',
        'order_id': self.order.id,
        'parent_id': level1.id,
    })
    level3_1 = self.env['sale.order.segment'].create({
        'name': 'L3-1',
        'order_id': self.order.id,
        'parent_id': level2.id,
        'sequence': 10,
    })
    level3_2 = self.env['sale.order.segment'].create({
        'name': 'L3-2',
        'order_id': self.order.id,
        'parent_id': level2.id,
        'sequence': 20,
    })

    self.assertEqual(level1.outline_number, '1')
    self.assertEqual(level2.outline_number, '1.1')
    self.assertEqual(level3_1.outline_number, '1.1.1')
    self.assertEqual(level3_2.outline_number, '1.1.2')
```

## Actualización del Módulo

**__manifest__.py:**
```python
{
    'name': 'Spora Segment',
    'version': '1.2.0',  # Bump version
    'summary': 'Hierarchical segments with outline numbering and print reports',
    'data': [
        # ... existing data files ...
        'report/sale_order_segment_report.xml',
    ],
}
```

## Migración y Compatibilidad

- **No requiere migración de datos**: Campo computed con `store=True` se calcula automáticamente
- **Presupuestos existentes**: Recibirán numeración al cargar la vista
- **Backward compatible**: Vistas antiguas siguen funcionando

## Casos de Uso

### Escenario 1: Mismo nombre, diferente padre
```
1. Proyecto Web
   1.1. Diseño  ← Diseño para web
2. Proyecto Móvil
   2.1. Diseño  ← Diseño para móvil (diferenciado claramente)
```

### Escenario 2: Reordenamiento
```
Antes:
1. Setup (sequence=10)
2. Core (sequence=20)

Usuario cambia Core.sequence = 5

Después (automático):
1. Core
2. Setup
```

### Escenario 3: Impresión PDF
```
1. FASE 1 ................................. 10.000€
   • Consultoría (10h × 100€) ..............  1.000€
   1.1. DISEÑO ............................  5.000€
       • Mockups (20h × 150€) .............  3.000€
       • Wireframes (10h × 200€) ..........  2.000€
   1.2. DESARROLLO ........................  4.000€
```

## Checklist de Implementación

- [ ] Añadir campo `outline_number` al modelo
- [ ] Implementar método `_compute_outline_number`
- [ ] Actualizar `_compute_display_name`
- [ ] Modificar `_order` del modelo
- [ ] Actualizar vista tree de segmentos
- [ ] Crear directorio `report/`
- [ ] Crear template de reporte principal
- [ ] Crear template recursivo
- [ ] Crear definición de reporte
- [ ] Añadir archivo de reporte al manifest
- [ ] Crear archivo de tests
- [ ] Ejecutar tests
- [ ] Actualizar módulo en Odoo
- [ ] Validar en presupuesto real
- [ ] Generar PDF de prueba
- [ ] Actualizar README con v1.2.0
- [ ] Commit y push a GitHub

## Resultado Esperado

**Vista de edición:**
- Columna "Nº" siempre visible con numeración outline
- Ordenamiento automático por número
- Display name en selects: "S00001 / 1.1. Diseño"

**PDF de impresión:**
- Tabla profesional con indentación visual
- Totales de segmentos destacados en negrita
- Productos con bullet point
- Jerarquía clara hasta 4 niveles
- Total general al final

**Experiencia de usuario:**
- Numeración automática, sin intervención manual
- Diferenciación inmediata de segmentos similares
- Presupuestos profesionales para clientes
