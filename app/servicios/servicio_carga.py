from sqlalchemy.orm import Session
from app.modelos.parque import Parque
from app.modelos.carga import Carga
from app.repositorios.repositorio_turbina import RepositorioTurbina
from app.repositorios.repositorio_inspeccion import RepositorioInspeccion
from app.repositorios.repositorio_carga import RepositorioCarga
from app.repositorios.repositorio_warning_por_mes import RepositorioWarningPorMes
from app.repositorios.repositorio_warning_por_tipo import RepositorioWarningPorTipo
from app.etl.parser_rodamientos import parsear_estado_rodamientos, parsear_nuevo_control
from app.etl.parser_logbook import parsear_logbook
from app.etl.agregador_warnings import agregar_por_mes, agregar_por_tipo
from app.etl.parser_warnings_peralta import (
    parsear_warnings_mensuales,
    parsear_warnings_por_tipo,
)


class ServicioCarga:
    """
    Orquesta todo el proceso de carga de Excels a la DB.

    Unico lugar del sistema que:
      - conoce la sesion y controla la transaccion (commit / rollback)
      - sabe que existen parsers Y repositorios a la vez
    Los parsers no saben de la DB. Los repositorios no saben de Excel.
    """

    def __init__(self, sesion: Session):
        self.sesion          = sesion
        self.repo_turbina    = RepositorioTurbina(sesion)
        self.repo_inspeccion = RepositorioInspeccion(sesion)
        self.repo_carga      = RepositorioCarga(sesion)
        self.repo_warn_mes   = RepositorioWarningPorMes(sesion)
        self.repo_warn_tipo  = RepositorioWarningPorTipo(sesion)

    def _obtener_parque(self, codigo: str) -> Parque:
        parque = self.sesion.query(Parque).filter_by(codigo=codigo).first()
        if not parque:
            raise ValueError(f"Parque '{codigo}' no encontrado. Corriste seed.py?")
        return parque

    def _insertar_inspecciones(self, registros: list[dict], parque_id: int, carga_id: int) -> dict:
        """Logica compartida entre el seed y la carga mensual de rodamientos."""
        insertados = 0
        omitidos   = 0
        for reg in registros:
            turbina = self.repo_turbina.obtener_por_codigo(parque_id, reg["codigo_turbina"])
            if not turbina or reg.get("fecha") is None:
                omitidos += 1
                continue
            datos = {k: v for k, v in reg.items() if k != "codigo_turbina"}
            if self.repo_inspeccion.insertar_si_no_existe(turbina.id, datos, carga_id):
                insertados += 1
            else:
                omitidos += 1
        return {"insertados": insertados, "omitidos": omitidos}

    # ---------------------------------------------------------------
    #  RODAMIENTOS
    # ---------------------------------------------------------------

    def cargar_seed_rodamientos(self, ruta: str, codigo_parque: str, nombre_archivo: str) -> dict:
        """Carga inicial: hoja Estado_Rodamientos (una vez por parque)."""
        try:
            parque = self._obtener_parque(codigo_parque)
            carga  = self.repo_carga.crear(parque.id, "seed_rodamientos", nombre_archivo)

            registros = parsear_estado_rodamientos(ruta)
            resultado = self._insertar_inspecciones(registros, parque.id, carga.id)

            carga.estado               = "exitosa"
            carga.registros_insertados = resultado["insertados"]
            self.sesion.commit()
            return {"estado": "exitosa", "carga_id": carga.id, **resultado}
        except Exception as error:
            self.sesion.rollback()
            raise RuntimeError(f"Error en seed de rodamientos: {error}") from error

    def cargar_control_mensual(self, ruta: str, codigo_parque: str, nombre_archivo: str) -> dict:
        """Carga mensual: hoja Nuevo_Control_De_Rodamientos (la de las X)."""
        try:
            parque = self._obtener_parque(codigo_parque)
            carga  = self.repo_carga.crear(parque.id, "control_mensual", nombre_archivo)

            registros = parsear_nuevo_control(ruta)
            resultado = self._insertar_inspecciones(registros, parque.id, carga.id)

            carga.estado               = "exitosa"
            carga.registros_insertados = resultado["insertados"]
            self.sesion.commit()
            return {"estado": "exitosa", "carga_id": carga.id, **resultado}
        except Exception as error:
            self.sesion.rollback()
            raise RuntimeError(f"Error en control mensual: {error}") from error

    # ---------------------------------------------------------------
    #  WARNINGS
    # ---------------------------------------------------------------

    def cargar_logbook(self, ruta: str, codigo_parque: str, nombre_archivo: str) -> dict:
        """
        Carga mensual de warnings (ambos parques). Lee el logbook,
        clasifica, AGREGA a conteos, y guarda en las dos tablas.
        """
        try:
            parque = self._obtener_parque(codigo_parque)
            carga  = self.repo_carga.crear(parque.id, "logbook", nombre_archivo)

            eventos = parsear_logbook(ruta, codigo_parque)

            ins_mes  = self._guardar_conteos(agregar_por_mes(eventos),  parque.id, carga.id, self.repo_warn_mes,  "mes")
            ins_tipo = self._guardar_conteos(agregar_por_tipo(eventos), parque.id, carga.id, self.repo_warn_tipo, "tipo")

            carga.estado               = "exitosa"
            carga.registros_insertados = ins_mes + ins_tipo
            self.sesion.commit()
            return {
                "estado": "exitosa", "carga_id": carga.id,
                "eventos_clasificados": len(eventos),
                "conteos_por_mes": ins_mes, "conteos_por_tipo": ins_tipo,
            }
        except Exception as error:
            self.sesion.rollback()
            raise RuntimeError(f"Error al cargar logbook: {error}") from error

    def cargar_seed_warnings_peralta(self, ruta: str, nombre_archivo: str) -> dict:
        """
        Carga inicial SOLO de Peralta: las dos hojas pre-agregadas
        (Warnings_Mensuales + Warnings_por_Tipo). Corre una vez.
        """
        try:
            parque = self._obtener_parque("PSP")
            carga  = self.repo_carga.crear(parque.id, "seed_warnings", nombre_archivo)

            ins_mes  = self._guardar_conteos(parsear_warnings_mensuales(ruta), parque.id, carga.id, self.repo_warn_mes,  "mes")
            ins_tipo = self._guardar_conteos(parsear_warnings_por_tipo(ruta),  parque.id, carga.id, self.repo_warn_tipo, "tipo")

            carga.estado               = "exitosa"
            carga.registros_insertados = ins_mes + ins_tipo
            self.sesion.commit()
            return {
                "estado": "exitosa", "carga_id": carga.id,
                "conteos_por_mes": ins_mes, "conteos_por_tipo": ins_tipo,
            }
        except Exception as error:
            self.sesion.rollback()
            raise RuntimeError(f"Error en seed de warnings Peralta: {error}") from error

    def _guardar_conteos(self, conteos: list[dict], parque_id: int, carga_id: int, repo, etiqueta: str) -> int:
        """Inserta una lista de conteos usando el repo correspondiente."""
        insertados = 0
        for c in conteos:
            turbina = self.repo_turbina.obtener_por_codigo(parque_id, c["codigo_turbina"])
            if not turbina:
                continue
            datos = {k: v for k, v in c.items() if k != "codigo_turbina"}
            if repo.insertar_si_no_existe(turbina.id, datos, carga_id):
                insertados += 1
        return insertados

    # ---------------------------------------------------------------
    #  REVERSION
    # ---------------------------------------------------------------

    def revertir_carga(self, carga_id: int) -> dict:
        """Elimina todo lo insertado por una carga y la marca como revertida."""
        try:
            carga = self.sesion.get(Carga, carga_id)
            if not carga:
                raise ValueError(f"Carga {carga_id} no encontrada")
            if carga.estado == "revertida":
                raise ValueError(f"La carga {carga_id} ya fue revertida")

            total = (
                self.repo_inspeccion.eliminar_por_carga(carga_id)
                + self.repo_warn_mes.eliminar_por_carga(carga_id)
                + self.repo_warn_tipo.eliminar_por_carga(carga_id)
            )
            carga.estado = "revertida"
            self.sesion.commit()
            return {"estado": "revertida", "carga_id": carga_id, "registros_eliminados": total}
        except Exception as error:
            self.sesion.rollback()
            raise RuntimeError(f"Error al revertir carga: {error}") from error