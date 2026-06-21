# Documentazione Firmware — `firmware/razzo.ino`

## Panoramica

Il firmware è il **computer di bordo** del razzo ad acqua Space AL. Gira su un **Arduino Nano** montato all'interno della fusoliera e ha tre responsabilità principali:

1. **Acquisire** l'assetto (pitch e roll) e l'altitudine ogni 100 ms.
2. **Stabilizzare** attivamente il razzo durante la fase propulsa muovendo due servo.
3. **Aprire il paracadute** in automatico al rilevamento della caduta libera.
4. **Trasmettere** tutti i dati alla stazione di terra via radio 2.4 GHz.

---

## Dipendenze (librerie Arduino)

| Libreria | Uso |
|---|---|
| `Wire.h` | Comunicazione I²C con MPU6050 e BMP180 |
| `Servo.h` | Controllo servo PWM |
| `SPI.h` | Bus SPI per il modulo radio |
| `RF24.h` | Driver per il modulo nRF24L01 |
| `Adafruit_BMP085.h` | Driver per BMP180 (altimetro/barometro) |

---

## Hardware collegato

| Periferica | Pin Arduino | Note |
|---|---|---|
| nRF24L01 — CE | 9 | Chip Enable radio |
| nRF24L01 — CSN | 10 | Chip Select (SPI) |
| MPU6050 | SDA/SCL | Indirizzo I²C `0x68` |
| BMP180 | SDA/SCL | Condivide il bus I²C |
| Servo Roll (ServoX) | 8 | Stabilizzazione sull'asse di rollio |
| Servo Pitch (ServoY) | 7 | Stabilizzazione sull'asse di beccheggio |
| Servo Paracadute | 5 | Apertura/chiusura paracadute |
| Servo Gambe | (non attach) | Previsto ma non ancora cablato in v4.0 |

---

## Struttura dati trasmessa

```cpp
struct __attribute__((packed)) SensorData {
    int32_t Pitch;       // beccheggio in gradi (×1)
    int32_t Roll;        // rollio in gradi (×1)
    int32_t altitudine;  // altitudine relativa in cm
    int32_t paracadute;  // 0 = chiuso, 1 = aperto
    int32_t Amp;         // modulo del vettore accelerazione ×10
};
```

`__attribute__((packed))` garantisce che la struct occupi esattamente **20 byte** senza padding, semplificando la deserializzazione sul lato ricevente.

### Calcolo dell'altitudine

L'altitudine viene misurata **relativa al suolo**: al momento dell'accensione il firmware memorizza la quota barometrica assoluta (`altitudineDiRiferimento`) e calcola ad ogni ciclo la differenza:

```cpp
float altitudineAssoluta = bmp.readAltitude(101325);
data.altitudine = (int32_t)((altitudineAssoluta - altitudineDiRiferimento) * 100);
```

Il valore è in **centimetri** (moltiplicato per 100) per mantenere la precisione all'interno di un `int32_t`.

---

## Flusso di esecuzione

### `setup()`

```
1. Serial.begin(9600)
2. Inizializza radio nRF24L01
   - canale 100, PA_MIN, 250 kbps
   - apre pipe di scrittura "ABCDE"
3. Inizializza MPU6050 via I²C
   - scrive 0x00 nel registro 0x6B (disattiva sleep)
4. Inizializza BMP180
   - memorizza altitudineDiRiferimento (pressione 101325 Pa)
5. Aggancia servo sui pin 8, 7, 5
6. Posizione iniziale paracadute: 135°
```

### `loop()` — ciclo da 100 ms

```
1. mpu_read()           → legge 7 raw da MPU6050 via I²C
2. Calcola ax, ay, az   → normalizza con offset di calibrazione
3. Calcola gx, gy, gz   → non usati nel controllo, solo telemetria
4. Raw_Amp              → modulo del vettore acc. (usato per rilevare lancio e caduta)
5. data.Roll            → FunctionsPitchRoll(AcX, AcY, AcZ)
6. data.Pitch           → FunctionsPitchRoll(AcY, AcX, AcZ)
7. data.altitudine      → BMP180 (cm relativi al suolo)
8. Servo mapping        → da ±90° a 0–179° per ServoX e ServoY
9. if (trustVector)     → muovi servo solo durante la spinta
10. radio.write()       → trasmetti 20 byte
11. Serial.print()      → log su monitor seriale
12. Rilevamento lancio  → se Amp > 10 (≈1 g), attiva trustVector
13. Rilevamento caduta  → se Amp cala di >9 unità → attendi 500 ms →
                          conferma calo >3 → apri paracadute
14. delay(100)
```

---

## Logica di stabilizzazione

I servo vengono comandati solo quando `trustVector == true`, ovvero dopo che il modulo dell'accelerazione ha superato i **10 g** (`data.Amp > 10`, dove Amp è il valore ×10).

```cpp
int ServoRoll  = map(data.Roll,  -90, 90,   0, 179);
int ServoPitch = map(data.Pitch, -90, 90, 179,   0);

if (trustVector) {
    ServoX.write(ServoRoll);
    ServoY.write(ServoPitch);
}
```

Il mapping è invertito per il pitch (`179, 0`) perché il servo è montato nella direzione opposta.

---

## Rilevamento caduta libera e apertura paracadute

L'algoritmo usa una soglia isteresi a due stadi per evitare falsi positivi da vibrazioni:

```
Condizione 1: Amp corrente - memoria < -9
  → attendi 500 ms (filtro anti-rimbalzo)
Condizione 2: Amp - memoria < -3
  → paracadute aperto (Servopara a 180°, poi riportato a 90°)
  → trasmissione di un pacchetto di emergenza
  → reset di trustVector e memoria
```

Dopo l'apertura il paracadute viene riportato in posizione neutra (90°) per essere pronto a un eventuale riutilizzo.

---

## Calibrazione MPU6050

I valori di offset applicati sono specifici dell'unità hardware usata:

```cpp
ax = (AcX - 2050) / 16384.00;   // offset AcX
ay = (AcY -   77) / 16384.00;   // offset AcY
az = (AcZ - 1947) / 16384.00;   // offset AcZ
gx = (GyX +  270) / 131.07;
gy = (GyY -  351) / 131.07;
gz = (GyZ +  136) / 131.07;
```

Se si sostituisce l'MPU6050 è necessario ricalibrare e aggiornare questi valori.

---

## Configurazione radio

```cpp
RF24 radio(9, 10);                    // CE=9, CSN=10
const byte address[6] = "ABCDE";

radio.setChannel(100);               // canale RF (100 = 2.500 GHz)
radio.setPALevel(RF24_PA_MIN);       // potenza minima (uso in laboratorio)
radio.setDataRate(RF24_250KBPS);     // 250 kbps, massima portata
radio.openWritingPipe(address);
radio.stopListening();               // modalita' trasmettitore
```

La stazione di terra deve usare gli stessi parametri con `openReadingPipe`.

---

## Output seriale (debug)

Ad ogni ciclo viene stampata una riga del tipo:

```
PITCH=3  ROLL=-1  AMP=12  PARA=0  ALT=145cm  TX=OK
```

Utile per il debug senza la dashboard, collegando l'Arduino al PC via USB e aprendo il Serial Monitor a 9600 baud.

---

## Note di versione

Il firmware attuale è la **v4.0** (Aprile 2026). Le principali aggiunte rispetto alla v3.0 sono:
- `struct __attribute__((packed))` a 20 byte (prima i campi erano separati)
- Altitudine relativa via BMP180 in centimetri
- Predisposizione per le gambe di atterraggio deployabili (`Servogambe`)
