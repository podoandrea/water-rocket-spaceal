# 🐍 Water Rocket Space AL · Python

> Cronologia del software della stazione di terra. Codice attuale: [src/](src/) · progetto: [spaceal.it](https://spaceal.it)

Cronologia completa del software di terra — dalla py-v0.0 alla py-v1.0

## Changelog · 6 versioni

### py-v0.0 — Primo test ricezione radio — output terminale

Script minimalista per verificare che la radio NRF24L01 riceva correttamente i dati trasmessi dall'Arduino del razzo. Nessuna interfaccia grafica.

**Novità**

- Inizializzazione radio NRF24L01 via pyrf24 (CE=GPIO22, CSN=CE0)
- Protocollo a 4 pacchetti da 32 byte: pitch, roll, altitudine, paracadute
- Decodifica little-endian a 4 byte per ogni valore (`struct.unpack('<i', ...)`)
- Canale 76, payload 32 byte, 1 Mbps
- Output continuo su terminale

**Problemi rilevati**

- Canale 76 — non corrisponde al canale 100 usato dal firmware Arduino v1.1+
- Indirizzo pipe "00001" — non corrisponde a "ABCDE" usato dall'Arduino v1.1+
- Attesa pacchetti successivi con busy-wait (`while not radio.available()`) — blocca il processo
- Nessuna gestione timeout: se un pacchetto non arriva il loop si blocca indefinitamente

Tag: `pyrf24` · `struct` · `NRF24L01 (GPIO22/CE0)` · `Radio`

---

### py-v0.1 — Prima dashboard Dash con grafico e pulsanti GPIO

Primo tentativo di interfaccia grafica completa: dashboard web Dash con grafico altitudine in tempo reale, cronometro di volo e controllo tramite pulsanti fisici GPIO su Raspberry Pi.

**Novità**

- Dashboard web Plotly Dash accessibile da browser
- Grafico altitudine dinamico in tempo reale
- Cronometro di volo con thread background dedicato
- Pulsanti fisici GPIO: avvia (pin 2), pausa (pin 3), reset (pin 4), refresh (pin 5)
- Storico lanci: salva i dati di ogni lancio e li rende selezionabili
- Indicatore paracadute: immagine con glow verde (aperto) / rosso (chiuso)
- Tema scuro con sfondo #111111

**Problemi rilevati**

- Canale radio ancora 76 e pipe "00001" — disallineato con Arduino v1.1+
- Lettura radio nel callback Dash: blocca il thread UI durante l'attesa dei 4 pacchetti
- Busy-wait tra i pacchetti radio dentro il callback — può causare timeout Dash
- Stato paracadute globale non protetto da lock — race condition con thread cronometro
- Il grafico mostra solo l'asse Y (pitch) come altitudine — dato non corretto
- Intervallo refresh GPIO ogni 1000ms — ritardo di risposta ai pulsanti fisici

Tag: `Dash + Plotly` · `pyrf24` · `RPi.GPIO` · `Browser (Dash)` · `GPIO pulsanti fisici` · `Radio`

---

### py-v0.2 — Dashboard Dash con visualizzatore 3D STL e input seriale

Aggiunto visualizzatore 3D interattivo del modello STL del razzo che ruota in tempo reale con i dati di assetto. Cambio sorgente dati da radio a seriale USB.

**Novità**

- Visualizzatore 3D STL del razzo con dash-vtk + VTK
- Rotazione del modello 3D in tempo reale con angoli pitch/roll ricevuti
- Cambio sorgente dati: porta seriale COM6 a 9600 baud
- Parsing stringa seriale con formato: `Alt = X ; X = Y ; Y = Z`
- Pulsanti software nel browser (non più GPIO fisici)
- Storico lanci con checklist di selezione nel grafico

**Risolti**

- Rimosso busy-wait radio: lettura seriale sincrona più stabile
- Compatibilità con PC Windows (non richiede Raspberry Pi)

**Problemi rilevati**

- Porta seriale hardcoded a COM6 — non portabile su altri PC
- Oggetto `ser` creato a livello di modulo — errore immediato se COM6 non esiste
- Il modello STL viene riletto e riprocessato con VTK ad ogni callback — molto lento
- Percorso file STL hardcoded a un path specifico del PC
- Stato globale (asse_x, asse_y, storico) non thread-safe
- Il visualizzatore STL scompare se il browser non ha WebGL attivo

Tag: `Dash + Plotly` · `dash-vtk + VTK` · `pyserial` · `Browser (Dash) + 3D STL` · `Seriale COM6`

---

### py-v0.3 — Interfaccia Tkinter nativa con 4 grafici matplotlib

Abbandono di Dash a favore di un'interfaccia nativa Tkinter. Quattro grafici matplotlib separati per altitudine, X, Y, Z. Input via seriale.

**Novità**

- Interfaccia nativa Tkinter fullscreen — nessun browser necessario
- 4 grafici matplotlib in tempo reale: altitudine, X, Y, Z
- Thread separato per lettura seriale — GUI non si blocca durante la lettura
- Finestra scorrevole: mantiene solo gli ultimi 100 punti per grafico
- Parsing per prefissi: `Alt =`, `X =`, `Y =`, `Z =`
- Correzione altitudine: sottra 65m (offset di calibrazione locale)

**Risolti**

- Eliminata dipendenza VTK e dash-vtk — avvio molto più veloce
- Thread lettura seriale separato: GUI sempre reattiva

**Problemi rilevati**

- Porta COM6 ancora hardcoded
- Offset 65m hardcoded — specifico del sito di test, non configurabile
- Aggiornamento grafici ogni secondo (sleep 1s nel thread) — bassa frequenza
- Importazione `renderer` (renderizza_stl) non inclusa nel codice — errore all'avvio
- I 4 grafici condividono lo stesso asse X ma con logiche diverse — disallineamento dati
- Nessun indicatore paracadute e nessun cronometro di volo

Tag: `tkinter` · `matplotlib` · `pyserial` · `Tkinter nativo` · `Seriale COM6`

---

### py-v0.4 — Versione ibrida Tkinter + Plotly + radio pigpio/nrf24

Ritorno alla radio con una nuova libreria (pigpio/nrf24). Interfaccia Tkinter fullscreen con grandi display numerici, affiancata da grafici Plotly aperti nel browser.

**Novità**

- Radio tramite `nrf24` + `pigpio` — libreria alternativa a pyrf24
- Canale corretto a 100 e pipe "ABCDE" — allineato con Arduino v1.1+
- GUI Tkinter fullscreen: PITCH e ROLL come grandi numeri colorati
- Colori dinamici: lime se l'angolo è tra -3° e +3°, rosso altrimenti
- Indicatore paracadute: label "PARACADUTE" cambia colore
- Grafici Plotly con 3 subplot (accelerazione, pitch, roll) aperti nel browser
- Deque circolari da 200 campioni per storico recente
- Thread radio separato: GUI non si blocca
- Struct unpack flessibile: tenta formato `<ii f ?` poi fallback a `<ii`

**Risolti**

- Canale e indirizzo radio allineati con il firmware Arduino
- Thread radio separato: nessun blocco della GUI
- Eliminato busy-wait: `nrf.data_ready()` con sleep 50ms

**Problemi rilevati**

- I grafici Plotly vengono aperti nel browser una sola volta all'avvio — non si aggiornano in tempo reale
- Struct unpack con formato `<ii f ?` (13 byte) non compatibile con struct Arduino packed a 20 byte
- pigpio richiede il demone `pigpiod` avviato manualmente prima dell'esecuzione
- Nessun cronometro di volo, nessuno storico lanci
- L'altitudine non viene mostrata nell'interfaccia grafica

Tag: `tkinter` · `plotly` · `pigpio + nrf24` · `Tkinter + Browser Plotly` · `Radio (canale 100)`

---

### py-v1.0 — Refactoring completo — pacchetto modulare space-al-telemetry ⭐

Riscrittura completa dell'intera applicazione in un pacchetto Python strutturato. Architettura modulare con separazione netta tra UI, stato, configurazione e sorgente dati. Supporto nativo sia radio che seriale.

**Novità**

- **app.py** — entry point pulito, solo layout Dash e callback
- **config.py** — tutti i parametri configurabili in un file (canale, pin, porte, URL)
- **state.py** — classe `FlightState` thread-safe con lock per cronometro e dati volo
- **radio_reader.py** — `RadioReader` con timeout, interfaccia `leggi_coordinate()`
- **serial_reader.py** — `SerialReader` con stessa interfaccia di RadioReader
- **gpio_compat.py** — stub GPIO per eseguire su PC Windows senza Raspberry Pi
- Selezione sorgente dati via `MODALITA_INPUT`: `"radio"` o `"serial"`
- Metodi `snapshot_storico()` e `snapshot_corrente()` per letture sicure senza esporre il lock
- Gestione errori con `TimeoutError` e `OSError` — il programma non crasha se i dati non arrivano
- Indirizzo paracadute corretto tramite `dati.get("paracadute_aperto")` — boolean esplicito

**Risolti**

- Race condition sullo stato globale: tutto protetto da threading.Lock
- Porta seriale e canale radio configurabili senza modificare il codice
- Compatibilità PC: gpio_compat permette sviluppo su Windows senza Raspberry Pi
- Timeout sul reader: il programma non si blocca se i dati non arrivano
- Grafici Plotly Dash aggiornati in tempo reale (non più snapshot statici)
- Storico lanci thread-safe con copia difensiva nelle snapshot

Tag: `Dash + Plotly` · `pyrf24 / pyserial` · `threading` · `Browser (Dash)` · `Radio o Seriale (configurabile)` · `GPIO opzionali`

---

Water Rocket Space AL — Software di Terra Python  
6 versioni · py-v0.0 → py-v1.0 | github.com/podoandrea/water-rocket-python
