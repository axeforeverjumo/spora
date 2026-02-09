# Pasos de Validación - Feature Outline Numbering v1.2.0

## Estado Actual

✅ **Implementación completada**
- Código actualizado en todos los archivos
- Tests creados (8 test cases)
- Reportes QWeb implementados
- Manifest actualizado a v1.2.0

⏳ **Pendiente de validación**
- Actualización del módulo en Odoo
- Ejecución de tests
- Validación visual en UI
- Generación de PDF de ejemplo

---

## PASO 1: Actualizar Módulo en Odoo

### Método 1: Desde la UI (Recomendado)

1. **Acceder a Odoo**
   - Abrir navegador: http://localhost:8069
   - Login con credenciales de administrador

2. **Activar Modo Desarrollador**
   - Settings > General Settings
   - Scroll hasta el final
   - Click en "Activate the developer mode"

3. **Actualizar Módulo**
   - Settings > Apps
   - Buscar "spora" o "segment"
   - Encontrar "Spora - Hierarchical Budget Segments"
   - Click en botón "Upgrade" (icono de upgrade)
   - Esperar confirmación (puede tardar 10-30 segundos)

4. **Verificar Actualización**
   - Revisar que la versión sea `18.0.1.2.0`
   - No debe haber mensajes de error en el log

### Método 2: Desde CLI (Alternativo)

```bash
# Opción A: Con docker compose
docker compose stop odoo
docker compose run --rm odoo odoo -d spora -r odoo -w odoo --db_host db -u spora_segment --stop-after-init
docker compose start odoo

# Opción B: Dentro del contenedor
docker exec -it spora_odoo bash
odoo -d spora -r odoo -w odoo --db_host db -u spora_segment --stop-after-init
exit
docker compose restart odoo
```

---

## PASO 2: Ejecutar Tests

### Desde CLI

```bash
# Detener servidor
docker exec spora_odoo pkill -f odoo-bin

# Ejecutar tests
docker exec spora_odoo odoo -d spora -r odoo -w odoo --db_host db \
  --test-enable --stop-after-init -u spora_segment \
  --log-level=test 2>&1 | tee test_results.log

# Ver resultados de tests de outline numbering
grep -A 2 "test_outline" test_results.log

# Reiniciar servidor
docker compose restart odoo
```

### Resultados Esperados

Debes ver algo como:

```
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_root_segments: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_nested: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_resequence: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_three_levels: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_multiple_trees: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_display_name: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_ordering: ok
```

**Total esperado:** 8 tests PASSED

---

## PASO 3: Validar Numeración en Vista Tree

### 3.1 Crear Presupuesto de Prueba

1. **Ir a Sales > Quotations**
2. **Create** nuevo presupuesto
3. **Seleccionar cliente** (cualquiera)

### 3.2 Crear Segmentos Jerárquicos

**Pestaña "Segments" > Add a line**

Crear esta estructura:

```
1. Fase 1 - Diseño (sequence=10)
   1.1. Wireframes (sequence=10, parent=Fase 1)
   1.2. Mockups (sequence=20, parent=Fase 1)
2. Fase 2 - Desarrollo (sequence=20)
   2.1. Frontend (sequence=10, parent=Fase 2)
   2.2. Backend (sequence=20, parent=Fase 2)
       2.2.1. API (sequence=10, parent=Backend)
       2.2.2. Database (sequence=20, parent=Backend)
3. Fase 3 - Testing (sequence=30)
```

**Cómo crear:**

1. Click "Add a line" para crear "Fase 1"
   - Name: `Fase 1 - Diseño`
   - Sequence: `10`
   - Parent Segment: *(dejar vacío)*

2. Click "Add a line" para crear "Wireframes"
   - Name: `Wireframes`
   - Sequence: `10`
   - Parent Segment: `Fase 1 - Diseño`

3. *(Repetir para todos los segmentos...)*

### 3.3 Verificar Numeración

**En la vista tree de segmentos, debes ver:**

