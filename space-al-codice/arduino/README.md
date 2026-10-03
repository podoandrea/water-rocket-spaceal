# Firmware del razzo — v1.3

Firmware di volo di **Space AL** per Arduino Nano: legge i sensori, stabilizza il
razzo con i servomotori, apre il paracadute in caduta e trasmette la telemetria a terra.

🌐 Pagina del firmware e storia delle versioni: [spaceal.it](https://spaceal.it) · cronologia
completa in [`CHANGELOG.md`](CHANGELOG.md).

File: [`razzo/razzo.ino`](razzo/razzo.ino) (lo sketch sta nella cartella `razzo/`, come
richiede l'Arduino IDE).

## Hardware e collegamenti

| Componente | Collegamento |
|---|---|
| Arduino Nano | scheda principale |
| MPU6050 (accelerometro + giroscopio) | I2C (A4 = SDA, A5 = SCL), indirizzo `0x68` |
| BMP180 / BMP085 (barometro) | I2C (stesso bus) |
| nRF24L01 (radio 2.4 GHz) | SPI · CE = **D9**, CSN = **D10** |
| Servo X (stabilizzazione roll) | **D8** |
| Servo Y (stabilizzazione pitch) | **D7** |
| Servo paracadute | **D5** |

## Librerie

Da installare con *Strumenti → Gestisci librerie* nell'Arduino IDE:

| Libreria | Uso |
|---|---|
| **RF24** (TMRh20) | radio nRF24L01 |
| **Adafruit BMP085 Library** | barometro BMP180/BMP085 |
| `Wire`, `SPI`, `Servo` | già incluse nell'IDE |

## Come funziona

**Avvio (`setup`)**
- radio in trasmissione: canale **100**, indirizzo **`"ABCDE"`**, **250 kbps**, potenza minima;
- risveglio dell'MPU6050 e lettura dell'altitudine di riferimento (quota zero) dal BMP180;
- servo paracadute in posizione di riposo (135°);
- sul monitor seriale (9600 baud) stampa `BMP180 OK` / `BMP180 ERRORE` e la
  dimensione della struct (deve essere **20**).

**Ciclo (`loop`, ogni ~100 ms)**
1. legge l'MPU6050 e applica gli offset di calibrazione;
2. calcola **roll** e **pitch** (gradi) e l'**accelerazione totale** `Amp` (in decimi di g);
3. calcola l'**altitudine relativa** in centimetri;
4. se la stabilizzazione è attiva, muove i servo X/Y in proporzione a roll e pitch;
5. trasmette via radio il pacchetto di telemetria e stampa i valori sul seriale;
6. attiva la stabilizzazione (`trustVector`) quando `Amp > 10` (oltre ~1 g);
7. **rilevamento caduta**: se l'accelerazione cala bruscamente rispetto al massimo
   registrato, attende 500 ms, ricontrolla e, se confermato, apre il paracadute
   (servo a 180°), invia `paracadute = 1`, poi riporta i servo a 90° e disattiva
   la stabilizzazione.

## Pacchetto di telemetria (radio)

Struct `SensorData`, *packed*, **20 byte**, interi a 32 bit little-endian:

| Byte | Campo | Unità |
|---|---|---|
| 0–3 | `Pitch` | gradi |
| 4–7 | `Roll` | gradi |
| 8–11 | `altitudine` | centimetri (relativa all'accensione) |
| 12–15 | `paracadute` | 0 = chiuso, 1 = apertura in corso |
| 16–19 | `Amp` | accelerazione totale × 10 (g) |

Uscita sul monitor seriale (9600 baud), una riga per ciclo:

```
PITCH=3  ROLL=-1  AMP=10  PARA=0  ALT=12cm  TX=OK
```

## Note sul codice (v1.3, pubblicato senza modifiche)

- Il servo `Servogambe` è dichiarato e comandato, ma non è collegato a nessun pin
  (manca `attach`), e `write(-180)` è fuori dall'intervallo 0–180.
- Il `delay(500)` della conferma di caduta sospende per mezzo secondo la lettura dei sensori e la trasmissione.
- Gli angoli usano `3.14` al posto di π e vengono troncati a interi.
- La pressione di riferimento è quella standard (101325 Pa): l'altitudine è
  relativa al punto di accensione, quindi l'errore assoluto non incide.
- Il formato radio e seriale non corrisponde ancora a quello letto dal computer di
  terra py-v1.0: vedi il [README principale](../README.md), sezione *Stato attuale*.
