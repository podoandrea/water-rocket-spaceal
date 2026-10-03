# Computer di terra — py-v1.0

Dashboard di telemetria di **Space AL**: riceve i dati del razzo via radio o via
USB e li mostra in tempo reale nel browser, con grafico, stato del paracadute,
cronometro di volo e storico dei lanci.

🌐 Pagina della stazione di terra e della telemetria: [spaceal.it](https://spaceal.it) ·
cronologia completa in [`CHANGELOG.md`](CHANGELOG.md).

## File

| File | Ruolo |
|---|---|
| [`src/app.py`](src/app.py) | **punto di ingresso**: interfaccia Dash, callback, pulsanti |
| [`src/config.py`](src/config.py) | tutte le impostazioni (sovrascrivibili con variabili d'ambiente) |
| [`src/state.py`](src/state.py) | stato condiviso thread-safe: cronometro, lancio in corso, storico |
| [`src/radio_reader.py`](src/radio_reader.py) | ricezione via nRF24L01 (`pyrf24`, solo Raspberry Pi) |
| [`src/serial_reader.py`](src/serial_reader.py) | ricezione via porta seriale USB (`pyserial`) |
| [`src/gpio_compat.py`](src/gpio_compat.py) | pulsanti fisici su Raspberry Pi; su PC usa un sostituto (pulsanti sempre "non premuti") |

## Installazione

Serve Python 3.8 o superiore.

```bash
pip install -r requirements.txt
```

Su **Raspberry Pi** in modalità radio servono anche (vedi i commenti in
`requirements.txt`):

```bash
pip install pyrf24 RPi.GPIO
```

## Avvio

```bash
python src/app.py
```

Apri il browser su **http://127.0.0.1:8050**.

## Configurazione

Tutto è in `src/config.py`. Ogni valore si può cambiare senza toccare il codice,
con una variabile d'ambiente:

| Variabile | Default | Significato |
|---|---|---|
| `SPACEAL_INPUT_MODE` | `serial` | sorgente dati: `serial` (USB) o `radio` (nRF24L01) |
| `SPACEAL_SERIAL_PORT` | `COM3` | porta seriale (Linux/RPi: es. `/dev/ttyUSB0`) |
| `SPACEAL_SERIAL_BAUDRATE` | `9600` | velocità seriale |
| `SPACEAL_SERIAL_TIMEOUT` | `5` | timeout lettura seriale (s) |
| `SPACEAL_RADIO_CE_PIN` | `22` | pin CE della radio (GPIO) |
| `SPACEAL_RADIO_CSN_PIN` | `0` | CSN della radio (CE0 = GPIO8) |
| `SPACEAL_RADIO_CHANNEL` | `76` | canale radio |
| `SPACEAL_RADIO_PAYLOAD_SIZE` | `32` | dimensione pacchetto (byte) |
| `SPACEAL_RADIO_ADDRESS` | `00001` | indirizzo della pipe radio |
| `SPACEAL_PIN_AVVIA` / `PAUSA` / `RESET` / `REFRESH` | `2` / `3` / `4` / `5` | pulsanti fisici (GPIO BCM) |
| `SPACEAL_INTERVAL_READ_MS` | `1000` | intervallo lettura dati (ms) |
| `SPACEAL_INTERVAL_GRAPH_MS` | `2000` | intervallo aggiornamento grafico (ms) |
| `SPACEAL_INTERVAL_TIMER_MS` | `200` | intervallo aggiornamento cronometro (ms) |
| `SPACEAL_PARACHUTE_IMG_URL` | immagine online | icona del paracadute |

Esempi:

```bash
# Windows (PowerShell), Arduino su COM5
$env:SPACEAL_SERIAL_PORT = "COM5"; python src/app.py

# Raspberry Pi con radio nRF24L01
SPACEAL_INPUT_MODE=radio python src/app.py
```

## Collegamenti su Raspberry Pi (modalità radio)

| nRF24L01 | Raspberry Pi |
|---|---|
| CE | GPIO22 |
| CSN | CE0 (GPIO8) |
| SCK / MOSI / MISO | SPI0 (GPIO11 / GPIO10 / GPIO9) |
| VCC | 3.3 V |

Pulsanti fisici (opzionali, attivi bassi): Avvia = GPIO2, Pausa = GPIO3,
Reset = GPIO4, Refresh = GPIO5. Hanno la precedenza sui pulsanti a schermo.

## Uso della dashboard

- **Avvia**: fa partire il cronometro e la registrazione del lancio.
- **Pausa**: ferma cronometro e grafico.
- **Reset**: archivia il lancio nello storico e azzera tutto. I lanci archiviati
  compaiono nel grafico come "Lancio N (durata)".
- **Refresh**: richiesta di aggiornamento (stampa un messaggio sul terminale).
- L'**icona del paracadute** passa da rossa a verde quando il razzo segnala l'apertura.

## Formato dati atteso

**Radio** (`radio_reader.py`): 4 pacchetti consecutivi da 32 byte, ognuno con un
intero a 4 byte little-endian nei primi 4 byte: pitch, roll, altitudine, paracadute
(0/1). Radio a 1 Mbps, potenza massima.

**Seriale** (`serial_reader.py`): una riga di testo per lettura, campi separati da `;`:

```
Alt = 12.5; X = 3.0; Y = -1.0; Pr1
```

`Pr1` = paracadute aperto, `Pr0` (o campo assente) = chiuso. I campi mancanti valgono 0.

## Note sul codice (py-v1.0, pubblicato senza modifiche)

- Il grafico "Altitudine" disegna il campo `y`, che contiene il **pitch** e non l'altitudine.
- In modalità radio, se un pacchetto non arriva entro 1 s, la lettura solleva un
  `TimeoutError`: la dashboard lo stampa e mostra valori a zero fino al pacchetto successivo.
- I parametri radio e il formato seriale non corrispondono ancora a quelli trasmessi
  dal firmware Arduino v1.3: vedi il [README principale](../README.md), sezione *Stato attuale*.