| Nº    | Name                | Subtotal | Total |
|-------|---------------------|----------|-------|
| 1     | Fase 1 - Diseño     | 0.00     | 0.00  |
| 1.1   | Wireframes          | 0.00     | 0.00  |
| 1.2   | Mockups             | 0.00     | 0.00  |
| 2     | Fase 2 - Desarrollo | 0.00     | 0.00  |
| 2.1   | Frontend            | 0.00     | 0.00  |
| 2.2   | Backend             | 0.00     | 0.00  |
| 2.2.1 | API                 | 0.00     | 0.00  |
| 2.2.2 | Database            | 0.00     | 0.00  |
| 3     | Fase 3 - Testing    | 0.00     | 0.00  |

**✅ VALIDADO si:**
- La columna "Nº" aparece como primera columna (después de handle)
- Los números reflejan correctamente la jerarquía
- El ancho de la columna es aproximadamente 80px

---

## PASO 4: Validar Display Name

### 4.1 Crear Tarea de Proyecto

1. **Ir a Project**
2. **Abrir proyecto** vinculado al presupuesto anterior
3. **Crear nueva tarea** o abrir existente
4. **Campo "Budget Segment"** debe estar visible

### 4.2 Verificar Display Name

1. **Click en campo "Budget Segment"**
2. **Ver el dropdown**

**Debe mostrar:**
```
S00001 / 1. Fase 1 - Diseño
S00001 / 1.1. Wireframes
S00001 / 1.2. Mockups
S00001 / 2. Fase 2 - Desarrollo
S00001 / 2.1. Frontend
S00001 / 2.2. Backend
S00001 / 2.2.1. API
S00001 / 2.2.2. Database
S00001 / 3. Fase 3 - Testing
```

**✅ VALIDADO si:**
- Cada opción incluye el número outline después del código de presupuesto
- Formato es exactamente: `CÓDIGO / NÚMERO. NOMBRE`

---

## PASO 5: Validar Reordenamiento Automático

### 5.1 Cambiar Sequence

1. **Editar presupuesto** del paso anterior
2. **Editar segmento "Fase 2 - Desarrollo"**
3. **Cambiar Sequence** de `20` a `5`
4. **Guardar**

### 5.2 Verificar Recálculo

**Abrir vista tree de segmentos**

**Antes (sequence 20):**
```
1. Fase 1 - Diseño
2. Fase 2 - Desarrollo
3. Fase 3 - Testing
```

**Después (sequence 5):**
```
1. Fase 2 - Desarrollo
  1.1. Frontend
  1.2. Backend
2. Fase 1 - Diseño
  2.1. Wireframes
  2.2. Mockups
3. Fase 3 - Testing
```

**✅ VALIDADO si:**
- Los números se recalculan automáticamente
- Los hijos mantienen la numeración correcta respecto al padre
- No es necesario refrescar manualmente

---

## PASO 6: Validar Reporte PDF

### 6.1 Añadir Productos a Segmentos

**Para hacer el PDF más realista, añadir productos:**

1. **Pestaña "Order Lines"** del presupuesto
2. **Add a line** para cada producto:

```
Fase 1 - Diseño:
  - Producto: "Consultoría Diseño" | Qty: 10 | Price: 100.00 | Segment: 1. Fase 1 - Diseño

Wireframes:
  - Producto: "Wireframe Mockup" | Qty: 5 | Price: 150.00 | Segment: 1.1. Wireframes

Mockups:
  - Producto: "Mockup Design" | Qty: 8 | Price: 120.00 | Segment: 1.2. Mockups

Fase 2 - Desarrollo:
  - Producto: "Consultoría Dev" | Qty: 20 | Price: 80.00 | Segment: 2. Fase 2 - Desarrollo

Frontend:
  - Producto: "Desarrollo Frontend" | Qty: 15 | Price: 100.00 | Segment: 2.1. Frontend

Backend:
  - Producto: "Desarrollo Backend" | Qty: 20 | Price: 120.00 | Segment: 2.2. Backend

API:
  - Producto: "Implementación API" | Qty: 12 | Price: 150.00 | Segment: 2.2.1. API

Database:
  - Producto: "Diseño DB" | Qty: 8 | Price: 100.00 | Segment: 2.2.2. Database
```

