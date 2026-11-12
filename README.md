# sistema reservas laboratorio
## 1. Especificación breve

**Problema.** La coordinación de un laboratorio gestiona pedidos por mensajes y
planilla; se confirman unidades para horarios superpuestos y las cancelaciones
siguen bloqueando el horario.

**Alcance.** Consultar disponibilidad por unidad e intervalo, reservar, cancelar
conservando el historial, y persistir todo entre reinicios. Una unidad por reserva.
Fuera de alcance: autenticación, notificaciones, pagos, integraciones, GUI,
administración del inventario.

**Inventario inicial** (`data/inventario.json`): MIC-01, MIC-02 (microscopio digital),
OSC-01 (osciloscopio), MUL-01 (multímetro), FUE-01 (fuente de alimentación).

**Reglas**
- R1. Una reserva activa ocupa el intervalo [inicio, fin); una cancelada no.
- R2. Unidad debe existir en el inventario.
- R3. Solicitante no vacío ni solo espacios.
- R4. Fechas válidas en formato ISO 8601 (YYYY-MM-DDTHH:MM), sin zona; hora local
      de America/Argentina/Buenos_Aires.
- R5. inicio < fin (estricto).
- R6. Se rechaza superposición con reservas activas de la misma unidad.
- R7. Se permiten límites consecutivos y reservas simultáneas de unidades distintas.
- R8. La disponibilidad aplica exactamente las mismas validaciones que reservar.
- R9. Cancelar cambia el estado a `cancelada`, conserva ID y datos, libera el intervalo.
- R10. Las reservas y sus estados persisten tras reiniciar.

**Supuestos** (a confirmar): fechas pasadas rechazadas; duración máxima 8 h;
anticipación máxima 90 días; cancelar una reserva ya cancelada da error.

**Criterios de aceptación**
- CA1. Con MIC-01 reservado 10:00–11:00: 10:30–11:30 se rechaza, 11:00–12:00 se acepta.
- CA2. MIC-02 puede reservarse 10:00–11:00 aunque MIC-01 esté ocupado.
- CA3. Tras cancelar, el intervalo figura disponible y la reserva sigue listada como cancelada.
- CA4. Tras detener y reiniciar la app, las reservas activas y canceladas siguen ahí.
- CA5. Entradas inválidas (unidad desconocida, solicitante vacío, fecha mal formada,
       inicio >= fin) se rechazan con mensaje claro.

## 2. Interfaz de consola

Desde la raíz del repositorio, ejecutar con Python 3:

```powershell
py -m src.reservas --help
py -m src.reservas disponibilidad MIC-01 "<inicio>" "<fin>"
py -m src.reservas reservar MIC-01 "Solicitante ficticio" "<inicio>" "<fin>"
py -m src.reservas cancelar 1
py -m src.reservas listar
py -m src.reservas reiniciar-datos
```

Reemplazá `<inicio>` y `<fin>` por fechas futuras válidas en formato
`YYYY-MM-DDTHH:MM` (máximo 90 días de anticipación y hasta 8 horas de duración).
La base predeterminada es
`data/reservas.db`; se puede cambiar con `--db <ruta>` antes del subcomando o
con la variable de entorno `RESERVAS_DB`. `reiniciar-datos` solicita escribir
`SI` antes de borrar las reservas.
