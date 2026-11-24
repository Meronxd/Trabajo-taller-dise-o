@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Horometro - Panel de mantenimiento
pushd "%~dp0" || goto :error
if not exist "horometro_pc.py" goto :carpeta
if not exist "panel.html" goto :carpeta
set "PYRUN=python"
python -c "import sys;sys.exit(sys.version_info[:2] < (3,10))" >nul 2>&1
if not errorlevel 1 goto :listo
set "PYRUN=py -3"
py -3 -c "import sys;sys.exit(sys.version_info[:2] < (3,10))" >nul 2>&1
if not errorlevel 1 goto :listo
echo No se encontro Python 3.10 o superior en este computador.
goto :error

:listo
rem Si ya esta funcionando nuestro panel local, abrirlo sin disputar COM3.
%PYRUN% -c "import json,urllib.request as u,webbrowser as w; url='http://127.0.0.1:8000'; d=json.load(u.urlopen(url+'/api/state',timeout=1)); assert isinstance(d,dict) and {'connected','status','events','history_error'}.issubset(d); w.open(url)" >nul 2>&1
if not errorlevel 1 exit /b 0
%PYRUN% -c "from serial.tools import list_ports" >nul 2>&1
if not errorlevel 1 goto :abrir
echo Falta pyserial. La primera instalacion necesita Internet.
choice /c SN /m "Instalar ahora"
if errorlevel 2 goto :error
%PYRUN% -m pip install -r requirements.txt
if errorlevel 1 goto :error

:abrir
echo Conecte la ESP32. Cierre el Monitor Serie de Arduino para liberar COM3.
echo Deje esta ventana abierta durante la prueba. Para terminar, cierrela.
%PYRUN% horometro_pc.py --port COM3
if errorlevel 1 goto :error
exit /b 0

:carpeta
echo Coloque este archivo en la carpeta pc del horometro, junto a horometro_pc.py y panel.html.
:error
pause
exit /b 1
