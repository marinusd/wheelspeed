// wheel sensor pins - digital
const int pFW = 2; //frontWheelSensorPin
const int pRW = 3; //rearWheelSensorPin
// volatiles force loading from memory not registers. Required b/c interrupts.
volatile unsigned int frontCount, rearCount = 0u;
unsigned int nowFrontCount, prevFrontCount, deltaFrontCount = 0u;
unsigned int nowRearCount, prevRearCount, deltaRearCount = 0u;
volatile unsigned long frontMicros, rearMicros = 0ul;
unsigned long nowFrontMicros, prevFrontMicros, deltaFrontMicros = 0ul;
unsigned long prevRearMicros, nowRearMicros, deltaRearMicros    = 0ul;

// analog (ADC) pins
// rideHeightSensors are 3.3v
const int pRRH = 0; // RRH, right ride height
const int pLRH = 1; // LRH, left ride height
// other sensors are 5v
const int pFT  = 2; // FT, FuelTemperature
const int pFP  = 3; // FP, FuelPressure
const int pGP  = 4; // GP, GearPosition
const int pMAP = 5; // MAP, ManifoldAbsolutePressure
const int pAFR = 6; // AFR, AirFuelRatio, O2 sensor
// the analogReads() return ints between 0-1023
int AFR, FP, FT, MAP, GP, LRH, RRH = 0;
int loopct = 0;

void setup () {
  Serial.begin(9600);  // we only do output
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");
  pinMode(pFW, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pFW), frontPulseISR, RISING);
  pinMode(pRW, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pRW), rearPulseISR, RISING);
  // do initial reads on the analog pins
  analogRead(pRRH);
  analogRead(pLRH);
  analogRead(pFT);
  analogRead(pFP);
  analogRead(pGP);
  analogRead(pMAP);
  analogRead(pAFR);
  Serial.println(" Finished.");
  printHeader();
} // end of setup

// ISRs for wheel speed sensors
void frontPulseISR () {
  frontCount++;
  frontMicros = micros();
  }
void rearPulseISR () {
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
  Serial.print("RRH");  Serial.print(',');
  Serial.println("GP");
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
  Serial.print(RRH); Serial.print(',');
  Serial.println(GP);
}

void loop () {
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
  // gather the ADC inputs. The values returned are 0-1023 based on voltage.
  RRH = analogRead(pRRH); // right ride height
  LRH = analogRead(pLRH); // left ride height
  FT  = analogRead(pFT);  // fuel temperature
  FP  = analogRead(pFP);  // fuel pressure
  GP  = analogRead(pGP);  // gear position
  MAP = analogRead(pMAP); // manifold absolute pressure
  AFR = analogRead(pAFR); // Lambda, O2 sensor

  // send ze data
  printOutput();
  delay(300);
  }  // end of loop

