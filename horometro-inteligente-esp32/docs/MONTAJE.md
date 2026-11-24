# Montaje

## Componentes

| Componente | Uso |
|---|---|
| ESP32-S3 con pines soldados | Contador, NVS y comunicación |
| Interruptor con contactos secos | Simulación de chapa ON/OFF |
| Dos conexiones al interruptor | Une GPIO4 con GND al cerrar |
| Cable USB de datos | Energía y transmisión al PC |
| Protoboard y Dupont, si son necesarios | Soporte y conexiones sin soldar |
| Regulador externo, resistencias y capacitor disponibles | Fuera de este montaje USB |

Desconectar el USB antes de modificar cables. Usar el nombre impreso del pin, no contar posiciones desde una foto.

1. Con multímetro en continuidad y el switch desconectado de la placa, comprobar qué dos contactos cierran en ON y abren en OFF. Si tiene tres o más patas no asumir que todas sirven igual.
2. Conectar un contacto a GPIO4.
3. Conectar el otro a GND.
4. Verificar que no hay puentes entre alimentación y GND.
5. Conectar el USB al conector COM y cargar el firmware.
6. Confirmar ON/OFF en el panel antes de cerrar la caja.

En una protoboard habitual, cada grupo de cinco agujeros a un lado del canal central está conectado internamente. Los grupos de ambos lados quedan separados. Los rieles laterales pueden estar cortados en el centro: comprobar continuidad, no fiarse solo de la línea impresa. No poner ambos contactos del switch sobre un mismo grupo conectado.
