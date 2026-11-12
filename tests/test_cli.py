import contextlib
from datetime import datetime, timedelta
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reservas.cli import main


class CliReservasTests(unittest.TestCase):
    def test_error_de_validacion_devuelve_codigo_no_cero_y_mensaje(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = Path(directorio) / "reservas.db"
            ahora = (
                datetime.now().replace(second=0, microsecond=0)
                + timedelta(days=1)
            )
            inicio = ahora.strftime("%Y-%m-%dT%H:%M")
            fin = (ahora + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
            error = io.StringIO()

            with contextlib.redirect_stderr(error):
                codigo = main(
                    ["--db", str(ruta_db), "disponibilidad", "NO-EXISTE", inicio, fin]
                )

            self.assertNotEqual(codigo, 0)
            self.assertIn("Unidad desconocida", error.getvalue())

    def test_subcomandos_usan_la_base_de_datos_indicada(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = Path(directorio) / "reservas.db"
            inicio_dt = (
                datetime.now().replace(second=0, microsecond=0)
                + timedelta(days=1)
            )
            fin_dt = inicio_dt + timedelta(hours=1)
            inicio = inicio_dt.strftime("%Y-%m-%dT%H:%M")
            fin = fin_dt.strftime("%Y-%m-%dT%H:%M")

            def ejecutar(*args, entrada=None):
                salida = io.StringIO()
                with contextlib.redirect_stdout(salida):
                    with contextlib.redirect_stderr(io.StringIO()):
                        resultado = main(
                            ["--db", str(ruta_db), *args],
                            input_fn=lambda _: entrada,
                        )
                return resultado, salida.getvalue()

            codigo, salida = ejecutar("disponibilidad", "MIC-01", inicio, fin)
            self.assertEqual(codigo, 0)
            self.assertIn("disponible", salida.lower())

            codigo, salida = ejecutar(
                "reservar", "MIC-01", "Solicitante ficticio", inicio, fin
            )
            self.assertEqual(codigo, 0)
            self.assertIn("Reserva creada", salida)

            codigo, salida = ejecutar("listar")
            self.assertEqual(codigo, 0)
            self.assertIn("activa", salida)
            self.assertIn("Solicitante ficticio", salida)

            codigo, _ = ejecutar("cancelar", "1")
            self.assertEqual(codigo, 0)

            codigo, salida = ejecutar("listar")
            self.assertEqual(codigo, 0)
            self.assertIn("cancelada", salida)

            codigo, salida = ejecutar("disponibilidad", "MIC-01", inicio, fin)
            self.assertEqual(codigo, 0)
            self.assertIn("disponible", salida.lower())

            codigo, salida = ejecutar("reiniciar-datos", entrada="NO")
            self.assertNotEqual(codigo, 0)
            self.assertIn("no se modificaron", salida.lower())
            codigo, salida = ejecutar("listar")
            self.assertEqual(codigo, 0)
            self.assertIn("cancelada", salida)

            codigo, salida = ejecutar("reiniciar-datos", entrada="SI")
            self.assertEqual(codigo, 0)
            self.assertIn("reiniciados", salida.lower())
            codigo, salida = ejecutar("listar")
            self.assertEqual(codigo, 0)
            self.assertIn("No hay reservas", salida)

    def test_reiniciar_datos_sin_entrada_informa_el_error(self):
        error = io.StringIO()

        def fin_de_entrada(_):
            raise EOFError

        with tempfile.TemporaryDirectory() as directorio:
            with contextlib.redirect_stderr(error):
                codigo = main(
                    [
                        "--db",
                        str(Path(directorio) / "reservas.db"),
                        "reiniciar-datos",
                    ],
                    input_fn=fin_de_entrada,
                )

        self.assertNotEqual(codigo, 0)
        self.assertIn("no se recibió confirmación", error.getvalue())


if __name__ == "__main__":
    unittest.main()
