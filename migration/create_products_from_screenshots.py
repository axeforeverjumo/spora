#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear productos en Odoo desde capturas de pantalla
Ejecutar: python3 migration/create_products_from_screenshots.py
"""

import sys
import os

# Productos extraídos de las capturas de pantalla
PRODUCTS = [
    # Imagen 1
    ("Carta informativa personalitzada nova implantació", 0.78),
    ("Carta informativa personalitzada bujols comunitaris", 1.60),
    ("Carta informativa personalitzada porta a porta ja existent", 0.27),
    ("Sobre corporatiu per la carta personalitzada del porta a porta ja existent", 0.23),
    ("Magnètic amb calendari de recollida - 4 models -", 0.77),
    ("Manipulatge sobre + carta + magnètic pap existent", 0.25),
    ("Cartells informatius - 3 models -", 1.73),
    ("Lones informatives 1x4m", 100.00),
    ("Flyer de repesca", 0.70),

    # Imagen 2
    ("Bustiada de la carta informativa", 0.53),
    ("Xerrades informatives obertes a ciutadania", 275.00),
    ("Muntatge de kits", 24.54),
    ("Punt informatiu itinerant amb repartiment i associació de material", 24.54),

    # Imagen 3
    ("Enviament de les cartes a Paprec", 80.00),

    # Imagen 4
    ("Carta informativa", 1.73),
    ("Calendari recollida Sant Antoni - A4 -", 1.05),
    ("Calendari recollida polígon PAEC - 21*10cm -", 0.73),
    ("Calendari recollida Calonge - A4 -", 1.18),

    # Imagen 7
    ("Carta informativa implantació", 0.45),
    ("Díptic informatiu", 0.15),
    ("Lones informatives", 100.00),
    ("Cartells informatius", 0.83),

    # Imagen 8
    ("Preparació dels punts informatius (elements de comunicació)", 100.00),

    # Imagen 9
    ("W-LINK per associar els materials", 8.33),

    # Imagen 10
    ("Personalització del punt informatiu", 350.00),
    ("Vehicle com a punt informatiu", 60.00),
    ("W-LINK per associar dades", 8.33),
    ("Bustiada del flyer informatiu de repesca", 24.54),
]

def create_products():
    """Crea productos en Odoo vía MCP."""

    print("=" * 80)
    print("CREACIÓN DE PRODUCTOS EN ODOO")
    print("=" * 80)
    print(f"\nTotal productos a crear: {len(PRODUCTS)}\n")

    created = []
    duplicates = []
    errors = []

    # Nota: Este script debe ejecutarse desde un contexto con acceso a MCP Odoo
    # Para uso real, usar las herramientas MCP directamente

    for idx, (name, price) in enumerate(PRODUCTS, 1):
        print(f"\n[{idx}/{len(PRODUCTS)}] Procesando: {name}")
        print(f"    Precio: {price:.2f}€")

        # Aquí iría la llamada real a MCP para:
        # 1. Verificar si existe: search_records(model='product.product', domain=[('name', '=', name)])
        # 2. Si no existe: create_record(model='product.product', values={...})

        # Por ahora, solo preparamos el resumen
        created.append((name, price))

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"\n✅ Productos a crear: {len(created)}")
    print(f"⚠️  Duplicados saltados: {len(duplicates)}")
    print(f"❌ Errores: {len(errors)}")

    if created:
        print("\n📦 LISTA DE PRODUCTOS:")
        for idx, (name, price) in enumerate(created, 1):
            print(f"  {idx}. {name} - {price:.2f}€")

    if duplicates:
        print("\n⚠️  DUPLICADOS DETECTADOS:")
        for name in duplicates:
            print(f"  - {name}")

    if errors:
        print("\n❌ ERRORES:")
        for error in errors:
            print(f"  - {error}")

    print("\n" + "=" * 80)
    print("NOTA: Este script es un template. Para crear productos reales,")
    print("ejecutar los comandos MCP manualmente o integrar con create_record.")
    print("=" * 80)

if __name__ == "__main__":
    create_products()
