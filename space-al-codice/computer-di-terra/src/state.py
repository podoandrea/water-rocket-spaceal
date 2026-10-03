"""
state.py
--------
Stato globale condiviso dall'applicazione: cronometro, dati dei voli
in corso e storico dei lanci precedenti.

Tenere lo stato in un modulo separato permette ai callback Dash di
importarlo senza creare dipendenze circolari tra app.py e i moduli
di acquisizione dati (radio_reader.py / serial_reader.py).
"""

import threading
import time


class FlightState:
    """Stato condiviso e thread-safe per cronometro e dati di volo."""

    def __init__(self):
        self._lock = threading.Lock()

        # Cronometro
        self.tempo = 0.0
        self.in_esecuzione = False
        self.reset_flag = False
        self.tempo_inizio = 0.0

        # Stato paracadute (per lancio corrente)
        self.stato_paracadute = False

        # Serie del lancio in corso
        self.asse_x = []
        self.asse_y = []

        # Storico dei lanci completati: lista di tuple (asse_x, asse_y)
        self.storico_grafici = []
        # Storico tempi: lista di tuple (tempo_inizio, tempo_fine)
        self.storico_tempi = []

    # ------------------------------------------------------------------
    # Cronometro
    # ------------------------------------------------------------------
    def avvia(self):
        with self._lock:
            if not self.in_esecuzione:
                self.tempo_inizio = self.tempo
            self.in_esecuzione = True
            self.reset_flag = False

    def pausa(self):
        with self._lock:
            self.in_esecuzione = False
            self.reset_flag = False

    def reset(self):
        """Archivia il lancio corrente nello storico e azzera il cronometro."""
        with self._lock:
            self.stato_paracadute = False
            if self.asse_x and self.asse_y:
                self.storico_grafici.append((self.asse_x.copy(), self.asse_y.copy()))
                self.storico_tempi.append((self.tempo_inizio, self.tempo))
            self.tempo = 0.0
            self.in_esecuzione = False
            self.reset_flag = True
            self.asse_x = []
            self.asse_y = []

    def tick(self, delta=0.1):
        """Da chiamare periodicamente dal thread del cronometro."""
        with self._lock:
            if self.in_esecuzione:
                self.tempo += delta

    def aggiungi_punto(self, valore_y):
        with self._lock:
            if self.in_esecuzione:
                self.asse_x.append(self.tempo)
                self.asse_y.append(valore_y)

    def imposta_paracadute_aperto(self):
        with self._lock:
            self.stato_paracadute = True

    # ------------------------------------------------------------------
    # Snapshot per i callback (evita di esporre il lock all'esterno)
    # ------------------------------------------------------------------
    def snapshot_storico(self):
        with self._lock:
            return list(self.storico_grafici), list(self.storico_tempi)

    def snapshot_corrente(self):
        with self._lock:
            return list(self.asse_x), list(self.asse_y)


def avvia_thread_cronometro(state: FlightState, intervallo=0.1):
    """Avvia in background il thread che incrementa il cronometro."""

    def loop():
        while True:
            time.sleep(intervallo)
            state.tick(intervallo)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t

