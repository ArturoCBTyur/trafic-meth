@echo off
REM Construye el ejecutable autocontenido en Windows.
REM Uso:  build.bat
setlocal
cd /d "%~dp0"

echo >> Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo >> Construyendo con PyInstaller (onefile)...
python -m PyInstaller --clean -y trafic_meth.spec
if errorlevel 1 goto :error

echo.
echo >> Listo. Ejecutable en: dist\SmartIntersection.exe
goto :eof

:error
echo.
echo >> ERROR durante la construccion.
exit /b 1
