# Documentazione Ground Station — `ground-station/src/`

## Panoramica

La ground station è la **dashboard di telemetria** del progetto Space AL. Gira su un Raspberry Pi (o qualsiasi PC) e visualizza in tempo reale i dati trasmessi dal razzo: altitudine, pitch, roll e stato del paracadute.

È costruita con **Python/Dash** (Plotly) e supporta due sorgenti di dati intercambiabili:
- **radio** — nRF24L01 collegato via SPI al Raspberry Pi (produzione)
- **serial** — Arduino ricevitore collegato via USB (sviluppo/test)

---

## Struttura dei file

```
ground-station/src/
├── app.py           # Punto di ingresso; layout Dash e tutti i callback
├── config.py        # Tutti i parametri configurabili (pin, porta, intervalli)
├── gpio_compat.py   # Wrapper GPIO: reale su RPi, mock su PC
├── radio_reader.py  # Acquisizione dati via nRF24L01 (pyRF24)
├── serial_reader.py # Acquisizione dati via porta seriale (pyserial)
└── state.py         # Stato condiviso thread-safe (cronometro + storico)
```

---

## Dipendenze Python

```
dash
plotly
pyserial          # per SerialReader
pyrf24            # solo su Raspberry Pi, per RadioReader
RPi.GPIO          # solo su Raspberry Pi
```

Installa con:

```bash
pip install dash plotly pyserial
# Solo su Raspberry Pi:
pip install pyrf24 RPi.GPIO
```

---

## Avvio

```bash
python ground-station/src/app.py
```

La dashboard si apre su `http://127.0.0.1:8050/`.

### Selezionare la sorgente dati

Tramite variabile d'ambiente (non toccare il codice):

```bash
# Modalita' seriale (default)
SPACEAL_INPUT_MODE=serial python ground-station/src/app.py

# Modalita' radio (solo Raspberry Pi)
SPACEAL_INPUT_MODE=radio python ground-station/src/app.py
```

---

## File per file

---

### `config.py` — Configurazione centralizzata

Tutti i parametri modificabili sono variabili di modulo, con un valore di default e un override tramite variabile d'ambiente. Nessun "numero magico" nel codice.

#### Modalità input

```python
MODALITA_INPUT = os.getenv("SPACEAL_INPUT_MODE", "serial")  # "serial" | "radio"
```

#### Pin GPIO (Raspberry Pi, BCM)

| Variabile | Default | Funzione |
|---|---|---|
| `PIN_AVVIA` | 2 | Pulsante Avvia cronometro |
| `PIN_PAUSA` | 3 | Pulsante Pausa |
| `PIN_RESET` | 4 | Pulsante Reset (archivia lancio) |
| `PIN_REFRESH` | 5 | Pulsante Refresh dashboard |

In modalità `serial` su PC questi pin non sono mai fisicamente letti (il mock GPIO restituisce sempre HIGH).

#### Configurazione radio nRF24L01

| Variabile | Default | Nota |
|---|---|---|
| `RADIO_CE_PIN` | 22 | BCM GPIO22 |
| `RADIO_CSN_PIN` | 0 | SPI CE0 = GPIO8 |
| `RADIO_CHANNEL` | 76 | Deve corrispondere al firmware |
| `RADIO_PAYLOAD_SIZE` | 32 | Byte per pacchetto |
| `RADIO_PIPE_ADDRESS` | `"00001"` | Indirizzo pipe in ricezione |

> **Attenzione**: il firmware usa canale 100 e indirizzo `"ABCDE"`. Se usi `RadioReader` devi allineare `RADIO_CHANNEL=100` e `RADIO_PIPE_ADDRESS=ABCDE`.

#### Porta seriale

| Variabile | Default | Nota |
|---|---|---|
| `SERIAL_PORT` | `COM3` | Su Linux: `/dev/ttyUSB0` o simile |
| `SERIAL_BAUDRATE` | 9600 | Deve corrispondere al firmware |
| `SERIAL_TIMEOUT` | 5.0 s | Timeout lettura riga |

#### Intervalli UI (millisecondi)

| Variabile | Default | Scopo |
|---|---|---|
| `INTERVALLO_LETTURA_MS` | 1000 | Poll sorgente dati |
| `INTERVALLO_GRAFICO_MS` | 2000 | Aggiornamento grafico in volo |
| `INTERVALLO_TIMER_MS` | 200 | Aggiornamento display cronometro |

---

### `gpio_compat.py` — Astrazione GPIO multipiattaforma

Restituisce il modulo `RPi.GPIO` reale su Linux (se disponibile) o un `SimpleNamespace` mock con la stessa interfaccia:

