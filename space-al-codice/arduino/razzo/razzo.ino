#include <Wire.h>
#include <Servo.h>
#include <SPI.h>
#include <RF24.h>
#include <Adafruit_BMP085.h>   // ← AGGIUNTO: libreria BMP180

const int MPU_addr = 0x68;
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;
float ax = 0, ay = 0, az = 0, gx = 0, gy = 0, gz = 0;

struct __attribute__((packed)) SensorData {
  int32_t Pitch;
  int32_t Roll;
  int32_t altitudine;
  int32_t paracadute;
  int32_t Amp;
};

RF24 radio(9, 10);
const byte address[6] = "ABCDE";
bool trustVector = false;

Servo ServoX;
Servo ServoY;
Servo ServoX1;
Servo ServoY1;
Servo Servopara;
Servo Servogambe;

SensorData data;
int memoria = 0;

Adafruit_BMP085 bmp;                  // ← AGGIUNTO: oggetto BMP180
float altitudineDiRiferimento = 0;    // ← AGGIUNTO: quota zero al momento dell'accensione

void setup() {
  Serial.begin(9600);

  radio.begin();
  radio.setChannel(100);
  radio.setPALevel(RF24_PA_MIN);
  radio.setDataRate(RF24_250KBPS);
  radio.openWritingPipe(address);
  radio.stopListening();

  Wire.begin();
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // ← AGGIUNTO: inizializzazione BMP180
  if (bmp.begin()) {
    altitudineDiRiferimento = bmp.readAltitude(101325);
    Serial.println("BMP180 OK");
  } else {
    Serial.println("BMP180 ERRORE");
  }

  ServoX.attach(8);
  ServoY.attach(7);
  Servopara.attach(5);

  Servopara.write(135);
  data.altitudine = 0;
  data.paracadute = 0;
  data.Amp        = 0;

  Serial.print("Dimensione struct: ");
  Serial.println(sizeof(data)); // deve stampare 20
}

void loop() {
  mpu_read();
  ax = (AcX - 2050) / 16384.00;
  ay = (AcY - 77)   / 16384.00;
  az = (AcZ - 1947) / 16384.00;
  gx = (GyX + 270)  / 131.07;
  gy = (GyY - 351)  / 131.07;
  gz = (GyZ + 136)  / 131.07;

  float Raw_Amp = pow(pow(ax,2) + pow(ay,2) + pow(az,2), 0.5);
  data.Amp   = Raw_Amp * 10;
  data.Roll  = FunctionsPitchRoll(AcX, AcY, AcZ);
  data.Pitch = FunctionsPitchRoll(AcY, AcX, AcZ);

  // ← AGGIUNTO: lettura altitudine relativa in cm (int32_t)
  float altitudineAssoluta = bmp.readAltitude(101325);
  data.altitudine = (int32_t)((altitudineAssoluta - altitudineDiRiferimento) * 100);

  int ServoRoll  = map(data.Roll,  -90, 90,   0, 179);
  int ServoPitch = map(data.Pitch, -90, 90, 179,   0);

  if (trustVector) {
    ServoX.write(ServoRoll);
    ServoY.write(ServoPitch);
  }

  bool ok = radio.write(&data, sizeof(data));

  Serial.print("PITCH=");      Serial.print(data.Pitch);
  Serial.print("  ROLL=");     Serial.print(data.Roll);
  Serial.print("  AMP=");      Serial.print(data.Amp);
  Serial.print("  PARA=");     Serial.print(data.paracadute);
  Serial.print("  ALT=");      Serial.print(data.altitudine);   // ← AGGIUNTO
  Serial.print("cm  TX=");     Serial.println(ok ? "OK" : "FAIL");

  if (data.Amp > 10) {
    trustVector = true;
  }

  if (data.Amp - memoria > 0) {
    memoria = data.Amp;
  } else if (data.Amp - memoria < -9) {
    delay(500);
    if (data.Amp - memoria < -3) {
      Serial.println("cado!!");
      data.paracadute = 1;
      radio.write(&data, sizeof(data));
      Servopara.write(180);
      Servogambe.write(-180);
      delay(1000);
      Servopara.write(90);
      Servogambe.write(90);
      data.paracadute = 0;
      memoria = 0;
      trustVector = false;
    }
  }

  delay(100);
}

void mpu_read() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 14, true);
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Tmp = Wire.read() << 8 | Wire.read();
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();
}

double FunctionsPitchRoll(double A, double B, double C) {
  double DatoB = sqrt(B*B + C*C);
  double Value = atan2(A, DatoB) * 180 / 3.14;
  return (int)Value;
}
