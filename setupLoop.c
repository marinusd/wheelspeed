// wheel sensor vars
const int D2 = 2;  //frontWheelSensorPin
const int D3 = 3;  //rearWheelSensorPin

volatile unsigned int frontCount, rearCount = 0u;
unsigned int nowFrontCount, prevFrontCount, deltaFrontCount = 0u;
unsigned int nowRearCount, prevRearCount, deltaRearCount = 0u;
volatile unsigned long frontMicros, rearMicros = 0ul;
unsigned long nowFrontMicros, prevFrontMicros, deltaFrontMicros = 0ul;
unsigned long prevRearMicros, nowRearMicros, deltaRearMicros    = 0ul;

// rideHeightSensors are 3.3v, get them with a divider
const int A0 = 0; // AFR, AirFuelRatio, O2 sensor
const int A1 = 1; // FP, FuelPressure
const int A2 = 2; // FT, FuelTemperature
const int A3 = 3; // MAP, ManifoldAbsolutePressure
const int A4 = 4; // LRH, left ride height
const int A5 = 5; // RRH, right ride height
// the analogReads() return ints between 0-1023
int AFR, FP, FT, MAP, LRH, RRH = 0;
String output = "";


void setup ()
  {
  Serial.begin(9600);  // we only do output
  pinMode(D2, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(D2), frontPulseISR, RISING);
  pinMode(D3, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(D3), rearPulseISR, RISING);
  // do initial reads on the analog pins
  analogRead(A0);
  analogRead(A1);
  analogRead(A2);
  analogRead(A3);
  analogRead(A4);
  analogRead(A5);
} // end of setup

// ISRs for wheel speed sensors
void frontPulseISR ()
  {
  frontCount++;
  frontMicros = micros()
  }
void rearPulseISR ()
  {
  rearCount++;
  rearMicros = micros()
  }

void updateWheelValues() {
  deltaFrontCount  = nowFrontCount-prevFrontCount;
  deltaFrontMicros = nowFrontMicros-prevFrontMicros;
  deltaRearCount   = nowRearCount-prevRearCount;
  deltaRearMicros  = nowRearMicros-prevRearMicros;
  prevFrontCount  = nowFrontCount;
  prevFrontMicros = nowFrontMicros;
  prevRearCount   = nowRearCount;
  prevRearMicros  = nowRearMicros;
  //frontRPM = rpm(deltaFrontCount, deltaFrontMicros);
  //rearRPM  = rpm(deltaRearCount, deltaRearMicros);
}

int rpm(int deltaCount, long deltaMicros) {
  int revsPerMinute = 0;
  if (deltaMicros > 1) {
    float revsPerMicro = deltaCount/(deltaMicros*1.0);
    revsPerMinute = revsPerMicro * (1000*1000*60);
  }
  return revsPerMinute;
}

String assembleOutput () {
  output = millis(); output += ",";   // timestamp, though this is the local timestamp
  output += deltaFrontCount; output += ",";
  output += deltaFrontMicros; output += ",";
  output += deltaRearCount; output += ",";
  output += deltaRearMicros; output += ",";
  output += AFR; output += ",";
  output += FP; output += ",";
  output += FT; output += ",";
  output += MAP; output += ",";
  output += LRH; ouput += ",";
  output += RRH;
}

void loop ()
  {
  // get wheel speeds
  noInterrupts ();  // dont allow changes while we read the volatiles
  nowFrontCount  = frontCount;
  nowFrontMicros = frontMicros;
  nowRearCount   = rearCount;
  nowRearMicros  = rearMicros;
  interrupts ();
  updateWheelValues()
  // gather the other inputs
  AFR = analogRead(A0);
  FP  = analogRead(A1);  // fuel pressure
  FT  = analogRead(A2);  // fuel temperature
  MAP = analogRead(A3);
  LRH = analogRead(A4);  // left ride height
  RRH = analogRead(A5);  // right ride height
  // send an output string
  assembleOutput()
  Serial.println(output);
  delay(100);
  }  // end of loop