```python
GPIO = get_gpio()
GPIO.setmode(GPIO.BCM)          # no-op su PC
GPIO.setup(pin, GPIO.IN)        # no-op su PC
GPIO.input(pin)                 # ritorna sempre 1 (HIGH) su PC
```

Questo permette di sviluppare e testare l'intera app su Windows/macOS senza Raspberry Pi, con i pulsanti fisici semplicemente ignorati e l'interazione che avviene solo via UI.

---

### `state.py` — Stato globale thread-safe

#### Classe `FlightState`

Gestisce lo stato condiviso tra il thread del cronometro e i callback Dash. Tutti i metodi pubblici acquisiscono un `threading.Lock` internamente.

| Attributo | Tipo | Descrizione |
|---|---|---|
| `tempo` | `float` | Secondi trascorsi nel volo corrente |
| `in_esecuzione` | `bool` | True se il cronometro sta girando |
| `reset_flag` | `bool` | True nell'intervallo subito dopo un Reset |
| `stato_paracadute` | `bool` | True se il paracadute è stato aperto |
| `asse_x` | `list[float]` | Timestamp campioni volo corrente |
| `asse_y` | `list[float]` | Altitudine campioni volo corrente |
| `storico_grafici` | `list[tuple]` | (asse_x, asse_y) di ogni lancio archiviato |
| `storico_tempi` | `list[tuple]` | (t_inizio, t_fine) di ogni lancio archiviato |

#### Metodi

| Metodo | Comportamento |
|---|---|
| `avvia()` | Imposta `in_esecuzione = True` |
| `pausa()` | Imposta `in_esecuzione = False` |
| `reset()` | Archivia il volo corrente in `storico_grafici`/`storico_tempi`, azzera tutto |
| `tick(delta)` | Incrementa `tempo` di `delta` se `in_esecuzione` |
| `aggiungi_punto(y)` | Appende un campione alle serie del volo corrente |
| `imposta_paracadute_aperto()` | Imposta `stato_paracadute = True` |
| `snapshot_storico()` | Ritorna copie sicure di `storico_grafici` e `storico_tempi` |
| `snapshot_corrente()` | Ritorna copie sicure di `asse_x` e `asse_y` |

#### `avvia_thread_cronometro(state)`

Lancia un daemon thread che chiama `state.tick(0.1)` ogni 100 ms. Il thread è daemon (muore con il processo principale).

---

### `radio_reader.py` — Acquisizione via nRF24L01

Usa la libreria `pyrf24`. Se la libreria non è disponibile, il `__init__` solleva subito un `RuntimeError` chiaro.

#### Protocollo atteso

Il firmware Space AL trasmette una struct packed da 20 byte. La `RadioReader` attuale legge invece **4 pacchetti separati da 32 byte**, estraendo il primo `int32_t` little-endian da ciascuno:

| Ordine pacchetto | Campo |
|---|---|
| 1 | pitch |
| 2 | roll |
| 3 | altitudine |
| 4 | stato paracadute (0/1) |

> **Nota di compatibilità**: il firmware v4.0 trasmette la struct a 20 byte in un unico `radio.write()`. Se aggiorni `RadioReader` per leggere il firmware v4.0 devi usare un singolo `radio.read(32)` e deserializzare con `struct.unpack("<iiiii", buffer[0:20])`.

#### Metodi

| Metodo | Ritorna |
|---|---|
| `leggi_coordinate()` | `dict {"x", "y", "alt", "paracadute_aperto"}` oppure `None` se la radio non ha dati |
| `_leggi_intero(timeout)` | `int` — legge un pacchetto e ne estrae i primi 4 byte |

---

### `serial_reader.py` — Acquisizione via porta seriale

Legge righe ASCII dalla seriale. Il formato atteso è:

```
Alt = 145.2; X = 3.0; Y = -1.0; Pr0
```

I campi sono separati da `;`. L'ordine non è vincolato; i campi assenti mantengono il valore di default (0 / False).

| Token | Campo decodificato |
|---|---|
| `Alt = <float>` | altitudine (floor a 0) |
| `X = <float>` | roll |
| `Y = <float>` | pitch |
| `Pr1` | paracadute aperto |
| `Pr0` o assente | paracadute chiuso |

#### Metodi

| Metodo | Comportamento |
|---|---|
| `leggi_coordinate()` | Legge una riga, fa parsing, ritorna dict |
| `_estrai_valore(campo)` | Statico — estrae il float dopo `=` |
| `chiudi()` | Chiude la porta seriale |

