#!/bin/bash
set -e

echo "============================================"
echo "  Instalando dependencias..."
echo "============================================"

pip3 install flask pywebview || pip install flask pywebview

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Fallo la instalacion de dependencias."
    echo "Asegurate de tener Python 3 y pip instalados."
    exit 1
fi

echo ""
echo "============================================"
echo "  Iniciando Compilador..."
echo "  Abre http://localhost:5000 en tu navegador"
echo "============================================"
python3 app.py
