# Progreso y decisiones

## Entorno
- VS Code
- Extensión GitHub Copilot   
- Python: salida de `python --version`: 3.14
- Plan: Copilot Free

## Registro         
(el agente agrega entradas acá; yo agrego las decisiones de revisión)

### 2026-11-10 — Núcleo de reglas de reservas en memoria
- **Tarea:** se agregó `src/reservas/` con reservas en memoria, validación compartida por `reservar` y `consultar_disponibilidad`, y pruebas `unittest` para creación, solapamiento, límites consecutivos, unidades distintas y entradas inválidas.
- **Decisiones:** el inventario permitido es el listado inicial del README; la disponibilidad devuelve `False` ante una superposición y lanza `ValueError` ante entradas inválidas. Se aplican fechas futuras, duración máxima de 8 horas y anticipación máxima de 90 días, solicitados para esta tarea aunque el README los enumera como supuestos por confirmar. Fechas locales sin zona y formato estricto `YYYY-MM-DDTHH:MM`.
- **Prueba primero:** previo a implementar, `py -m unittest discover -s tests -v` falló con `ModuleNotFoundError: No module named 'reservas'`.
- **Comando y resultado final:** `python -m unittest discover -s tests -v` — **OK**, 7 pruebas ejecutadas. El entorno no resuelve `python` directamente, por lo que el comando se ejecutó tras anteponer temporalmente al `PATH` la ubicación del intérprete Python 3.14 disponible mediante `py`.

### 2026-11-10 — Ajustes de API, IDs y reloj
- **Tarea:** se quitó el solicitante de `consultar_disponibilidad`, se agregó un ID incremental y `buscar_por_id`, y se inyectó `reloj` en `GestorReservas` con `datetime.now` como valor predeterminado. Las pruebas ahora usan un reloj fijo.
- **Decisiones:** la reserva conserva `dataclass(frozen=True)`; la búsqueda por un ID inexistente lanza `KeyError`. El solicitante se valida al reservar, mientras que las reglas comunes continúan centralizadas en `_validar_reserva`.
- **Prueba primero:** antes de cambiar la implementación, `python -m unittest discover -s tests -v` ejecutó 8 pruebas y falló con 8 errores: `GestorReservas.__init__()` no aceptaba `reloj`.
- **Comando y resultado final:** `python -m unittest discover -s tests -v` — **OK**, 8 pruebas ejecutadas. Se antepuso temporalmente al `PATH` el intérprete Python 3.14 disponible mediante `py`, porque `python` no está disponible directamente en el entorno.
- **Validación adicional:** `git diff --check` sin errores; diagnóstico Pylance de `domain.py` sin diagnósticos. La comprobación de compatibilidad de firma de Pylance no encontró call sites resolubles.

- **Verificado por mí (Windows, Python 3.14.6 según `py --version`):**
  `py -m unittest discover -s tests -v` → 8 pruebas OK en mi terminal.
- **Solo informado por el agente (no verificado por mí):** `git diff --check`
  y diagnósticos de Pylance.
- **Aprobaciones de comandos que di:** pruebas con `Allow Once`; diagnóstico de
  lectura de Python (`Get-Command`, variables de entorno) con `Allow Once`;
  `py -m unittest ...` con `Allow Once`. No usé "permitir siempre".
- **Decisión humana:** CORREGIR. Al revisar el diff pedí tres cambios:
  (a) la consulta de disponibilidad no debe exigir solicitante, porque el enunciado
  habla de consultar por unidad e intervalo; (b) la reserva necesita ID, porque
  debe ser identificable y la cancelación conserva el identificador; (c) reloj
  inyectable, para que las pruebas no dependan de la fecha del día.
  Tras la corrección acepté el resultado.
- **Evidencia:** commit `<hash>`.

### 2026-11-11 — Persistencia SQLite e inventario externo
- **Tarea:** se agregó persistencia de reservas y estados en `data/reservas.db`,
  carga del inventario desde `data/inventario.json`, reinicio de reservas sin
  borrar el inventario, y pruebas temporales para persistencia, IDs, carga de
  inventario y fallos de validación.
- **Decisiones:** el JSON asocia cada ID de unidad con su nombre de equipo;
  SQLite usa `INTEGER PRIMARY KEY AUTOINCREMENT` para no reutilizar IDs, incluso
  luego de reiniciar datos. La fecha de cancelación es nullable y se carga junto
  con el estado. La prueba marca una reserva como cancelada directamente en
  SQLite, sin agregar aún la cancelación de usuario.
- **Prueba primero:** antes de implementar, `py -m unittest discover -s tests -v`
  ejecutó 12 pruebas y falló con 12 errores porque `GestorReservas` todavía no
  aceptaba `db_path`.
- **Comando y resultado final:** `py -m unittest discover -s tests -v` —
  **OK**, 12 pruebas ejecutadas.
- **Validación adicional:** `git diff --check` señaló espacios finales en líneas
  preexistentes y modificadas localmente de esta bitácora; no se alteraron esos
  cambios del usuario. La prueba modificó temporalmente los `.pyc` versionados;
  fueron restaurados y no quedan modificados. Sin commit.

### 2026-11-12 — Cancelación y CLI
- **Tarea:** se agregó cancelación persistente por ID, con fecha de cancelación,
  conservación del registro y liberación del intervalo; se agregó la CLI con
  disponibilidad, reserva, cancelación, listado y reinicio confirmado. Se
  documentó su uso en README y se añadieron pruebas de dominio y CLI.
- **Decisiones:** la cancelación actualiza SQLite dentro de una transacción y
  luego actualiza el estado en memoria; IDs inexistentes producen `KeyError` y
  las dobles cancelaciones `ValueError`. La CLI acepta `--db` antes del
  subcomando o `RESERVAS_DB`; `reiniciar-datos` exige escribir `SI` exactamente
  y no borra con confirmación negativa o entrada finalizada. El comando
  documentado para el diseño `src/` es `py -m src.reservas`.
- **Prueba primero:** antes de implementar, `py -m unittest discover -s tests -v`
  ejecutó 18 pruebas y falló con 6 errores: no existían `GestorReservas.cancelar`
  ni `reservas.cli`.
- **Comando y resultado final:** `py -m unittest discover -s tests -v` —
  **OK**, 20 pruebas ejecutadas con Python 3.15.2.
- **Validación adicional:** `py -m src.reservas --help` — **OK**;
  `git diff --check` — **OK**; diagnósticos Pylance de sintaxis en los archivos
  Python modificados — **sin errores**. Sin commit.