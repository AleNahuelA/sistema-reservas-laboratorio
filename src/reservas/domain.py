from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable


UNIDADES_INICIALES = frozenset(
    {"MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"}
)
FORMATO_FECHA = "%Y-%m-%dT%H:%M"


@dataclass(frozen=True)
class Reserva:
    id: int
    unidad: str
    solicitante: str
    inicio: datetime
    fin: datetime
    estado: str = "activa"


class _ReservaSuperpuestaError(ValueError):
    pass


class GestorReservas:
    def __init__(self, reloj: Callable[[], datetime] = datetime.now):
        self._reservas = []
        self._reloj = reloj
        self._siguiente_id = 1

    @property
    def reservas(self):
        return tuple(self._reservas)

    def reservar(self, unidad, solicitante, inicio, fin):
        if not isinstance(solicitante, str) or not solicitante.strip():
            raise ValueError("El solicitante no puede estar vacío.")
        inicio_dt, fin_dt = self._validar_reserva(unidad, inicio, fin)
        reserva = Reserva(
            self._siguiente_id, unidad, solicitante, inicio_dt, fin_dt
        )
        self._reservas.append(reserva)
        self._siguiente_id += 1
        return reserva

    def buscar_por_id(self, id_reserva):
        for reserva in self._reservas:
            if reserva.id == id_reserva:
                return reserva
        raise KeyError(f"No existe una reserva con id {id_reserva}.")

    def consultar_disponibilidad(self, unidad, inicio, fin):
        try:
            self._validar_reserva(unidad, inicio, fin)
        except _ReservaSuperpuestaError:
            return False
        return True

    def _validar_reserva(self, unidad, inicio, fin):
        if not isinstance(unidad, str) or unidad not in UNIDADES_INICIALES:
            raise ValueError(f"Unidad desconocida: {unidad!r}.")

        if not isinstance(inicio, str) or not isinstance(fin, str):
            raise ValueError("Las fechas deben tener formato ISO 8601 YYYY-MM-DDTHH:MM.")
        try:
            inicio_dt = datetime.strptime(inicio, FORMATO_FECHA)
            fin_dt = datetime.strptime(fin, FORMATO_FECHA)
        except ValueError as error:
            raise ValueError(
                "Las fechas deben tener formato ISO 8601 YYYY-MM-DDTHH:MM."
            ) from error
        if (
            inicio_dt.strftime(FORMATO_FECHA) != inicio
            or fin_dt.strftime(FORMATO_FECHA) != fin
        ):
            raise ValueError("Las fechas deben tener formato ISO 8601 YYYY-MM-DDTHH:MM.")
        if inicio_dt >= fin_dt:
            raise ValueError("El inicio debe ser anterior al fin.")

        ahora = self._reloj()
        if inicio_dt < ahora:
            raise ValueError("El inicio de la reserva no puede estar en el pasado.")
        if fin_dt - inicio_dt > timedelta(hours=8):
            raise ValueError("La duración máxima de una reserva es de 8 horas.")
        if inicio_dt > ahora + timedelta(days=90):
            raise ValueError(
                "La reserva no puede comenzar con más de 90 días de anticipación."
            )

        for reserva in self._reservas:
            if (
                reserva.estado == "activa"
                and reserva.unidad == unidad
                and inicio_dt < reserva.fin
                and reserva.inicio < fin_dt
            ):
                raise _ReservaSuperpuestaError(
                    "La reserva se superpone con otra reserva activa de la unidad."
                )
        return inicio_dt, fin_dt
