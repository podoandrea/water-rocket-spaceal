"""
gpio_compat.py
---------------
Wrapper per RPi.GPIO che permette di eseguire l'applicazione anche su
piattaforme diverse da Raspberry Pi (Windows/macOS/Linux desktop) per
test e sviluppo, senza alterare la logica dei pulsanti fisici.

Su Raspberry Pi (Linux) viene importato il modulo reale RPi.GPIO.
Su qualsiasi altra piattaforma viene usato un mock che simula i
pulsanti sempre "non premuti" (HIGH), cosi' l'app si avvia comunque
e i pulsanti a schermo restano l'unico modo di interagire.
"""

import sys
import types


def get_gpio():
    if sys.platform.startswith("linux"):
        try:
            import RPi.GPIO as GPIO
            return GPIO
        except ImportError:
            pass  # ambiente Linux ma senza RPi.GPIO: si usa il mock sotto

    return types.SimpleNamespace(
        BCM=0,
        IN=0,
        LOW=0,
        HIGH=1,
        setmode=lambda mode: None,
        setup=lambda pin, mode: None,
        input=lambda pin: 1,  # sempre HIGH = pulsante non premuto
        cleanup=lambda *a, **k: None,
    )

