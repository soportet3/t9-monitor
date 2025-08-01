import time
import os
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

# --- CONFIGURACIÓN ---
OLT_URL = "https://10.109.250.81"
LOGIN_URL = f"{OLT_URL}/action/login.html"
STATUS_URL = f"{OLT_URL}/action/onustatusinfo.html"  # Página con Phase State

# Variables desde el entorno de Render
USERNAME = os.getenv("OLT_USER", "scraping")
PASSWORD = os.getenv("OLT_PASS", "monitoreo1234")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Intervalo en segundos
INTERVALO = 60

# Iniciar Flask para mantener vivo el servicio
app = Flask(__name__)

@app.route('/')
def index():
    return "Servicio de monitoreo OLT en ejecución 🚀"


def enviar_telegram(mensaje):
    """Envía un mensaje a Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code != 200:
            print("Error en Telegram:", r.text)
    except Exception as e:
        print("Error enviando a Telegram:", e)


def login():
    """Inicia sesión en la OLT."""
    session = requests.Session()
    payload = {"username": USERNAME, "password": PASSWORD}
    try:
        r = session.post(LOGIN_URL, data=payload, verify=False, timeout=10)
        if r.status_code == 200:
            return session
    except Exception as e:
        print("Error al loguearse:", e)
    return None


def revisar_onus():
    """Revisa el estado de las ONUs y envía alerta si detecta LOS."""
    while True:
        sesion = login()
        if sesion:
            try:
                r = sesion.get(STATUS_URL, verify=False, timeout=10)
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
        else:
            print("No se pudo iniciar sesión en la OLT.")

        time.sleep(INTERVALO)


if __name__ == "__main__":
    # Mensaje de prueba para verificar Telegram
    enviar_telegram("✅ Monitor iniciado en Render. Conexión a Telegram funcionando.")
    
    # Lanzar revisión de ONUs en segundo plano
    hilo = threading.Thread(target=revisar_onus, daemon=True)
    hilo.start()

    # Flask mantiene vivo el contenedor en Render
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
