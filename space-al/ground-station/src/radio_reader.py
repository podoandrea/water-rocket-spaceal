"""
radio_reader.py
----------------
Acquisizione dati telemetrici via radio nRF24L01 (pyRF24), pensata
per l'esecuzione su Raspberry Pi con modulo radio collegato via SPI.

Il protocollo applicativo si aspetta 4 pacchetti consecutivi da 32
byte, ciascuno contenente un intero a 4 byte little-endian:
    1) pitch
    2) roll
    3) altitudine
    4) stato paracadute (0 = chiuso, 1 = aperto)

Se il modulo pyrf24 o RPi.GPIO non sono disponibili (es. sviluppo su
PC), la classe espone comunque la stessa interfaccia ma solleva un
errore chiaro al momento dell'uso, cosi' il resto dell'app puo'
importare il modulo senza errori su piattaforme non Raspberry.
"""

import struct
import time

try:
    from pyrf24 import RF24, RF24_PA_MAX, RF24_1MBPS
    _RF24_DISPONIBILE = True
except ImportError:  # pragma: no cover - dipende dalla piattaforma
    _RF24_DISPONIBILE = False


class RadioReader:
    def __init__(self, ce_pin, csn_pin, channel, payload_size, pipe_address):
        if not _RF24_DISPONIBILE:
            raise RuntimeError(
                "Il modulo 'pyrf24' non e' disponibile. "
                "RadioReader puo' essere usato solo su Raspberry Pi con "
                "pyRF24 installato. Usa SerialReader in alternativa."
            )

        self.radio = RF24(ce_pin, csn_pin)
        self.radio.begin()
        self.radio.setPayloadSize(payload_size)
        self.radio.setChannel(channel)
        self.radio.setDataRate(RF24_1MBPS)
        self.radio.set_pa_level(RF24_PA_MAX)
        self.radio.openReadingPipe(1, pipe_address)
        self.radio.startListening()

    def _leggi_intero(self, timeout=1.0):
        """Attende e legge un intero a 4 byte da un pacchetto da 32 byte."""
        attesa_iniziale = time.monotonic()
        while not self.radio.available():
            if time.monotonic() - attesa_iniziale > timeout:
                raise TimeoutError("Timeout in attesa di un pacchetto radio")
            time.sleep(0.01)

        buffer = self.radio.read(32)
        return struct.unpack("<i", buffer[0:4])[0]

    def leggi_coordinate(self):
        """
        Legge una quaterna completa (pitch, roll, alt, paracadute).

        Ritorna un dizionario {"x", "y", "alt", "paracadute_aperto"}.
        Solleva TimeoutError se i dati non arrivano in tempo: il
        chiamante decide come gestire l'assenza di dati (es. mantenere
        l'ultimo valore noto).
        """
        if not self.radio.available():
            return None

        pitch = self._leggi_intero()
        roll = self._leggi_intero()
        alt = self._leggi_intero()
        paracadute = self._leggi_intero()

        return {
            "x": roll,
            "y": pitch,
            "alt": alt,
            "paracadute_aperto": paracadute == 1,
        }

