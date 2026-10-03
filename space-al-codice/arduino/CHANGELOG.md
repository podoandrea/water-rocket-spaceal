# 🚀 Water Rocket Space AL · Arduino

> Cronologia del firmware del razzo. Codice attuale: [razzo/razzo.ino](razzo/razzo.ino) · progetto: [spaceal.it](https://spaceal.it)

Cronologia completa delle versioni del firmware — dalla v0.0 alla v1.3

## Changelog · 12 versioni

### v0.0 — Primo altimetro con apertura paracadute

Punto di partenza del progetto. Codice minimalista che legge l'altitudine tramite BMP085 e apre il paracadute quando il razzo inizia a scendere.

**Novità**

- Lettura altitudine con sensore barometrico BMP085
- Media su 3 letture consecutive per ridurre il rumore
- 1 servomotore per apertura paracadute (pin 8)
- Rilevamento apice: il servo si attiva quando l'altitudine scende sotto il massimo

**Problemi rilevati**

- Pressione al livello del mare hardcoded a 101325 Pa — valore non calibrato per il sito di lancio
- Media calcolata dividendo int per int: troncamento errori di arrotondamento
- Nessun debounce: piccole oscillazioni barometriche possono aprire il paracadute prematuramente
- Condizione apertura: `mediaAltezza - mediaPrecedente + 1 < 0` — il +1 è arbitrario

**Hardware**

- Arduino + BMP085 (I2C) + 1x Servo

Tag: `Adafruit_BMP085` · `Servo.h` · `BMP085` · `1x Servo`

---

### v0.1 — Media letture con funzione dedicata

Miglioramento della precisione altimetrica con una funzione separata per il calcolo della media e una pressione di riferimento ricalibrata.

**Novità**

- Funzione `compute_mean()` separata e riutilizzabile
- Media portata a 4 letture (era 3)
- SEA_LEVEL_PRESSURE aggiornato a 101220 Pa (calibrazione locale)
- Array dedicato `altezze[]` per raccolta campioni

**Risolti**

- Calcolo media ora usa `float` internamente per evitare troncamento

**Problemi rimanenti**

- Condizione apertura paracadute ancora con il +1 arbitrario
- Nessuna protezione contro riapertura multipla del paracadute

Tag: `Adafruit_BMP085` · `BMP085` · `1x Servo`

---

### v0.2 — Stabilizzatori con MPU6050 e 4 servomotori

Prima implementazione del sistema di stabilizzazione attiva. Abbandono temporaneo dell'altimetro per sviluppare il controllo d'assetto.

**Novità**

- Giroscopio/accelerometro MPU6050 per rilevamento assetto
- 4 servomotori per controllo su assi X e Y (thrust vector)
- LED verde e rosso per stato visivo
- Buzzer su pin 5
- Calibrazione automatica offset giroscopio all'avvio (`calcGyroOffsets()`)
- Funzione `getAccelleration()` per rilevare se il razzo è in volo

**Problemi rilevati**

- Bug critico: `if (mpu6050.getAngleX() == -1 < 0 < 1)` — confronto a catena non valido in C++, sempre vero
- Logica stabilizzatore aggiornata ogni 1000ms: troppo lento per correggere in volo
- Conflitto pin: `ledping = 7` e `servopin4 = 7` sullo stesso pin
- Libreria cambiata (MPU6050_tockn) — incompatibile con versioni precedenti

Tag: `MPU6050_tockn` · `Servo.h` · `MPU6050` · `4x Servo` · `LED + Buzzer`

---

### v0.3 — Rilevamento caduta libera via interrupt hardware

Approccio alternativo all'apertura paracadute: uso dell'interrupt hardware di caduta libera dell'MPU6050 anziché il barometro.

**Novità**

- Interrupt hardware su pin 2 (`attachInterrupt(0, doInt, RISING)`)
- Configurazione soglie caduta libera: threshold 17, duration 2ms
- Filtro DHPF a 5Hz per sopprimere vibrazioni motore
- Risposta immediata grazie all'interrupt (non dipende dal loop)

**Problemi rilevati**

- Libreria MPU6050 diversa dalla v0.2 (incompatibile con MPU6050_tockn)
- Soglia 17 hardcoded — sensibile a vibrazioni in volo, potenziali falsi positivi
- Dopo apertura paracadute, servo torna a 90° dopo 5 secondi fissi — non verifica lo stato reale
- flag `freefallDetected` non protetto da race condition

Tag: `MPU6050 (elektronikit)` · `Servo.h` · `MPU6050` · `1x Servo (paracadute)`

---

### v0.4 — Fusione stabilizzatori + caduta libera (5 servo)

Prima versione che unisce i due sistemi principali: stabilizzatori attivi durante il volo e apertura automatica paracadute in caduta.

**Novità**

- 5 servomotori: 4 stabilizzatori (pin 7-10) + 1 paracadute (pin 6)
- Soglia caduta libera alzata a 100 per ridurre falsi positivi
- Calibrazione giroscopio all'avvio (`calibrateGyro()`)
- Flag `paracadute` per bloccare gli stabilizzatori durante l'apertura
- In apertura paracadute: tutti e 4 i servo si portano a 180° (massima deflessione)

**Problemi rimanenti**

- Bug condizione a catena `== -1 < 0 < 1` ancora presente nella funzione stabilizer()
- Stabilizzatore aggiornato ogni 1000ms — ancora troppo lento
- Libreria cambiate di nuovo (MPU6050 elektronikit, non tockn)

Tag: `MPU6050 (elektronikit)` · `Servo.h` · `MPU6050` · `5x Servo`

---

### v0.5 — Altimetro + logging su scheda SD

Introduzione della scheda SD per il logging dei dati di volo. Permette l'analisi post-lancio dell'altitudine e degli eventi.

**Novità**

- Scheda SD su pin 4 per registrazione dati
- File `servo.txt` con log continuo di altitudine e eventi
- Contatore `paracadute` per tracciare numero aperture
- File chiuso automaticamente al primo evento paracadute

**Problemi rilevati**

- File aperto con `O_WRITE`: sovrascrive i dati esistenti senza append
- Il file non viene mai flushato durante il volo — dati persi se alimentazione cade
- Condizione apertura paracadute ancora con +1 arbitrario e nessun debounce
- Sensore BMP e SD non inizializzati con controllo errori separato

Tag: `Adafruit_BMP085` · `SD.h + SPI.h` · `BMP085` · `SD card (pin 4)` · `1x Servo`

---

### v0.6 — Tentativo fusione altimetro + SD + stabilizzatori

Primo tentativo di integrare tutti i sistemi in un unico codice. Versione transitoria con componenti parzialmente commentati.

**Novità**

- Struttura unificata con MPU6050_tockn + BMP085 + SD in un solo sketch
- 4 servo stabilizzatori con angoli calcolati da MPU6050
- Serial output degli angoli X/Y ogni secondo

**Problemi rilevati**

- BMP085 e SD card commentati — non funzionali in questa versione
- Conflitto: `myServo.attach(8)` e `servopin2 = 8` sullo stesso pin
- Bug catena confronto `== -1 < 0 < 1` ancora presente
- File SD non aperto — scritture su oggetto non inizializzato (comportamento indefinito)

Tag: `MPU6050_tockn` · `Adafruit_BMP085 (commentato)` · `SD.h (commentato)` · `MPU6050` · `4x Servo`

---

### v0.7 — Prima versione completa — tutti i sistemi integrati 🏁

Pietra miliare del progetto: tutti i sistemi presenti e attivi in un unico firmware. Richiede tutte le librerie e 5 servomotori.

**Novità**

- Tutti i sistemi attivi: caduta libera + stabilizzatori + SD + altimetro
- Cambio libreria stabilizzatori a MPU6050 elektronikit (per interrupt caduta libera)
- 5 servo operativi: 4 stabilizzatori + 1 paracadute
- Logging altitudine su SD con BMP085

**Problemi rilevati**

- Bug critico: `file.close()` chiamato ad ogni ciclo del loop — il file viene chiuso e non si può più scrivere
- Bug: SD aperta prima di `SD.begin()` — la SD non è mai inizializzata
- Bug catena confronto ancora presente in `stabilizer()`
- Latenza stabilizzatori ancora 1000ms — troppo lenta per correzioni in volo

Tag: `MPU6050` · `Adafruit_BMP085` · `SD.h` · `MPU6050 + BMP085` · `5x Servo + SD card`

---

### v1.0 — Refactoring completo — telemetria radio NRF24L01 ⭐

Riscrittura completa dell'architettura. Abbandono delle librerie MPU per lettura I2C raw, introduzione della radio NRF24L01 per telemetria bidirezionale in tempo reale.

**Novità**

- Lettura MPU-6050 diretta via I2C raw (registri 0x3B–0x48) — nessuna libreria dedicata
- Calcolo Pitch e Roll con `atan2()` — preciso su tutti i quadranti
- Radio NRF24L01 (pin 7/8) per trasmissione telemetria a terra
- 6 servo: 4 thrust vector (pin 2-5) + paracadute (pin 7) + gambe (pin 9)
- Rilevamento apice via decadimento vettore accelerazione (`Amp`)
- Offsets MPU calibrati manualmente: AcX-2050, AcY-77, AcZ-1947

**Problemi rilevati**

- Indirizzo radio "00001" — canale non impostato, interferenze probabili
- Servo paracadute su pin 7 e radio CE su pin 7 — conflitto pin
- Offset MPU hardcoded — non validi su altri sensori
- BMP085 commentato — altitudine non trasmessa
- Delay fisso 500ms + verifica dell'ampiezza: finestra cieca durante caduta

Tag: `RF24.h` · `nRF24L01.h` · `Servo.h` · `MPU6050 (raw I2C)` · `NRF24L01` · `6x Servo`

---

### v1.1 — Struttura SensorData e flag trustVector

Ottimizzazione della trasmissione radio e introduzione del flag trustVector per abilitare gli stabilizzatori solo durante il volo effettivo.

**Novità**

- Struct `SensorData` per impacchettare Pitch, Roll, altitudine, paracadute, Amp
- Radio ottimizzata: canale 100, `RF24_250KBPS`, `RF24_PA_MIN`
- Indirizzo radio cambiato a "ABCDE" (5 char ASCII validi)
- Flag `trustVector`: stabilizzatori attivi solo quando Amp > 10 (in volo)
- Reset trustVector e memoria dopo apertura paracadute
- Conferma TX: stampa "OK" o "FAIL" sul Serial

**Risolti**

- Conflitto pin radio/servo risolto: radio su pin 9/10, servo su pin separati
- Stabilizzatori non si attivano durante la preparazione al lancio

**Problemi rimanenti**

- Struct non packed — possibile disallineamento byte con ricevitore Python
- Altitudine non ancora integrata (campo presente ma vale 0)
- Nome file indica "aggiungere altimetro" — funzione mancante riconosciuta

Tag: `RF24.h` · `MPU6050 (raw I2C)` · `NRF24L01 (canale 100)` · `3x Servo attivi`

---

### v1.2 — Struct packed e compatibilità Arduino/Python
*18 aprile 2026*

Fix della serializzazione della struttura dati per garantire compatibilità tra il firmware Arduino e il software Python di telemetria a terra.

**Novità**

- `__attribute__((packed))` sulla struct per allineamento byte garantito
- Tutti i campi della struct convertiti in `int32_t` (4 byte ciascuno)
- Debug dimensione struct in `setup()`: deve stampare esattamente 20
- Inizializzazione esplicita di altitudine, paracadute e Amp a 0
- Serial output unificato su una riga con tutti i valori

**Risolti**

- Disallineamento byte struct tra Arduino e Python — dati corrotti sul ricevitore
- Pulizia codice: rimossi commenti obsoleti e variabili inutilizzate

**Problemi rimanenti**

- Altitudine nel pacchetto sempre 0 — sensore BMP non ancora collegato

Tag: `RF24.h` · `MPU6050 (raw I2C)` · `NRF24L01` · `3x Servo`

---

### v1.3 — Integrazione altimetro BMP180 — altitudine reale in telemetria 🏁
*21 aprile 2026*

Versione attuale e più avanzata. Finalmente l'altitudine reale è integrata nel pacchetto radio. Il razzo trasmette a terra in tempo reale: pitch, roll, accelerazione, stato paracadute e quota relativa in centimetri.

**Novità**

- Sensore BMP180 inizializzato in `setup()` con verifica errore
- Calibrazione quota zero al momento dell'accensione (`altitudineDiRiferimento`)
- Altitudine relativa calcolata in cm: `(assoluta - riferimento) × 100`
- Altitudine trasmessa via radio nel campo `data.altitudine` (int32_t)
- Serial output: `ALT=XXXcm` aggiunto alla riga di debug

**Risolti**

- Campo altitudine nel pacchetto radio finalmente valorizzato con dati reali
- Offset rispetto alla quota di accensione elimina le variazioni barometriche assolute

**Problemi noti / sviluppi futuri**

- Offset MPU ancora hardcoded — richiede ricalibrazione per ogni singolo sensore
- Nessuna registrazione SD dei dati di volo (rimossa dal v0.7)
- trustVector soglia fissa Amp > 10 — da calibrare con dati reali di lancio
- Delay 500ms durante rilevamento caduta — finestra cieca ancora presente

Tag: `RF24.h` · `Adafruit_BMP085` · `MPU6050 + BMP180` · `NRF24L01` · `3x Servo`

---

Water Rocket Space AL — Progetto Arduino  
14 versioni · v0.0 → v1.3 | github.com/podoandrea/water-rocket-arduino
