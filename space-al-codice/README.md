# Space AL — codice del razzo e del computer di terra

**Space AL** è un razzo ad acqua autonomo progettato e costruito da Andrea Podo:
stabilizzazione attiva con servomotori, telemetria radio a 250 kbps, paracadute
automatico e una stazione di terra con dashboard in tempo reale.

🌐 **Sito del progetto: [spaceal.it](https://spaceal.it)**: struttura del razzo, modelli 3D,
firmware, telemetria e storia completa delle versioni.

Questo repository raccoglie **l'ultima versione** del codice dei due sistemi:

| Cartella | Cosa contiene | Versione |
|---|---|---|
| [`arduino/`](arduino/) | firmware di volo del razzo (Arduino Nano) | **v1.3** · 21/06/2026 |
| [`computer-di-terra/`](computer-di-terra/) | dashboard Python della stazione di terra (Raspberry Pi o PC) | **py-v1.0** · 21/06/2026 |

Ogni cartella ha il suo README con i dettagli (collegamenti, librerie, avvio) e il
`CHANGELOG.html` con la cronologia completa delle versioni.

---

## Come funziona il sistema

```
        RAZZO (Arduino Nano)                         STAZIONE DI TERRA
 ┌─────────────────────────────────┐          ┌──────────────────────────────┐
 │ MPU6050  → pitch, roll, accel.  │          │ Raspberry Pi / PC            │
 │ BMP180   → altitudine           │  radio   │  nRF24L01  (modalità radio)  │
 │ 2 servo  → stabilizzazione      │ ───────► │     oppure                   │
 │ 1 servo  → paracadute           │  2.4 GHz │  cavo USB  (modalità seriale)│
 │ nRF24L01 → telemetria ogni 100ms│          │  → dashboard web (Dash)      │
 └─────────────────────────────────┘          └──────────────────────────────┘
```

1. **In rampa** l'Arduino legge i sensori e trasmette continuamente pitch, roll,
   altitudine, stato del paracadute e accelerazione.
2. **Al lancio**, quando l'accelerazione supera la soglia, si attiva la
   stabilizzazione: i servo X/Y correggono l'assetto in base a pitch e roll.
3. **In caduta** (brusco calo dell'accelerazione) il firmware apre il paracadute
   e lo segnala a terra.
4. **A terra** la dashboard mostra il grafico in tempo reale, lo stato del
   paracadute (icona verde/rossa), un cronometro di volo e lo storico dei lanci.

## Struttura del repository

```
space-al-codice/
├── README.md                  ← questo file
├── arduino/
│   ├── README.md              ← firmware: hardware, pin, librerie, caricamento
│   ├── CHANGELOG.html         ← storia del firmware v0.0 → v1.3
│   └── razzo/
│       └── razzo.ino          ← firmware di volo v1.3
└── computer-di-terra/
    ├── README.md              ← dashboard: installazione, configurazione, avvio
    ├── CHANGELOG.html         ← storia del software py-v0.0 → py-v1.0
    ├── requirements.txt       ← dipendenze Python
    └── src/
        ├── app.py             ← dashboard (punto di ingresso)
        ├── config.py          ← tutte le impostazioni
        ├── state.py           ← cronometro e storico lanci
        ├── radio_reader.py    ← ricezione via nRF24L01 (Raspberry Pi)
        ├── serial_reader.py   ← ricezione via USB
        └── gpio_compat.py     ← pulsanti fisici / mock per PC
```

## Avvio rapido

**Razzo:** apri `arduino/razzo/razzo.ino` con l'Arduino IDE, installa le librerie
indicate in [`arduino/README.md`](arduino/README.md) e carica lo sketch sull'Arduino Nano.

**Stazione di terra:**

```bash
cd computer-di-terra
pip install -r requirements.txt
python src/app.py
```

Poi apri il browser su `http://127.0.0.1:8050`.

## ⚠️ Stato attuale: compatibilità tra le due versioni

I codici sono pubblicati **così come sono**, senza modifiche. Nelle versioni attuali
il formato dei dati inviato dal razzo **non corrisponde** a quello che si aspetta
il computer di terra:

| | Firmware Arduino v1.3 trasmette | Computer di terra py-v1.0 si aspetta |
|---|---|---|
| Radio: canale | 100 | 76 |
| Radio: indirizzo | `"ABCDE"` | `"00001"` |
| Radio: velocità | 250 kbps | 1 Mbps |
| Radio: pacchetto | 1 struct da 20 byte (pitch, roll, alt, paracadute, amp) | 4 pacchetti da 32 byte (pitch, roll, alt, paracadute) |
| Seriale USB | `PITCH=… ROLL=… AMP=… PARA=… ALT=…cm TX=OK` | `Alt = …; X = …; Y = …; Pr1` |

Per far dialogare i due sistemi va allineato uno dei due lati. I dettagli sono nei
README delle cartelle e nella sezione Telemetria di [spaceal.it](https://spaceal.it).

## Autore

**Andrea Podo** · [spaceal.it](https://spaceal.it) · [GitHub](https://github.com/podoandrea)
