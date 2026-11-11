import unittest
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reservas.domain import GestorReservas


class GestorReservasTests(unittest.TestCase):
    def setUp(self):
        self.ahora = datetime(2035, 5, 20, 12, 0)
        self.gestor = GestorReservas(reloj=lambda: self.ahora)

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


if __name__ == "__main__":
    unittest.main()
