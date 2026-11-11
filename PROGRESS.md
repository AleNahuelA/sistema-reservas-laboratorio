# Progreso y decisiones

## Entorno
- VS Code: versión ___
- Extensión GitHub Copilot: versión ___ (modo Agent)
- Modelo: ___ (si no se muestra, escribir "no visible")
- Python: salida de `python --version`: ___
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