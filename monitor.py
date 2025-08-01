import time
import requests
from bs4 import BeautifulSoup
import os
from flask import Flask
import threading

# --- CONFIGURACIÓN ---
OLT_URL = "https://10.109.250.81"
LOGIN_URL = f"{OLT_URL}/action/login.html"
STATUS_URL = f"{OLT_URL}/action/onustatusinfo.html"  # Página con Phase State
USERNAME = os.getenv("OLT_USER", "scraping")
PASSWORD = os.getenv("OLT_PASS", "monitoreo1234")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Intervalo en segundos
INTERVALO = 60


def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code != 200:
            print("Error enviando a Telegram:", r.text)
    except Exception as e:
        print("Error enviando a Telegram:", e)


def login():
    session = requests.Session()
    payload = {"username": USERNAME, "password": PASSWORD}
    try:
        r = session.post(LOGIN_URL, data=payload, verify=False, timeout=10)
        if r.status_code == 200:
            return session
    except Exception as e:
        print("Error al loguearse:", e)
    return None


def revisar_onus(session):
    try:
        r = session.get(STATUS_URL, verify=False, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        filas = soup.find_all("tr")[1:]  # Ignorar encabezado

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


def loop_monitor():
    while True:
        sesion = login()
        if sesion:
            revisar_onus(sesion)
        else:
            print("No se pudo iniciar sesión en la OLT.")
        time.sleep(INTERVALO)


# --- Flask para Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Monitor de ONU corriendo en Render"


if __name__ == "__main__":
    # Hilo para el monitor
    t = threading.Thread(target=loop_monitor, daemon=True)
    t.start()

    # Flask para que Render detecte el puerto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
