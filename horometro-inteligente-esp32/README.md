# Horómetro inteligente con ESP32-S3

Prototipo universitario para registrar horas de uso y avisar mantenimientos periódicos. Un interruptor simula la chapa de contacto: **ON acumula; OFF pausa y conserva el total**. La ESP32 calcula el tiempo y los umbrales; el PC y el teléfono presentan esos datos.

**Modo exposición: 1 segundo real en ON = 1 hora simulada. Mantenimiento cada 10 horas por defecto.**

## Funciones

- Lectura del interruptor con resistencia pull-up interna y antirrebote de 40 ms.
- Contador y configuración guardados en la memoria NVS de la ESP32.
- Panel local en el PC con total, estado, próximo aviso, historial, sonido y notificación de escritorio opcional.
- Transmisión USB serie a 115200 baudios; el mismo cable alimenta la placa.
- Lectura Bluetooth Low Energy en iPhone mediante phyphox.
- Visor móvil adicional con tono de mantenimiento y botón para probar sonido.
- Intervalo ajustable desde el PC, reconocimiento de avisos y reinicio del total con el interruptor en OFF.
- Operación principal sin Internet después de instalar las herramientas.

## Hardware y conexiones

Placa usada: **ESP32-S3**, con conector USB marcado **COM**. Utilizar un cable USB de datos.

| Desde | Hacia |
|---|---|
| GPIO4, impreso como 4/IO4 en la placa | Un contacto del interruptor |
| GND/G de la placa | El otro contacto del interruptor |
| USB COM de la placa | Puerto USB del PC |

El interruptor debe unir esos contactos en ON y abrirlos en OFF. Si tiene más terminales, identificar el par con continuidad antes de conectarlo. Los colores de los cables no determinan su función. No conectar 5 V, 12 V ni una fuente externa al GPIO o al interruptor. El regulador externo, las dos resistencias y el capacitor no son necesarios para este montaje USB.

Véase [montaje y materiales](docs/MONTAJE.md).

## Inicio rápido en Windows

1. Descargar o clonar este repositorio y extraerlo completamente.
2. Instalar Arduino IDE y el paquete **esp32 by Espressif Systems**.
3. Abrir [firmware/horometro_ble/horometro_ble.ino](firmware/horometro_ble/horometro_ble.ino). Mantener `visor_ble.h` en la misma carpeta.
4. Seleccionar **ESP32S3 Dev Module**, el puerto de la placa y **USB CDC On Boot = Disabled** para el conector COM de esta placa. Cerrar el panel Python y el monitor serie antes de subir.
5. Cargar con el botón de flecha **Subir**. El firmware BLE también sirve para el panel USB; no hace falta cargar otro programa.
6. Instalar Python 3.10 o superior. En PowerShell, dentro de `pc`:

```powershell
python -m pip install -r requirements.txt
python horometro_pc.py --ports
python horometro_pc.py --port COM3
```

Sustituir COM3 por el puerto real. Abrir http://127.0.0.1:8000 y pulsar **Activar sonido y notificaciones**. Después puede usar `pc/Abrir_Horometro.bat`; el lanzador usa COM3 por defecto y abre el navegador. Mantener la ventana de Python abierta.

## Celular por Bluetooth

1. Instalar **phyphox** en el iPhone y permitir Bluetooth.
2. Enviar al teléfono [movil/Horometro.phyphox](movil/Horometro.phyphox) o [movil/Horometro_con_alarma.phyphox](movil/Horometro_con_alarma.phyphox). Desde Archivos: **Compartir → phyphox**.
3. Abrir el experimento, elegir **Horometro-UAI** y pulsar ▶.
4. Mantener la placa alimentada por USB. El PC no es necesario para la lectura BLE si se alimenta mediante batería externa.
5. Para el visor con alarma, mantener la app visible y comprobar el botón **Probar sonido**.

**El archivo básico solo muestra el aviso; no suena. El archivo con alarma añade un tono dentro de phyphox: no genera una notificación de iOS en la pantalla bloqueada.** El complemento opcional de [avisos por Windows](opcionales/avisos_iphone_windows/LEAME.txt) requiere Home Assistant y Wi-Fi local, y todavía necesita prueba física de entrega en el iPhone.

## Prueba de exposición

Con intervalo de 10 h, partir del total visible (puede conservar horas de pruebas anteriores):

1. ON unos 5 segundos: el total aumenta aproximadamente 5 h.
2. OFF unos 3 segundos: el total permanece fijo.
3. ON hasta alcanzar el siguiente múltiplo de 10 h: el PC registra el aviso; el celular muestra revisión pendiente.
4. Continuar hasta el siguiente umbral: debe generarse un nuevo aviso.
5. OFF, esperar la confirmación de pausa, desconectar y volver a conectar: verificar recuperación del acumulado.

[Plan y estado de validación](docs/PRUEBAS.md).

## Persistencia y límites

Se guarda al pasar a OFF, al cruzar un umbral, tras cambios de configuración y aproximadamente cada 5 s mientras cuenta. Un corte brusco puede perder unos 5 segundos reales (5 h de la simulación), si NVS funciona. No se mide sin alimentación. `storage_ok` informa el resultado de guardado.

Cambiar la escala en el código genera una sesión nueva si el registro no es compatible. La escala de demostración no sirve directamente para una medición industrial real. El contacto emula la señal de encendido; no comprueba giro ni carga de un motor.

## Contenido

| Carpeta | Contenido |
|---|---|
| `firmware/horometro_ble` | Programa ESP32 con interruptor, USB y BLE |
| `pc` | Puente Python, panel HTML y lanzador Windows |
| `movil` | Visores phyphox básico y con alarma |
| `cad` | Caja paramétrica OpenSCAD y STL de referencia |
| `docs` | Montaje, funcionamiento, pruebas y resolución de errores |
| `opcionales` | Avisos al iPhone mediante Windows y Home Assistant |

La caja CAD es un diseño preliminar de **200 × 120 × 55 mm**: medir el conjunto antes de imprimir. [Detalles](cad/README.md).

## Fuentes y autoría

[Fuentes, dependencias y uso de asistencia de IA](FUENTES.md). La publicación del código no modifica las licencias de sus dependencias.