---

### `app.py` — Applicazione Dash

#### Inizializzazione

All'avvio vengono eseguiti in sequenza:
1. Configurazione GPIO (mock o reale tramite `gpio_compat`)
2. Istanziazione del reader corretto (`RadioReader` o `SerialReader`) in base a `config.MODALITA_INPUT`
3. Creazione di `FlightState` e avvio del thread cronometro
4. Definizione del layout Dash
5. Registrazione dei callback

#### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Grafico altitudine (50% larghezza)   │  spazio libero  │
├─────────────────────────────────────────────────────────┤
│              Barra titolo "SPACE AL"                    │
├─────────────────────────────────────────────────────────┤
│         Cronometro  [Avvia] [Pausa] [Reset] [Refresh]   │
│                    [icona paracadute]                   │
└─────────────────────────────────────────────────────────┘
```

L'icona del paracadute (in basso a sinistra) cambia il `box-shadow` da rosso a verde lime quando il paracadute è aperto.

#### Callback

| ID callback | Trigger | Output | Funzione |
|---|---|---|---|
| `leggi_dati` | `interval-component` (1 s) | stile icona + store coordinate | Legge dal reader, aggiorna stato paracadute |
| `aggiorna_display` | `intervallo-timer` (200 ms) | testo cronometro | Mostra `state.tempo` formattato |
| `gestisci_pulsanti` | click Avvia/Pausa/Reset/Refresh | enable/disable interval, reset flag, checklist | Controlla anche i GPIO fisici |
| `aggiorna_grafico` | store coordinate + `intervallo-grafico` | figura Plotly | Traccia altitudine in tempo reale e storico |

#### Storico lanci

Premendo **Reset**, il volo corrente viene archiviato in `state.storico_grafici`. Nella `checklist-grafici` appaiono le voci "Lancio N (X.Xs)"; selezionando più lanci si sovrappongono i grafici per confronto.

---

## Architettura complessiva

```
         ┌───────────────────────────────────┐
         │           app.py                  │
         │  Dash layout + 4 callback         │
         │                                   │
         │   ┌──────────┐  ┌─────────────┐  │
         │   │FlightState│  │ config.py   │  │
         │   │(state.py) │  │ (parametri) │  │
         │   └──────────┘  └─────────────┘  │
         │        ▲                          │
         │        │ leggi_coordinate()        │
         │   ┌────┴────────────────────┐     │
         │   │  RadioReader            │     │
         │   │  oppure                 │     │
         │   │  SerialReader           │     │
         │   └────────────────────────┘     │
         └───────────────────────────────────┘
                   │                │
            nRF24L01          Arduino USB
           (Raspberry Pi)     (qualsiasi PC)
```

---

## Variabili d'ambiente — riepilogo completo

| Variabile | Default | Descrizione |
|---|---|---|
| `SPACEAL_INPUT_MODE` | `serial` | `"serial"` o `"radio"` |
| `SPACEAL_PIN_AVVIA` | `2` | GPIO BCM pulsante Avvia |
| `SPACEAL_PIN_PAUSA` | `3` | GPIO BCM pulsante Pausa |
| `SPACEAL_PIN_RESET` | `4` | GPIO BCM pulsante Reset |
| `SPACEAL_PIN_REFRESH` | `5` | GPIO BCM pulsante Refresh |
| `SPACEAL_RADIO_CE_PIN` | `22` | GPIO BCM CE radio |
| `SPACEAL_RADIO_CSN_PIN` | `0` | SPI CE0 |
| `SPACEAL_RADIO_CHANNEL` | `76` | Canale RF |
| `SPACEAL_RADIO_PAYLOAD_SIZE` | `32` | Byte payload |
| `SPACEAL_RADIO_ADDRESS` | `00001` | Indirizzo pipe |
| `SPACEAL_SERIAL_PORT` | `COM3` | Porta seriale |
| `SPACEAL_SERIAL_BAUDRATE` | `9600` | Baud rate |
| `SPACEAL_SERIAL_TIMEOUT` | `5.0` | Timeout lettura (s) |
| `SPACEAL_INTERVAL_READ_MS` | `1000` | Intervallo poll dati |
| `SPACEAL_INTERVAL_GRAPH_MS` | `2000` | Intervallo grafico |
| `SPACEAL_INTERVAL_TIMER_MS` | `200` | Intervallo timer |
| `SPACEAL_PARACHUTE_IMG_URL` | (URL esterno) | URL icona paracadute |
| `SPACEAL_STL_PATH` | `""` | Percorso modello 3D (futuro) |
