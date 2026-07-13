#!/usr/bin/env bash
# Construye el ejecutable autocontenido en Linux o macOS.
# Uso:  ./build.sh
set -euo pipefail

cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

echo ">> Instalando dependencias..."
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

echo ">> Construyendo con PyInstaller (onefile)..."
"$PY" -m PyInstaller --clean -y trafic_meth.spec

echo ""
echo ">> Listo. Ejecutable en: dist/SmartIntersection"
echo "   Córrelo con:  ./dist/SmartIntersection"
