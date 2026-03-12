"""
apps/qr_codes/services.py
==========================
Servicios del módulo QR:
  - HikvisionService: integración con dispositivo vía ISAPI (Digest Auth)
  - generar_qr_base64: generación de imagen QR en base64

Documentación ISAPI de referencia:
  /ISAPI/AccessControl/UserInfo/Record  (POST) — crear usuario temporal
  /ISAPI/AccessControl/CardInfo/Record  (POST) — asignar tarjeta QR
  /ISAPI/AccessControl/UserInfo/Delete  (PUT)  — eliminar usuario
"""

import base64
import io
import logging
from dataclasses import dataclass
from datetime import datetime

import qrcode
import requests
from requests.auth import HTTPDigestAuth
from django.utils.timezone import localtime

logger = logging.getLogger(__name__)


@dataclass
class ResultadoHikvision:
    """Resultado de una operación ISAPI."""

    exitoso: bool
    codigo_status: int
    mensaje: str
    respuesta_raw: str


class HikvisionService:
    """
    Cliente para la API ISAPI del dispositivo Hikvision.
    Usa autenticación Digest conforme al protocolo del dispositivo.

    Ejemplo de uso:
        config = ConfiguracionHikvision.objects.first()
        svc = HikvisionService(config)
        resultado = svc.crear_pase_completo("20240601120000001", inicio, fin)
    """

    # Formato de fecha requerido por ISAPI (sin zona horaria — el device usa timeType: local)
    FORMATO_FECHA_ISAPI = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, config) -> None:
        """
        Args:
            config: Instancia de ConfiguracionHikvision con los parámetros de conexión.
        """
        self._url_base = config.url_base
        self._auth = HTTPDigestAuth(config.usuario, config.password)
        self._puerta = config.puerta
        self._timeout = 10  # segundos

    # ------------------------------------------------------------------
    # Operaciones públicas
    # ------------------------------------------------------------------

    def crear_pase_completo(
        self,
        employee_no: str,
        inicio: datetime,
        fin: datetime,
    ) -> tuple[ResultadoHikvision, ResultadoHikvision]:
        """
        Ejecuta el flujo completo: crea usuario y luego asigna tarjeta QR.

        Returns:
            Tupla (resultado_usuario, resultado_tarjeta).
            Si el usuario falla, la tarjeta no se intenta.
        """
        # Convertir a hora local antes de formatear.
        # timezone.now() devuelve UTC; el dispositivo espera hora local
        # (timeType="local"), igual que el script standalone que usa datetime.now().
        inicio_str = self._fmt_local(inicio)
        fin_str    = self._fmt_local(fin)

        resultado_usuario = self.crear_usuario_temporal(employee_no, inicio_str, fin_str)

        if not resultado_usuario.exitoso:
            logger.error(
                "Fallo al crear usuario Hikvision [%s]: %s",
                employee_no,
                resultado_usuario.mensaje,
            )
            resultado_tarjeta = ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje="Omitido: el usuario no fue creado.",
                respuesta_raw="",
            )
            return resultado_usuario, resultado_tarjeta

        resultado_tarjeta = self.asignar_tarjeta_qr(employee_no)

        if not resultado_tarjeta.exitoso:
            logger.error(
                "Fallo al asignar tarjeta QR [%s]: %s",
                employee_no,
                resultado_tarjeta.mensaje,
            )

        return resultado_usuario, resultado_tarjeta

    def crear_usuario_temporal(
        self,
        employee_no: str,
        inicio_str: str,
        fin_str: str,
    ) -> ResultadoHikvision:
        """
        Crea un usuario temporal (tipo visitor) en el dispositivo.

        Args:
            employee_no: Identificador único del ticket (será usado como employeeNo).
            inicio_str: Fecha de inicio en formato ISAPI.
            fin_str: Fecha de fin en formato ISAPI.
        """
        url = f"{self._url_base}/ISAPI/AccessControl/UserInfo/Record?format=json"
        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": "Pasajero",
                "userType": "visitor",
                "doorRight": str(self._puerta),
                "RightPlan": [
                    {
                        "doorNo": self._puerta,
                        "planTemplateNo": "1",
                    }
                ],
                "Valid": {
                    "enable": True,
                    "beginTime": inicio_str,
                    "endTime": fin_str,
                    "timeType": "local",
                },
            }
        }

        logger.info("Creando usuario Hikvision: %s", employee_no)
        return self._post(url, payload)

    def asignar_tarjeta_qr(self, employee_no: str) -> ResultadoHikvision:
        """
        Asigna el código como tarjeta QR al usuario previamente creado.

        Args:
            employee_no: El mismo código usado en crear_usuario_temporal.
        """
        url = f"{self._url_base}/ISAPI/AccessControl/CardInfo/Record?format=json"
        payload = {
            "CardInfo": {
                "employeeNo": employee_no,
                "cardNo": employee_no,
                "cardType": "normalCard",
            }
        }

        logger.info("Asignando tarjeta QR Hikvision: %s", employee_no)
        return self._post(url, payload)

    def eliminar_usuario(self, employee_no: str) -> ResultadoHikvision:
        """
        Elimina un usuario del dispositivo (uso en expiración o cancelación).

        Args:
            employee_no: Identificador del usuario a eliminar.
        """
        url = f"{self._url_base}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [{"employeeNo": employee_no}]
            }
        }

        logger.info("Eliminando usuario Hikvision: %s", employee_no)
        return self._put(url, payload)

    def probar_conexion(self) -> ResultadoHikvision:
        """
        Verifica la conectividad con el dispositivo consultando su información básica.
        """
        url = f"{self._url_base}/ISAPI/System/deviceInfo"
        try:
            response = requests.get(
                url,
                auth=self._auth,
                timeout=self._timeout,
            )
            exitoso = response.status_code == 200
            return ResultadoHikvision(
                exitoso=exitoso,
                codigo_status=response.status_code,
                mensaje="Conexión exitosa." if exitoso else "Dispositivo respondió con error.",
                respuesta_raw=response.text[:500],
            )
        except requests.exceptions.ConnectionError:
            return ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje=f"No se puede conectar al dispositivo en {self._url_base}.",
                respuesta_raw="",
            )
        except requests.exceptions.Timeout:
            return ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje=f"Tiempo de espera agotado ({self._timeout}s).",
                respuesta_raw="",
            )

    # ------------------------------------------------------------------
    # Métodos privados de utilidad
    # ------------------------------------------------------------------

    def _fmt_local(self, dt: datetime) -> str:
        """
        Formatea un datetime como hora LOCAL sin zona horaria para la ISAPI.

        El dispositivo Hikvision trabaja con timeType='local', por lo que
        espera las fechas en hora local de la máquina, igual que el script
        standalone que usa datetime.now().

        Si el datetime es timezone-aware (ej. UTC de Django), lo convierte
        a la zona horaria local del servidor antes de formatear.
        """
        if dt.tzinfo is not None:
            dt = localtime(dt)          # convierte UTC → hora local del servidor
        return dt.strftime(self.FORMATO_FECHA_ISAPI)

    # ------------------------------------------------------------------
    # Métodos privados de transporte HTTP
    # ------------------------------------------------------------------

    def _post(self, url: str, payload: dict) -> ResultadoHikvision:
        return self._request("POST", url, payload)

    def _put(self, url: str, payload: dict) -> ResultadoHikvision:
        return self._request("PUT", url, payload)

    def _request(self, method: str, url: str, payload: dict) -> ResultadoHikvision:
        """Ejecuta una petición HTTP autenticada y normaliza el resultado."""
        try:
            response = requests.request(
                method,
                url,
                json=payload,
                auth=self._auth,
                timeout=self._timeout,
            )

            # Hikvision retorna statusCode en el body para indicar éxito/fallo
            exitoso = response.status_code in (200, 201)
            if exitoso:
                try:
                    body = response.json()
                    status_code_hik = body.get("statusCode", 0)
                    # statusCode 1 = success en ISAPI
                    exitoso = status_code_hik == 1
                    mensaje = body.get("statusString", "OK" if exitoso else "Error ISAPI")
                except Exception:
                    mensaje = "Respuesta no JSON"

            logger.debug(
                "%s %s → HTTP %s | Exitoso: %s",
                method, url, response.status_code, exitoso,
            )

            return ResultadoHikvision(
                exitoso=exitoso,
                codigo_status=response.status_code,
                mensaje=mensaje if exitoso else response.text[:200],
                respuesta_raw=response.text[:1000],
            )

        except requests.exceptions.ConnectionError as exc:
            logger.error("Error de conexión a Hikvision: %s", exc)
            return ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje=f"Error de conexión: {exc}",
                respuesta_raw="",
            )
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con Hikvision")
            return ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje=f"Tiempo de espera agotado ({self._timeout}s).",
                respuesta_raw="",
            )
        except Exception as exc:
            logger.exception("Error inesperado en HikvisionService: %s", exc)
            return ResultadoHikvision(
                exitoso=False,
                codigo_status=0,
                mensaje=f"Error inesperado: {exc}",
                respuesta_raw="",
            )


# ---------------------------------------------------------------------------
# Utilidades de generación QR
# ---------------------------------------------------------------------------

def generar_qr_base64(contenido: str) -> str:
    """
    Genera una imagen QR PNG a partir del contenido y la retorna
    como string base64 con el prefijo data URI para uso directo en HTML.

    Args:
        contenido: Texto que codificará el QR (generalmente el código del ticket).

    Returns:
        String con formato: "data:image/png;base64,<datos>"
    """
    qr = qrcode.QRCode(
        version=None,          # Tamaño automático según el contenido
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% de corrección
        box_size=10,
        border=4,
    )
    qr.add_data(contenido)
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    datos_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{datos_base64}"
