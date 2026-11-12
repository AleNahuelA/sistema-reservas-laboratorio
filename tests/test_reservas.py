from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reservas.domain import GestorReservas


class GestorReservasTests(unittest.TestCase):
    def setUp(self):
        self.ahora = datetime(2035, 5, 20, 12, 0)
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.gestor = GestorReservas(
            reloj=lambda: self.ahora,
            db_path=Path(self.directorio_temporal.name) / "reservas.db",
        )

    def tearDown(self):
        self.directorio_temporal.cleanup()

    def intervalo_futuro(self, dias=1, duracion_horas=1):
        inicio = self.ahora + timedelta(days=dias)
        fin = inicio + timedelta(hours=duracion_horas)
        return inicio.strftime("%Y-%m-%dT%H:%M"), fin.strftime("%Y-%m-%dT%H:%M")

    def test_crea_reserva_valida(self):
        inicio, fin = self.intervalo_futuro()

        reserva = self.gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

        self.assertEqual(reserva.unidad, "MIC-01")
        self.assertEqual(reserva.solicitante, "Solicitante ficticio")
        self.assertEqual(len(self.gestor.reservas), 1)
        self.assertEqual(self.gestor.buscar_por_id(reserva.id), reserva)

    def test_identificadores_unicos_y_busqueda_de_reserva(self):
        primero_inicio, primero_fin = self.intervalo_futuro()
        segundo_inicio, segundo_fin = self.intervalo_futuro(dias=2)
        primero = self.gestor.reservar(
            "MIC-01", "Solicitante ficticio", primero_inicio, primero_fin
        )
        segundo = self.gestor.reservar(
            "MIC-01", "Otro solicitante ficticio", segundo_inicio, segundo_fin
        )

        self.assertNotEqual(primero.id, segundo.id)
        self.assertEqual(self.gestor.buscar_por_id(primero.id), primero)
        with self.assertRaises(KeyError):
            self.gestor.buscar_por_id(999)

    def test_rechaza_superposicion_de_misma_unidad(self):
        inicio, fin = self.intervalo_futuro()
        inicio_2 = (datetime.strptime(inicio, "%Y-%m-%dT%H:%M") + timedelta(minutes=30))
        fin_2 = (datetime.strptime(fin, "%Y-%m-%dT%H:%M") + timedelta(minutes=30))
        self.gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

        with self.assertRaisesRegex(ValueError, "superpone"):
            self.gestor.reservar(
                "MIC-01",
                "Otro solicitante ficticio",
                inicio_2.strftime("%Y-%m-%dT%H:%M"),
                fin_2.strftime("%Y-%m-%dT%H:%M"),
            )

    def test_permite_limites_consecutivos(self):
        inicio, fin = self.intervalo_futuro()
        siguiente_fin = (
            datetime.strptime(fin, "%Y-%m-%dT%H:%M") + timedelta(hours=1)
        ).strftime("%Y-%m-%dT%H:%M")
        self.gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

        reserva = self.gestor.reservar(
            "MIC-01", "Otro solicitante ficticio", fin, siguiente_fin
        )

        self.assertEqual(len(self.gestor.reservas), 2)
        self.assertEqual(reserva.inicio.strftime("%Y-%m-%dT%H:%M"), fin)

    def test_permite_unidades_distintas_en_simultaneo(self):
        inicio, fin = self.intervalo_futuro()
        self.gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

        reserva = self.gestor.reservar(
            "MIC-02", "Otro solicitante ficticio", inicio, fin
        )

        self.assertEqual(reserva.unidad, "MIC-02")

    def test_rechaza_entradas_invalidas(self):
        inicio, fin = self.intervalo_futuro()
        casos = (
            ("unidad desconocida", "NO-EXISTE", "Solicitante ficticio", inicio, fin),
            ("solicitante vacío", "MIC-01", "   ", inicio, fin),
            ("fecha mal formada", "MIC-01", "Solicitante ficticio", "mañana", fin),
            ("inicio igual a fin", "MIC-01", "Solicitante ficticio", inicio, inicio),
            (
                "inicio posterior a fin",
                "MIC-01",
                "Solicitante ficticio",
                fin,
                inicio,
            ),
        )
        for descripcion, unidad, solicitante, desde, hasta in casos:
            with self.subTest(descripcion=descripcion):
                with self.assertRaises(ValueError):
                    self.gestor.reservar(unidad, solicitante, desde, hasta)

    def test_rechaza_fecha_pasada_duracion_y_anticipacion_excesivas(self):
        pasado_inicio = (self.ahora - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        pasado_fin = (self.ahora - timedelta(days=1) + timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        larga_inicio, larga_fin = self.intervalo_futuro(duracion_horas=9)
        lejana_inicio, lejana_fin = self.intervalo_futuro(dias=91)
        casos = (
            (pasado_inicio, pasado_fin),
            (larga_inicio, larga_fin),
            (lejana_inicio, lejana_fin),
        )

        for desde, hasta in casos:
            with self.subTest(desde=desde, hasta=hasta):
                with self.assertRaises(ValueError):
                    self.gestor.reservar(
                        "MIC-01", "Solicitante ficticio", desde, hasta
                    )

    def test_disponibilidad_comparte_validacion_y_detecta_ocupacion(self):
        inicio, fin = self.intervalo_futuro()
        self.gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

        self.assertFalse(
            self.gestor.consultar_disponibilidad(
                "MIC-01", inicio, fin
            )
        )
        with self.assertRaises(ValueError):
            self.gestor.consultar_disponibilidad("NO-EXISTE", inicio, fin)

    def test_inventario_se_carga_desde_archivo(self):
        inicio, fin = self.intervalo_futuro()
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = Path(directorio) / "reservas.db"
            ruta_inventario = Path(directorio) / "inventario.json"
            ruta_inventario.write_text(
                json.dumps({"EQ-01": "Equipo de prueba"}),
                encoding="utf-8",
            )
            gestor = GestorReservas(
                reloj=lambda: self.ahora,
                db_path=ruta_db,
                inventory_path=ruta_inventario,
            )

            reserva = gestor.reservar("EQ-01", "Solicitante ficticio", inicio, fin)

            self.assertEqual(reserva.unidad, "EQ-01")
            with self.assertRaisesRegex(ValueError, "Unidad desconocida"):
                gestor.reservar("MIC-01", "Solicitante ficticio", inicio, fin)

    def test_reservas_activas_y_canceladas_se_recuperan_al_reiniciar(self):
        inicio_activa, fin_activa = self.intervalo_futuro()
        inicio_cancelada, fin_cancelada = self.intervalo_futuro(dias=2)
        fecha_cancelacion = "2035-05-20T12:30:00"
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = Path(directorio) / "reservas.db"
            gestor = GestorReservas(reloj=lambda: self.ahora, db_path=ruta_db)
            activa = gestor.reservar(
                "MIC-01", "Solicitante ficticio", inicio_activa, fin_activa
            )
            cancelada = gestor.reservar(
                "MIC-02", "Otro solicitante ficticio", inicio_cancelada, fin_cancelada
            )
            with closing(sqlite3.connect(ruta_db)) as conexion:
                with conexion:
                    conexion.execute(
                        "UPDATE reservas SET estado = ?, fecha_cancelacion = ? WHERE id = ?",
                        ("cancelada", fecha_cancelacion, cancelada.id),
                    )

            gestor_reiniciado = GestorReservas(
                reloj=lambda: self.ahora, db_path=ruta_db
            )

            self.assertEqual(gestor_reiniciado.buscar_por_id(activa.id), activa)
            self.assertFalse(
                gestor_reiniciado.consultar_disponibilidad(
                    "MIC-01", inicio_activa, fin_activa
                )
            )
            reserva_cancelada = gestor_reiniciado.buscar_por_id(cancelada.id)
            self.assertEqual(reserva_cancelada.estado, "cancelada")
            self.assertEqual(
                reserva_cancelada.fecha_cancelacion,
                datetime.fromisoformat(fecha_cancelacion),
            )
            self.assertTrue(
                gestor_reiniciado.consultar_disponibilidad(
                    "MIC-02", inicio_cancelada, fin_cancelada
                )
            )
            siguiente_inicio, siguiente_fin = self.intervalo_futuro(dias=3)
            siguiente = gestor_reiniciado.reservar(
                "MIC-01", "Tercer solicitante ficticio", siguiente_inicio, siguiente_fin
            )
            self.assertGreater(siguiente.id, cancelada.id)

    def test_validacion_fallida_no_persiste_reserva(self):
        inicio, fin = self.intervalo_futuro()
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = Path(directorio) / "reservas.db"
            gestor = GestorReservas(reloj=lambda: self.ahora, db_path=ruta_db)

            with self.assertRaisesRegex(ValueError, "Unidad desconocida"):
                gestor.reservar("NO-EXISTE", "Solicitante ficticio", inicio, fin)

            with closing(sqlite3.connect(ruta_db)) as conexion:
                cantidad = conexion.execute(
                    "SELECT COUNT(*) FROM reservas"
                ).fetchone()[0]
            self.assertEqual(cantidad, 0)

    def test_reiniciar_datos_borra_reservas_y_conserva_inventario(self):
        inicio, fin = self.intervalo_futuro()
        reserva = self.gestor.reservar(
            "MIC-01", "Solicitante ficticio", inicio, fin
        )

        self.gestor.reiniciar_datos()

        self.assertEqual(self.gestor.reservas, ())
        nueva = self.gestor.reservar(
            "MIC-02", "Otro solicitante ficticio", inicio, fin
        )
        self.assertGreater(nueva.id, reserva.id)


if __name__ == "__main__":
    unittest.main()
