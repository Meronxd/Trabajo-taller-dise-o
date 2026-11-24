# Funcionamiento y protocolo

La ESP32 mide intervalos de tiempo con esp_timer_get_time(). El bucle cuenta solo mientras la lectura estabilizada de GPIO4 está a LOW. La resistencia pull-up interna mantiene HIGH cuando el interruptor queda abierto. El antirrebote exige 40 ms estables.

La hora simulada corresponde a 1 000 000 µs reales en ON. El índice de mantenimiento es la división entera del tiempo acumulado por el intervalo programado. La placa transmite ese índice y el estado pendiente; los visores no calculan tiempo de uso a partir de sus relojes.

## USB

JSON por líneas a 115200 baudios. Un informe cada 250 ms aproximadamente, además de cambios de estado y umbrales. Campos principales: total_us, us_per_hour, interval_hours, alert_index, ack_index, maintenance_due, next_due_us, generation, schedule y storage_ok.

El PC valida el informe, conserva hasta 100 avisos y evita duplicados mediante dispositivo, generación, escala, programa e índice de aviso. Al reconectar puede resumir varios umbrales en un único aviso.

Los comandos tienen formato `<id_entero> <comando>
`:

| Comando | Efecto |
|---|---|
| STATUS | Solicitar informe |
| RESET | Reiniciar contador; exige OFF |
| INTERVAL 10 | Configurar horas enteras entre 1 y 1 000 000; exige OFF y avisos previos reconocidos |
| ACK 1 | Reconocer el índice indicado; no borra el total |

Usar preferentemente el panel, que gestiona identificadores y confirmaciones.

## BLE

Nombre anunciado: Horometro-UAI. Un visor conectado a la vez.

Servicio: b7215800-26f4-49cf-942d-7a1c6f440901  
Característica READ/NOTIFY: b7215801-26f4-49cf-942d-7a1c6f440901

| Bytes | Tipo | Significado |
|---|---|---|
| 0–7 | float64 little endian | Horas acumuladas |
| 8–15 | float64 little endian | Próximo umbral en horas |
| 16 | uint8 | ON=1, OFF=0 |
| 17 | uint8 | Revisión pendiente=1 |

El visor básico es de lectura. Intervalo, reinicio y reconocimiento se gestionan desde el PC. La última cifra visible tras perder BLE puede estar desactualizada; no implica que siga llegando información.

## Avisos móviles

El visor con alarma observa el avance del próximo umbral que comunica la placa, el total recibido y la bandera de revisión pendiente. Reproduce un tono al detectar un nuevo vencimiento mientras el experimento está activo. El botón Probar sonido comprueba el altavoz y no cambia el contador. No sustituye una notificación del sistema ni garantiza alarmas en segundo plano. Al abrir el visor con avisos ya pendientes debe consultarse el texto; no se reproduce un historial de alarmas.

El complemento Windows/Home Assistant lee los nuevos eventos del panel, los deduplica y los envía a una automatización local. Su respuesta HTTP no prueba la entrega en el teléfono.
