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
const int pA0 = 0; // AFR, AirFuelRatio, O2 sensor
const int pA1 = 1; // FP, FuelPressure
const int pA2 = 2; // FT, FuelTemperature
const int pA3 = 3; // MAP, ManifoldAbsolutePressure
const int pA4 = 4; // LRH, left ride height
const int pA5 = 5; // RRH, right ride height
// the analogReads() return ints between 0-1023
int AFR, FP, FT, MAP, LRH, RRH = 0;
int loopct = 0;

void setup ()
  {
  Serial.begin(9600);  // we only do output
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");
  pinMode(D2, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(D2), frontPulseISR, RISING);
  pinMode(D3, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(D3), rearPulseISR, RISING);
  // do initial reads on the analog pins
  analogRead(pA0);
  analogRead(pA1);
  analogRead(pA2);
  analogRead(pA3);
  analogRead(pA4);
  analogRead(pA5);
  Serial.println(" Finished.");
  printHeader();
} // end of setup

// ISRs for wheel speed sensors
void frontPulseISR ()
  {
  frontCount++;
  frontMicros = micros();
  }
void rearPulseISR ()
  {
  rearCount++;
  rearMicros = micros();
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
}

void printHeader() {
  Serial.print("millis"); Serial.print(',');
  Serial.print("frontCount"); Serial.print(',');
  Serial.print("deltaFrontCount"); Serial.print(',');
  Serial.print("deltaFrontMicros"); Serial.print(',');
  Serial.print("rearCount"); Serial.print(',');
  Serial.print("deltaRearCount"); Serial.print(',');
  Serial.print("deltaRearMicros"); Serial.print(',');
  Serial.print("AFR"); Serial.print(',');
  Serial.print("FP"); Serial.print(',');
  Serial.print("FT"); Serial.print(',');
  Serial.print("MAP"); Serial.print(',');
  Serial.print("LRH"); Serial.print(',');
  Serial.println("RRH");
}

void printOutput () {
  Serial.print(millis()); Serial.print(',');
  Serial.print(nowFrontCount); Serial.print(',');
  Serial.print(deltaFrontCount); Serial.print(',');
  Serial.print(deltaFrontMicros); Serial.print(',');
  Serial.print(nowRearCount); Serial.print(',');
  Serial.print(deltaRearCount); Serial.print(',');
  Serial.print(deltaRearMicros); Serial.print(',');
  Serial.print(AFR); Serial.print(',');
  Serial.print(FP); Serial.print(',');
  Serial.print(FT); Serial.print(',');
  Serial.print(MAP); Serial.print(',');
  Serial.print(LRH); Serial.print(',');
  Serial.println(RRH);
}

void loop ()
  {
  loopct++;
  if (loopct >= 40) { printHeader(); loopct = 0; }
  // get wheel speeds
  noInterrupts ();  // dont allow changes while we read the volatiles
  nowFrontCount  = frontCount;
  nowFrontMicros = frontMicros;
  nowRearCount   = rearCount;
  nowRearMicros  = rearMicros;
  interrupts ();
  updateWheelValues();
  // gather the other inputs
  AFR = analogRead(pA0);
  FP  = analogRead(pA1);  // fuel pressure
  FT  = analogRead(pA2);  // fuel temperature
  MAP = analogRead(pA3);
  LRH = analogRead(pA4);  // left ride height
  RRH = analogRead(pA5);  // right ride height
  // send ze data
  printOutput();
  delay(500);
  }  // end of loop

