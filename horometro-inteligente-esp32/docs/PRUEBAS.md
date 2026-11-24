# Pruebas y estado real

Este archivo distingue observaciones físicas, comprobaciones de software y trabajo pendiente. No equivale a una certificación del equipo.

## Evidencia disponible al preparar el repositorio

| Comprobación | Estado |
|---|---|
| Compilación y carga de horometro_ble en ESP32-S3 | Confirmadas por registro aportado por el usuario |
| Conexión y lectura en vivo en phyphox | Usuario indicó «funciona» |
| Sonido/notificación del visor básico | No implementados en ese archivo; usuario reportó ausencia |
| Visor adicional con alarma | Lógica comprobada con datos simulados; sonido físico pendiente de confirmar |
| Notificación iOS desde Windows/Home Assistant | Complemento preparado; instalación y entrega física pendientes |
| Caja CAD | Modelo preliminar; dimensiones y ajuste físico pendientes |

Registro de carga aportado: 573272 bytes de programa (43 %), 27920 bytes de RAM estática (8 %), ESP32-S3, verificación de hash correcta y reinicio final. Esto prueba la carga de ese sketch, no todas sus funciones en hardware.

## Guion repetible

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Anotar total inicial e intervalo | Referencia visible |
| 2 | ON durante 5 s reales | Incremento aproximado de 5 h simuladas |
| 3 | OFF durante 3 s | Total fijo |
| 4 | Volver a ON | Reanuda desde el total previo |
| 5 | Alcanzar próximo umbral | Nuevo evento e indicación de mantenimiento |
| 6 | Seguir hasta otro umbral | Un nuevo aviso para ese vencimiento |
| 7 | Reconocer desde el PC | Desaparece pendiente; no cambia el total |
| 8 | OFF y cambiar intervalo | La ESP32 confirma el nuevo programa |
| 9 | OFF, esperar y reconectar USB | Conserva el total guardado |
| 10 | Probar sonido con el visor activo | Tono audible en el teléfono |
| 11 | Probar complemento con pantalla bloqueada | Notificación recibida; registrar requisitos de red |

Anotar fecha, total inicial/final, duración, observación y si pasó o falló. Medir error de conteo respecto de un cronómetro si se quiere cuantificar precisión. Evitar presentar valores medidos inexistentes.
