from collections import Counter


def agregar_por_mes(eventos: list[dict]) -> list[dict]:
    """
    Recibe los eventos clasificados del logbook y los cuenta por
    (turbina, mes, anio). Devuelve una fila por combinacion.

    Entrada:  [{codigo_turbina, fecha_inicio, mes, anio, tipo_warning}, ...]
    Salida:   [{codigo_turbina, mes, anio, cantidad}, ...]
    """
    contador = Counter(
        (e["codigo_turbina"], e["mes"], e["anio"])
        for e in eventos
    )

    return [
        {"codigo_turbina": turbina, "mes": mes, "anio": anio, "cantidad": cantidad}
        for (turbina, mes, anio), cantidad in contador.items()
    ]


def agregar_por_tipo(eventos: list[dict]) -> list[dict]:
    """
    Cuenta los eventos por (turbina, tipo, mes, anio). A diferencia del
    seed de Peralta, los datos del logbook SI tienen mes y anio, asi que
    los conservamos.

    Entrada:  [{codigo_turbina, fecha_inicio, mes, anio, tipo_warning}, ...]
    Salida:   [{codigo_turbina, tipo, mes, anio, cantidad}, ...]
    """
    contador = Counter(
        (e["codigo_turbina"], e["tipo_warning"], e["mes"], e["anio"])
        for e in eventos
    )

    return [
        {"codigo_turbina": turbina, "tipo": tipo, "mes": mes, "anio": anio, "cantidad": cantidad}
        for (turbina, tipo, mes, anio), cantidad in contador.items()
    ]