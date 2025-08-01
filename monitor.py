import os
import time
import requests
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
OLT_URL = "https://10.109.250.81"
STATUS_URL = f"{OLT_URL}/action/onustatusinfo.html"
LOGIN_URL = f"{OLT_URL}/action/login.html"

USERNAME = os.getenv("OLT_USER")
PASSWORD = os.getenv("OLT_PASS")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

INTERVALO = 60

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    requests.post(url, data=data)

def login():
    session = requests.Session()
    payload = {"username": USERNAME, "password": PASSWORD}
    r = session.post(LOGIN_URL, data=payload, verify=False)
    return session

def revisar_onus(session):
    try:
        # Simular click en Refresh
        r = session.post(STATUS_URL, data={"port_refresh": "Refresh"}, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        filas = soup.find_all("tr")[1:]
        for fila in filas:
            columnas = [c.text.strip() for c in fila.find_all("td")]
            if len(columnas) > 5:
                onu_id = columnas[0]
                phase_state = columnas[3]
                descripcion = columnas[4]
                if phase_state.lower() == "los":
                    mensaje = f"⚠️ ALERTA ONU\nID: {onu_id}\nEstado: {phase_state}\nDesc: {descripcion}"
                    enviar_telegram(mensaje)
    except Exception as e:
        print("Error revisando ONUs:", e)

if __name__ == "__main__":
    while True:
        sesion = login()
        if sesion:
            revisar_onus(sesion)
        time.sleep(INTERVALO)

