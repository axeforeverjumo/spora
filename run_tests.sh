#!/bin/bash

echo "======================================"
echo "Actualizando módulo spora_segment..."
echo "======================================"

# Esperar a que el contenedor esté listo
sleep 5

# Ejecutar actualización del módulo con tests
docker exec -i spora_odoo bash << 'EOF'
# Detener el servidor actual
pkill -f "odoo-bin"
sleep 2

# Ejecutar actualización con tests
odoo -d spora -r odoo -w odoo --db_host db --test-enable --stop-after-init -u spora_segment 2>&1 | tee /tmp/test_output.log

# Extraer resultados de los tests
echo ""
echo "======================================"
echo "RESUMEN DE TESTS:"
echo "======================================"
grep -E "(test_outline|ran [0-9]+ test|PASSED|FAILED|ERROR)" /tmp/test_output.log | tail -30

# Reiniciar servidor normal
nohup odoo -d spora -r odoo -w odoo --db_host db --dev=all > /dev/null 2>&1 &
EOF

echo ""
echo "Módulo actualizado. Odoo disponible en http://localhost:8069"