### 6.2 Generar PDF

1. **Botón Print** (icono de impresora)
2. **Seleccionar "Presupuesto Jerárquico"**
3. **Wait for PDF** to generate
4. **Descargar PDF** o **Abrir en navegador**

### 6.3 Verificar Contenido del PDF

**Cabecera:**
- ✅ Título: "Presupuesto: S00XXX"
- ✅ Cliente: Nombre del cliente
- ✅ Email y teléfono (si disponibles)
- ✅ Fecha del presupuesto
- ✅ Estado del presupuesto

**Tabla:**
- ✅ Columnas: Nº | Descripción | Cant. | Precio Unit. | Total
- ✅ Ancho aproximado: 8% | 47% | 10% | 15% | 20%

**Segmentos:**
- ✅ Fondo gris (#f5f5f5)
- ✅ Negrita en nombre
- ✅ Total del segmento en negrita a la derecha
- ✅ Indentación proporcional al nivel (15px por nivel)

**Productos:**
- ✅ Bullet point "•" antes del nombre
- ✅ Indentación adicional respecto al segmento padre
- ✅ Cantidad, precio unitario y total alineados a la derecha
- ✅ Color gris (#666) para el bullet

**Jerarquía Visual (Ejemplo):**

```
1. FASE 1 - DISEÑO ........................... 2.710€
    • Consultoría Diseño (10 × 100€) ..........  1.000€
  1.1. WIREFRAMES ..............................  750€
      • Wireframe Mockup (5 × 150€) ...........   750€
  1.2. MOCKUPS .................................  960€
      • Mockup Design (8 × 120€) ..............   960€

2. FASE 2 - DESARROLLO ....................... 6.900€
    • Consultoría Dev (20 × 80€) .............. 1.600€
  2.1. FRONTEND ............................... 1.500€
      • Desarrollo Frontend (15 × 100€) ....... 1.500€
  2.2. BACKEND ................................ 3.800€
      • Desarrollo Backend (20 × 120€) ........ 2.400€
    2.2.1. API ................................ 1.800€
          • Implementación API (12 × 150€) .... 1.800€
    2.2.2. DATABASE ...........................  800€
          • Diseño DB (8 × 100€) ..............   800€

─────────────────────────────────────────────────────
TOTAL PRESUPUESTO: ........................... 9.610€
```

**Total General:**
- ✅ Línea separadora gruesa (2px)
- ✅ Texto "TOTAL PRESUPUESTO:" alineado a la derecha
- ✅ Fuente grande (14pt) y negrita
- ✅ Total correcto (suma de todos los segmentos raíz)

**✅ VALIDADO si:**
- El PDF se genera sin errores
- La jerarquía es visualmente clara
- Los totales son correctos
- La indentación es proporcional
- Los segmentos destacan sobre los productos

---

## PASO 7: Tests Adicionales

### Test 1: Múltiples Presupuestos

**Objetivo:** Verificar que la numeración es independiente por presupuesto

1. Crear **Presupuesto A** con segmentos 1, 2, 3
2. Crear **Presupuesto B** con segmentos 1, 2, 3
3. Verificar que ambos tienen numeración 1, 2, 3 (no 4, 5, 6)

**✅ PASS** si cada presupuesto numera desde 1

### Test 2: Eliminación de Segmento

**Objetivo:** Verificar recálculo al eliminar segmento intermedio

1. Presupuesto con segmentos: 1, 2, 3
2. Eliminar segmento "2"
3. Verificar que "3" se renumera a "2"

**✅ PASS** si se recalcula automáticamente

### Test 3: Mover Segmento (Cambiar Parent)

**Objetivo:** Verificar recálculo al cambiar jerarquía

**Setup:**
```
1. Fase 1
  1.1. Diseño
  1.2. Desarrollo
2. Fase 2
```

**Acción:** Mover "1.2. Desarrollo" de "Fase 1" a "Fase 2"

**Resultado esperado:**
```
1. Fase 1
  1.1. Diseño
2. Fase 2
  2.1. Desarrollo  ← renumerado de 1.2 a 2.1
```

**✅ PASS** si se recalcula al cambiar parent_id

### Test 4: Jerarquía de 4 Niveles

**Objetivo:** Verificar soporte hasta MAX_HIERARCHY_DEPTH=4

**Setup:**
```
1. Level 1
  1.1. Level 2
    1.1.1. Level 3
      1.1.1.1. Level 4
```

**✅ PASS** si se numera correctamente hasta 1.1.1.1

### Test 5: Cambio de Sequence en Hijo

**Objetivo:** Verificar que cambiar sequence de hijo no afecta numeración

**Setup:**
```
1. Parent
  1.1. Child A (sequence=10)
  1.2. Child B (sequence=20)
```

**Acción:** Cambiar Child B sequence a 5

**Resultado esperado:**
```
1. Parent
  1.1. Child B (sequence=5)
  1.2. Child A (sequence=10)
```

**✅ PASS** si se renumeran basándose en nuevo orden de sequence

---

## PASO 8: Checklist Final

Marca cada item cuando esté validado:

### Implementación
- ✅ Campo `outline_number` añadido al modelo
- ✅ Método `_compute_outline_number` implementado
- ✅ Método `_compute_display_name` actualizado
- ✅ `_order` cambiado a `'outline_number, sequence, id'`
- ✅ Vista tree actualizada con columna "Nº"
- ✅ Reporte `sale_order_segment_report.xml` creado
- ✅ Template `sale_order_segment_template.xml` creado
- ✅ Template recursivo `segment_line_recursive` implementado
- ✅ Archivo `test_outline_numbering.py` creado con 8 tests
- ✅ `__manifest__.py` actualizado a v1.2.0
- ✅ README.md actualizado con changelog

### Validación
- [ ] Módulo actualizado en Odoo sin errores
- [ ] 8 tests de outline_numbering ejecutados y pasados
- [ ] Columna "Nº" visible en vista tree
- [ ] Numeración correcta en jerarquía de 3 niveles
- [ ] Display name incluye número outline
- [ ] Recálculo automático al cambiar sequence
- [ ] Reporte PDF generado sin errores
- [ ] Jerarquía visual clara en PDF
- [ ] Totales destacados en negrita en PDF
- [ ] Productos con bullet points en PDF
- [ ] Total general correcto en PDF

---

## PASO 9: Documentación de Resultados

### Captura de Pantalla 1: Vista Tree

**Archivo:** `screenshot_tree_view.png`

Capturar vista tree de segmentos mostrando:
- Columna "Nº" visible
- Numeración correcta (1, 1.1, 1.2, 2, 2.1, etc.)
- Varios niveles de jerarquía

### Captura de Pantalla 2: Display Name

**Archivo:** `screenshot_display_name.png`

Capturar dropdown de campo "Budget Segment" mostrando:
- Formato: "S00001 / 1.1. Segment Name"
- Múltiples segmentos con diferentes niveles

### Captura de Pantalla 3: PDF Header

**Archivo:** `screenshot_pdf_header.png`

Capturar parte superior del PDF con:
- Título del presupuesto
- Datos del cliente
- Fecha
- Cabecera de tabla

### Captura de Pantalla 4: PDF Hierarchy

**Archivo:** `screenshot_pdf_hierarchy.png`

Capturar sección del PDF mostrando:
- Jerarquía de 3+ niveles
- Indentación visual clara
- Segmentos en negrita con fondo gris
- Productos con bullets

### Captura de Pantalla 5: PDF Footer

**Archivo:** `screenshot_pdf_footer.png`

Capturar final del PDF con:
- Total general
- Línea separadora
- Formato destacado

### Output de Tests

**Archivo:** `test_results.log`

Guardar output completo de los tests mostrando:
```
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_root_segments: ok
spora.tests.test_outline_numbering.TestOutlineNumbering.test_outline_number_nested: ok
... (8 tests total)
```

---

## PASO 10: Commit y Push (Opcional)

Si todo está validado:

```bash
cd /Users/juanmanuelojedagarcia/Develop/spora

git add .
git commit -m "feat(spora_segment): implement outline numbering and hierarchical report v1.2.0

- Add outline_number computed field with recursive numbering
- Update display_name to include outline number
- Add 'Nº' column to tree view with 80px width
- Implement hierarchical PDF report with visual indentation
- Create recursive QWeb template for segments and products
- Add 8 unit tests for outline numbering functionality
- Update __manifest__.py to v18.0.1.2.0
- Update README with v1.2.0 changelog

Features:
- Automatic outline numbering (1, 1.1, 1.2, etc.)
- Recomputes on sequence change
- Professional PDF with indented hierarchy
- Segment totals in bold with gray background
- Products with bullet points
- Supports up to 4 hierarchy levels

Tests: 8/8 passed
Refs: docs/plans/2025-02-09-segment-outline-numbering-design.md"

git push origin main
```

---

## Troubleshooting

### "Columna Nº no aparece"

**Síntomas:** La columna "Nº" no se muestra en la vista tree

**Causas posibles:**
1. Módulo no actualizado
2. Cache de navegador
3. Error en XML

**Soluciones:**
```bash
# 1. Forzar actualización completa
docker exec spora_odoo odoo -d spora -u spora_segment --stop-after-init

# 2. Limpiar cache de navegador
Ctrl+Shift+R (o Cmd+Shift+R en Mac)

# 3. Verificar logs
docker logs spora_odoo | grep -i error | tail -20
```

### "outline_number es 0 o 0.0"

**Síntomas:** El campo outline_number muestra "0" o "0.0" en lugar de "1", "1.1", etc.

**Causa:** Segmento no está guardado antes de calcular posición en siblings.ids

**Solución:**
1. Guardar el segmento primero
2. Refrescar la vista
3. Verificar que segment.id está en siblings.ids

### "Tests no se ejecutan"

**Síntomas:** Los tests no aparecen en el output

**Causa:** Módulo no recargado o tests no importados

**Solución:**
```python
# Verificar tests/__init__.py
from . import test_outline_numbering  # ✅ debe estar presente

# Forzar reinstalación
docker exec spora_odoo odoo -d spora -u spora_segment --test-enable --stop-after-init
```

### "PDF no se genera"

**Síntomas:** Error al hacer clic en "Print > Presupuesto Jerárquico"

**Causas posibles:**
1. Template XML con errores de sintaxis
2. Binding no configurado
3. wkhtmltopdf no instalado

**Solución:**
```bash
# Ver logs de error
docker logs spora_odoo | grep -i "qweb\|report" | tail -30

# Verificar binding en Odoo
Settings > Technical > Actions > Reports
Buscar: "Presupuesto Jerárquico"
Verificar: binding_model_id = sale.order
```

### "Recursión infinita en template"

**Síntomas:** PDF se congela o timeout

**Causa:** Template recursivo sin condición de salida

**Verificación:**
```xml
<!-- CORRECTO: Procesa solo hijos existentes -->
<t t-foreach="segment.child_ids.sorted('outline_number')" t-as="segment">
    <t t-call="spora_segment.segment_line_recursive"/>
</t>

<!-- Si child_ids está vacío, no hay recursión → OK -->
```

---

## Contacto y Soporte

**Desarrollador:** Juan Manuel Ojeda
**Empresa:** JUMO Technologies
**Módulo:** spora_segment v1.2.0
**Odoo Version:** 18.0

Para reportar bugs o solicitar features:
1. Crear issue en el repositorio
2. Incluir logs relevantes
3. Adjuntar capturas de pantalla si aplica
