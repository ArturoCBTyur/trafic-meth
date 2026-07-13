import subprocess
import sys
import os

# Cambiar al directorio del script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Activar el venv y ejecutar el frontend
venv_python = os.path.join(".venv", "Scripts", "python.exe")
subprocess.run([venv_python, "frontend.py"])
