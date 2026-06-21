"""
serial_reader.py
-----------------
Acquisizione dati telemetrici via porta seriale, per setup basati su
Arduino o altro microcontrollore collegato via USB.

Formato riga atteso (testo ASCII, separato da ';'):
    Alt = <float>; X = <float>; Y = <float>; Pr1
oppure varianti che includano solo alcuni campi. "Pr1" indica
paracadute aperto, "Pr0" (o l'assenza del campo) paracadute chiuso.
"""

import serial


class SerialReader:
    def __init__(self, port, baudrate, timeout):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def leggi_coordinate(self):
        """
        Legge e fa il parsing di una riga dalla seriale.

        Ritorna un dizionario {"x", "y", "alt", "paracadute_aperto"}.
        I campi assenti nella riga letta mantengono il valore di default
        (0 per le coordinate, False per il paracadute).
        """
        riga = self.ser.readline().decode(errors="ignore").strip()
        coordinate = {"x": 0.0, "y": 0.0, "alt": 0.0, "paracadute_aperto": False}

        if not riga:
            return coordinate

        campi = riga.split(";")

        for campo in campi:
            campo = campo.strip()
            if campo.startswith("Alt"):
                coordinate["alt"] = max(0.0, self._estrai_valore(campo))
            elif campo.startswith("X"):
                coordinate["x"] = self._estrai_valore(campo)
            elif campo.startswith("Y"):
                coordinate["y"] = self._estrai_valore(campo)
            elif campo.startswith("Pr"):
                coordinate["paracadute_aperto"] = campo.strip() == "Pr1"

        return coordinate

    @staticmethod
    def _estrai_valore(campo):
        try:
            return float(campo.split("=")[1].strip())
        except (IndexError, ValueError):
            return 0.0

    def chiudi(self):
        if self.ser.is_open:
            self.ser.close()

