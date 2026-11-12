import argparse
import os
import sqlite3
import sys

from .domain import GestorReservas, Reserva


FORMATO_FECHA = "%Y-%m-%dT%H:%M"


def _formatear_reserva(reserva: Reserva) -> str:
    inicio = reserva.inicio.strftime(FORMATO_FECHA)
    fin = reserva.fin.strftime(FORMATO_FECHA)
    texto = (
        f"ID: {reserva.id} | Unidad: {reserva.unidad} | "
        f"Solicitante: {reserva.solicitante} | {inicio} a {fin} | "
        f"Estado: {reserva.estado}"
    )
    if reserva.fecha_cancelacion is not None:
        texto += (
            " | Cancelada: "
            + reserva.fecha_cancelacion.isoformat(timespec="seconds")
        )
    return texto


def _crear_parser():
    parser = argparse.ArgumentParser(
        prog="reservas",
        description="Gestiona las reservas del laboratorio.",
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("RESERVAS_DB"),
        help="ruta de la base SQLite (o variable RESERVAS_DB)",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    disponibilidad = subparsers.add_parser(
        "disponibilidad", help="consultar una unidad en un intervalo"
    )
    disponibilidad.add_argument("unidad")
    disponibilidad.add_argument("inicio")
    disponibilidad.add_argument("fin")

    reservar = subparsers.add_parser("reservar", help="crear una reserva")
    reservar.add_argument("unidad")
    reservar.add_argument("solicitante")
    reservar.add_argument("inicio")
    reservar.add_argument("fin")

    cancelar = subparsers.add_parser("cancelar", help="cancelar una reserva por ID")
    cancelar.add_argument("id", type=int)

    subparsers.add_parser("listar", help="listar reservas activas y canceladas")
    subparsers.add_parser(
        "reiniciar-datos", help="borrar todas las reservas previa confirmación"
    )
    return parser


def main(argv=None, input_fn=input):
    parser = _crear_parser()
    argumentos = parser.parse_args(argv)
    try:
        gestor = GestorReservas(db_path=argumentos.db)
        if argumentos.comando == "disponibilidad":
            disponible = gestor.consultar_disponibilidad(
                argumentos.unidad, argumentos.inicio, argumentos.fin
            )
            print("Disponible." if disponible else "No disponible.")
        elif argumentos.comando == "reservar":
            reserva = gestor.reservar(
                argumentos.unidad,
                argumentos.solicitante,
                argumentos.inicio,
                argumentos.fin,
            )
            print(f"Reserva creada con ID {reserva.id}.")
        elif argumentos.comando == "cancelar":
            reserva = gestor.cancelar(argumentos.id)
            print(f"Reserva {reserva.id} cancelada.")
        elif argumentos.comando == "listar":
            if not gestor.reservas:
                print("No hay reservas.")
            else:
                for reserva in gestor.reservas:
                    print(_formatear_reserva(reserva))
        elif argumentos.comando == "reiniciar-datos":
            try:
                confirmacion = input_fn(
                    "Esto borrará todas las reservas. Escriba SI para confirmar: "
                )
            except EOFError:
                print(
                    "Error: no se recibió confirmación; "
                    "no se modificaron las reservas.",
                    file=sys.stderr,
                )
                return 1
            if confirmacion != "SI":
                print("Operación cancelada; no se modificaron las reservas.")
                return 1
            gestor.reiniciar_datos()
            print("Datos de reservas reiniciados.")
        return 0
    except (ValueError, KeyError, sqlite3.Error, OSError) as error:
        mensaje = error.args[0] if isinstance(error, KeyError) else str(error)
        print(f"Error: {mensaje}", file=sys.stderr)
        return 1
