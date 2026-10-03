"""
config.py
---------
Configurazione centralizzata del progetto. Tutti i parametri
modificabili (pin GPIO, parametri radio, porta seriale, percorsi)
vivono qui per evitare valori "magici" sparsi nel codice.

I valori possono essere sovrascritti tramite variabili d'ambiente,
utile per passare da un Raspberry Pi a un PC di sviluppo senza
toccare il codice.
"""

import os

# ---------------------------------------------------------------------
# Modalita' di acquisizione dati: "radio" (nRF24L01 su Raspberry Pi)
# oppure "serial" (Arduino/microcontrollore via cavo USB)
# ---------------------------------------------------------------------
MODALITA_INPUT = os.getenv("SPACEAL_INPUT_MODE", "serial")  # "serial" | "radio"

# ---------------------------------------------------------------------
# Pin GPIO (BCM) per i pulsanti fisici, usati solo in modalita' "radio"
# su Raspberry Pi. In modalita' "serial" i pulsanti sono mostrati a video.
# ---------------------------------------------------------------------
PIN_AVVIA = int(os.getenv("SPACEAL_PIN_AVVIA", 2))
PIN_PAUSA = int(os.getenv("SPACEAL_PIN_PAUSA", 3))
PIN_RESET = int(os.getenv("SPACEAL_PIN_RESET", 4))
PIN_REFRESH = int(os.getenv("SPACEAL_PIN_REFRESH", 5))

# ---------------------------------------------------------------------
# Configurazione radio nRF24L01
# ---------------------------------------------------------------------
RADIO_CE_PIN = int(os.getenv("SPACEAL_RADIO_CE_PIN", 22))
RADIO_CSN_PIN = int(os.getenv("SPACEAL_RADIO_CSN_PIN", 0))  # CE0 = GPIO8
RADIO_CHANNEL = int(os.getenv("SPACEAL_RADIO_CHANNEL", 76))
RADIO_PAYLOAD_SIZE = int(os.getenv("SPACEAL_RADIO_PAYLOAD_SIZE", 32))
RADIO_PIPE_ADDRESS = os.getenv("SPACEAL_RADIO_ADDRESS", "00001").encode()

# ---------------------------------------------------------------------
# Configurazione porta seriale (Arduino / microcontrollore via USB)
# ---------------------------------------------------------------------
SERIAL_PORT = os.getenv("SPACEAL_SERIAL_PORT", "COM3")
SERIAL_BAUDRATE = int(os.getenv("SPACEAL_SERIAL_BAUDRATE", 9600))
SERIAL_TIMEOUT = float(os.getenv("SPACEAL_SERIAL_TIMEOUT", 5))

# ---------------------------------------------------------------------
# Intervalli di aggiornamento dell'interfaccia (millisecondi)
# ---------------------------------------------------------------------
INTERVALLO_LETTURA_MS = int(os.getenv("SPACEAL_INTERVAL_READ_MS", 1000))
INTERVALLO_GRAFICO_MS = int(os.getenv("SPACEAL_INTERVAL_GRAPH_MS", 2000))
INTERVALLO_TIMER_MS = int(os.getenv("SPACEAL_INTERVAL_TIMER_MS", 200))

# ---------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------
IMMAGINE_PARACADUTE_URL = os.getenv(
    "SPACEAL_PARACHUTE_IMG_URL",
    "https://e7.pngegg.com/pngimages/227/461/png-clipart-military-with-"
    "parachute-parachute-parachuting-paratrooper-military-parachute-army-"
    "desktop-wallpaper-thumbnail.png",
)

# Percorso opzionale al modello 3D del razzo (.stl), solo informativo:
# non e' attualmente caricato nella UI, ma e' previsto come estensione futura.
PERCORSO_MODELLO_STL = os.getenv("SPACEAL_STL_PATH", "")

