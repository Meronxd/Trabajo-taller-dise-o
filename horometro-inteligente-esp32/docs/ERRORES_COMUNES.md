# Errores comunes

- **Acceso denegado a COM3 al subir**: detener Python con Ctrl+C y cerrar el monitor serie de Arduino y otros programas del puerto. Reintentar Subir.
- **No aparece el puerto**: comprobar cable de datos, puerto USB y controlador correspondiente al puente USB-serie de la placa; las luces solo prueban alimentación.
- **Waiting for gdb server / OpenOCD**: utilizar la flecha Subir, no el botón de depuración.
- **Connecting sin avanzar**: mantener BOOT, pulsar y soltar RST y soltar BOOT cuando comience la escritura.
- **py no reconocido**: usar python. El lanzador también intenta py -3 si corresponde.
- **No module named serial**: dentro de pc ejecutar python -m pip install -r requirements.txt.
- **Panel sin datos**: comprobar puerto, monitor serie cerrado y una sola instancia del puente. Mostrar puertos con python horometro_pc.py --ports.
- **Puerto HTTP ocupado**: cerrar el panel previo o ejecutar con --http-port 8001 y abrir esa dirección.
- **No cambia ON/OFF**: verificar GPIO4 y GND, continuidad del switch y grupos internos de la protoboard.
- **No aparece Horometro-UAI**: verificar sketch BLE, permisos de Bluetooth, proximidad y que otro visor no esté conectado. Seleccionar dentro de phyphox.
- **No suena el visor**: usar Horometro_con_alarma.phyphox, pulsar ▶, subir volumen multimedia y probar el botón. El archivo básico no tiene sonido.
- **No hay notificación con el iPhone bloqueado**: phyphox no ofrece esa función en estos visores; revisar el complemento opcional, permisos, Wi-Fi local, modo silencio, Concentración y Local Push.
