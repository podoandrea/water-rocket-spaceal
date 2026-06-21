# Space AL — Razzo ad Acqua Autonomo

**Space AL** è un sistema completo per un razzo ad acqua con avionica attiva: stabilizzazione pitch/roll, altimetro barometrico, telemetria wireless a 250 kbps, apertura automatica del paracadute e dashboard di monitoraggio in tempo reale.

Il progetto è composto da due sottosistemi software indipendenti che comunicano via radio 2.4 GHz (nRF24L01).

---

## Struttura del repository

```
space-al/
├── firmware/
│   └── razzo.ino          # Codice Arduino (computer di bordo)
├── ground-station/
│   └── src/
│       ├── app.py          # Dashboard Dash — punto di ingresso
│       ├── config.py       # Configurazione centralizzata
│       ├── gpio_compat.py  # Astrazione GPIO (RPi / PC)
│       ├── radio_reader.py # Lettura dati via nRF24L01
│       ├── serial_reader.py# Lettura dati via USB seriale
│       └── state.py        # Stato condiviso thread-safe
└── docs/
    ├── firmware.md         # Documentazione dettagliata firmware
    └── ground-station.md   # Documentazione dettagliata Python
```

---

## Firmware (`firmware/razzo.ino`)

Gira su **Arduino Nano** all'interno del razzo.

### Funzionalità

- Lettura assetto 6DOF da **MPU6050** (I²C) ogni 100 ms
- Misura altitudine relativa al suolo da **BMP180** (I²C) in centimetri
- Stabilizzazione attiva pitch/roll con **2 servo SG90** (attivi sopra i ~1 g)
- Rilevamento caduta libera e apertura automatica **paracadute** (servo)
- Trasmissione telemetria via **nRF24L01** a 250 kbps, struct packed 20 byte

### Librerie richieste (Arduino IDE / PlatformIO)

```
Wire, Servo, SPI, RF24, Adafruit BMP085
```

### Struct trasmessa

```cpp
struct __attribute__((packed)) SensorData {
    int32_t Pitch;       // gradi
    int32_t Roll;        // gradi
    int32_t altitudine;  // centimetri relativi al suolo
    int32_t paracadute;  // 0 = chiuso, 1 = aperto
    int32_t Amp;         // modulo accelerazione ×10
};  // = 20 byte esatti
```

> Documentazione completa: [`docs/firmware.md`](docs/firmware.md)

---

## Ground Station (`ground-station/src/`)

Dashboard **Python/Dash** che gira su Raspberry Pi o PC.

### Funzionalità

- Grafico altitudine in tempo reale (Plotly)
- Indicatore visivo stato paracadute (glow verde/rosso)
- Cronometro di volo con Avvia / Pausa / Reset
- Storico lanci con sovrappposizione grafici per confronto
- Doppia sorgente dati: **radio nRF24L01** (produzione) o **seriale USB** (test)
- Pulsanti fisici GPIO su Raspberry Pi + pulsanti UI su PC

### Requisiti Python

```bash
pip install dash plotly pyserial
# Solo su Raspberry Pi:
pip install pyrf24 RPi.GPIO
```

### Avvio rapido

```bash
# Modalita' seriale (default — collegare Arduino via USB)
python ground-station/src/app.py

# Modalita' radio (Raspberry Pi con nRF24L01)
SPACEAL_INPUT_MODE=radio python ground-station/src/app.py
```

La dashboard è accessibile su `http://127.0.0.1:8050/`.

> Documentazione completa: [`docs/ground-station.md`](docs/ground-station.md)

---

## Architettura del sistema

```
┌─────────────────────────────┐        2.4 GHz        ┌──────────────────────────┐
│      RAZZO (Arduino Nano)   │ ─────────────────────► │  GROUND STATION          │
│                             │      nRF24L01           │  (Raspberry Pi / PC)     │
│  MPU6050 → Pitch/Roll       │      250 kbps           │                          │
│  BMP180  → Altitudine       │      20 byte            │  Python/Dash dashboard   │
│  Servo   → Stabilizzatori   │                         │  SerialReader (USB)      │
│  Servo   → Paracadute       │                         │  RadioReader (SPI)       │
└─────────────────────────────┘                         └──────────────────────────┘
```

---

## Versioni

| Versione | Data | Novità principali |
|---|---|---|
| v1.0 | Dicembre 2023 | BMP085, LCD I2C, tastiera 4×4, no stabilizzazione |
| v2.0 | 2024 | Servo stabilizzatori, paracadute automatico, USB seriale |
| v3.0 | 2025 | PCB custom KiCad, telemetria nRF24L01, dashboard Python/Dash |
| v4.0 | Aprile 2026 | Struct packed 20 byte, gambe deployabili, PCB v3.0, dashboard v2 |
| v4.5 | Estate 2026 (pianificato) | GPS Neo-6M, track su OpenStreetMap |
| v5.0 | Autunno 2026 (pianificato) | Controllo PID, camera FPV |
| v6.0 | 2027 (visione) | Atterraggio propulso stile Falcon 9, LIDAR |

---

## Licenza

MIT — © 2026 Andrea Podo
