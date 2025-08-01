import os
import time
import requests
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DESDE VARIABLES DE ENTORNO ---
OLT_URL = "https://10.109.250.81"
LOGIN_URL = f"{OLT_URL}/action/login.html"
STATUS_URL = f"{OLT_URL}/action/onustatusinfo.html"

USERNAME = os.getenv("OLT_USER")
PASSWORD = os.getenv("OLT_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Intervalo en segundos
INTERVALO = 60


def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print("Mensaje enviado a Telegram")
        else:
            print("Error enviando a Telegram:", r.text)
    except Exception as e:
        print("Error enviando a Telegram:", e)


def login():
    session = requests.Session()
    payload = {"username": USERNAME, "password": PASSWORD}
    try:
        r = session.post(LOGIN_URL, data=payload, verify=False, timeout=10)
        if r.status_code == 200:
            print("Login correcto en OLT")
            return session
    except Exception as e:
        print("Error al loguearse:", e)
    return None


def revisar_onus(session):
    try:
        # Simular el clic en Refresh
        payload_refresh = {"port_refresh": "Refresh"}
        session.post(STATUS_URL, data=payload_refresh, verify=False, timeout=10)

        # Obtener tabla actualizada
        r = session.get(STATUS_URL, verify=False, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        filas = soup.find_all("tr")[1:]  # Ignorar encabezado

        if not filas:
            print("⚠️ No se encontraron ONUs en la tabla.")
            return

        for fila in filas:
            columnas = [c.text.strip() for c in fila.find_all("td")]
            if len(columnas) > 5:
                onu_id = columnas[0]
                phase_state = columnas[3]
                descripcion = columnas[4]
                motivo = columnas[7] if len(columnas) > 7 else "N/A"

                if phase_state.lower() == "los":
                    mensaje = (f"⚠️ ALERTA ONU\n"
                               f"ID: {onu_id}\n"
                               f"Estado: {phase_state}\n"
                               f"Descripción: {descripcion}\n"
                               f"Motivo: {motivo}")
                    enviar_telegram(mensaje)
                    print("Alerta enviada:", mensaje)

    except Exception as e:
        print("Error revisando ONUs:", e)


if __name__ == "__main__":
    enviar_telegram("✅ Monitor iniciado en Render. Conexión a Telegram funcionando.")
    while True:
        sesion = login()
        if sesion:
            revisar_onus(sesion)
        else:
            print("No se pudo iniciar sesión en la OLT.")
        time.sleep(INTERVALO)
