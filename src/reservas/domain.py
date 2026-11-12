from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Callable


FORMATO_FECHA = "%Y-%m-%dT%H:%M"


@dataclass(frozen=True)
class Reserva:
    id: int
    unidad: str
    solicitante: str
    inicio: datetime
    fin: datetime
    estado: str = "activa"
    fecha_cancelacion: datetime | None = None


class _ReservaSuperpuestaError(ValueError):
    pass


class GestorReservas:
    def __init__(
        self,
        reloj: Callable[[], datetime] = datetime.now,
        db_path=None,
        inventory_path=None,
    ):
        directorio_datos = Path(__file__).resolve().parents[2] / "data"
        self._db_path = (
            Path(db_path)
            if db_path is not None
            else directorio_datos / "reservas.db"
        )
        ruta_inventario = (
            Path(inventory_path)
            if inventory_path is not None
            else directorio_datos / "inventario.json"
        )
        self._inventario = self._cargar_inventario(ruta_inventario)
        self._unidades = frozenset(self._inventario)
        self._reloj = reloj
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._reservas = self._cargar_reservas()

    @property
    def reservas(self):
        return tuple(self._reservas)

    def reservar(self, unidad, solicitante, inicio, fin):
        if not isinstance(solicitante, str) or not solicitante.strip():
            raise ValueError("El solicitante no puede estar vacío.")
        inicio_dt, fin_dt = self._validar_reserva(unidad, inicio, fin)
        with closing(sqlite3.connect(self._db_path)) as conexion:
            with conexion:
                cursor = conexion.execute(
                    """
                    INSERT INTO reservas (unidad, solicitante, inicio, fin, estado)
                    VALUES (?, ?, ?, ?, 'activa')
                    """,
                    (
                        unidad,
                        solicitante,
                        inicio_dt.isoformat(timespec="minutes"),
                        fin_dt.isoformat(timespec="minutes"),
                    ),
                )
                id_reserva = cursor.lastrowid
        reserva = Reserva(id_reserva, unidad, solicitante, inicio_dt, fin_dt)
        self._reservas.append(reserva)
        return reserva

    def reiniciar_datos(self):
        with closing(sqlite3.connect(self._db_path)) as conexion:
            with conexion:
                conexion.execute("DELETE FROM reservas")
        self._reservas.clear()

    def cancelar(self, id_reserva):
        reserva = self.buscar_por_id(id_reserva)
        if reserva.estado != "activa":
            raise ValueError(f"La reserva {id_reserva} ya está cancelada.")

        fecha_cancelacion = self._reloj().replace(microsecond=0)
        with closing(sqlite3.connect(self._db_path)) as conexion:
            with conexion:
                fila = conexion.execute(
                    "SELECT estado FROM reservas WHERE id = ?", (id_reserva,)
                ).fetchone()
                if fila is None:
                    raise KeyError(f"No existe una reserva con id {id_reserva}.")
                if fila[0] != "activa":
                    raise ValueError(f"La reserva {id_reserva} ya está cancelada.")
                cursor = conexion.execute(
                    """
                    UPDATE reservas
                    SET estado = 'cancelada', fecha_cancelacion = ?
                    WHERE id = ? AND estado = 'activa'
                    """,
                    (
                        fecha_cancelacion.isoformat(timespec="seconds"),
                        id_reserva,
                    ),
                )
                if cursor.rowcount != 1:
                    raise ValueError(
                        f"No se pudo cancelar la reserva {id_reserva} porque cambió su estado."
                    )

        cancelada = Reserva(
            id=reserva.id,
            unidad=reserva.unidad,
            solicitante=reserva.solicitante,
            inicio=reserva.inicio,
            fin=reserva.fin,
            estado="cancelada",
            fecha_cancelacion=fecha_cancelacion,
        )
        self._reservas[self._reservas.index(reserva)] = cancelada
        return cancelada

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
        if not isinstance(unidad, str) or unidad not in self._unidades:
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

    @staticmethod
    def _cargar_inventario(ruta_inventario):
        with ruta_inventario.open(encoding="utf-8") as archivo:
            inventario = json.load(archivo)
        if not isinstance(inventario, dict) or not all(
            isinstance(unidad, str)
            and unidad
            and isinstance(equipo, str)
            and equipo
            for unidad, equipo in inventario.items()
        ):
            raise ValueError("El inventario debe asociar cada unidad con su equipo.")
        return inventario

    def _cargar_reservas(self):
        with closing(sqlite3.connect(self._db_path)) as conexion:
            with conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reservas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidad TEXT NOT NULL,
                        solicitante TEXT NOT NULL,
                        inicio TEXT NOT NULL,
                        fin TEXT NOT NULL,
                        estado TEXT NOT NULL,
                        fecha_cancelacion TEXT
                    )
                    """
                )
                filas = conexion.execute(
                    """
                    SELECT id, unidad, solicitante, inicio, fin, estado, fecha_cancelacion
                    FROM reservas
                    ORDER BY id
                    """
                ).fetchall()
        return [
            Reserva(
                id=id_reserva,
                unidad=unidad,
                solicitante=solicitante,
                inicio=datetime.fromisoformat(inicio),
                fin=datetime.fromisoformat(fin),
                estado=estado,
                fecha_cancelacion=(
                    datetime.fromisoformat(fecha_cancelacion)
                    if fecha_cancelacion is not None
                    else None
                ),
            )
            for (
                id_reserva,
                unidad,
                solicitante,
                inicio,
                fin,
                estado,
                fecha_cancelacion,
            ) in filas
        ]
