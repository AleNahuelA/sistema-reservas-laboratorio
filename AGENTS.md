# Instrucciones para el agente

Proyecto: sistema de reservas de un laboratorio. La especificación está en
README.md (sección 1) y es la fuente de verdad. No cambies reglas sin que yo lo pida.

## Stack
- Python 3.11+, solo biblioteca estándar (sqlite3, argparse, datetime, unittest).
- No agregues dependencias.
- Datos en data/reservas.db; inventario en data/inventario.json.

## Reglas de diseño
- Intervalos semiabiertos [inicio, fin).
- Una única función de validación, usada tanto por reservar como por disponibilidad.
- Cancelar nunca borra: cambia el estado a "cancelada".
- Solicitantes siempre ficticios.

## Procedimiento obligatorio (adaptación específica)
1. TESTS PRIMERO: antes de implementar una regla, escribí la prueba que la verifica
   y mostrame que falla. Después implementá hasta que pase.
2. REGISTRO: al terminar cada tarea, agregá una entrada a PROGRESS.md con fecha,
   tarea, decisiones tomadas, comando de prueba ejecutado y su resultado real.
3. No marques algo como verificado si no corriste el comando. Si no pudiste
   ejecutarlo, escribí "no ejecutado" y el motivo.

## Límites y permisos
- Trabajá solo dentro de esta carpeta.
- No uses comandos destructivos (rm -rf, git reset --hard, git push --force).
- No hagas git commit ni git push: los hago yo después de revisar el diff.
- No leas ni escribas secretos, tokens ni archivos fuera del repo.
- Ante una ambigüedad de la especificación, preguntame en vez de asumir.