// chassis module sketch
// 2017-11-24b

// volatiles force loading from memory not registers. Required b/c interrupts.
volatile unsigned int frontCount, rearCount = 0u;
unsigned int nowFrontCount, prevFrontCount, deltaFrontCount = 0u;
unsigned int nowRearCount, prevRearCount, deltaRearCount = 0u;
volatile unsigned long frontMicros, rearMicros = 0ul;
unsigned long nowFrontMicros, prevFrontMicros, deltaFrontMicros = 0ul;
unsigned long prevRearMicros, nowRearMicros, deltaRearMicros    = 0ul;
// the analogReads() return ints between 0-1023
int LRH, RRH = 0;
int loopct = 0;

// wheel sensor pins - digital
const int pFW = 2; //frontWheelSensorPin
const int pRW = 3; //rearWheelSensorPin
// rideHeightSensors pins - analog, 3.3v
const int pRRH = A1; // RRH, right ride height
const int pLRH = A2; // LRH, left ride height


void setup ()
{
  Serial.begin(9600);  // we only do output
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");

  // configure the hall effect pins
  pinMode(pFW, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pFW), frontPulseISR, RISING);
  pinMode(pRW, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pRW), rearPulseISR, RISING);
 
  // do initial reads on the analog pins 
  analogRead(pRRH);
  analogRead(pLRH);
  
  // pullup the unused analog and digital pins 
  // 0&1 are serial, 2&3 are wheel sensor 
  digitalWrite(4, INPUT_PULLUP);
  digitalWrite(5, INPUT_PULLUP);
  digitalWrite(6, INPUT_PULLUP);
  digitalWrite(7, INPUT_PULLUP);
  digitalWrite(8, INPUT_PULLUP);
  digitalWrite(9, INPUT_PULLUP);  
  digitalWrite(10, INPUT_PULLUP);
  digitalWrite(11, INPUT_PULLUP);
  digitalWrite(12, INPUT_PULLUP);
  // analogs            
  // A1&A2 are ride height sensor
  digitalWrite(A0, INPUT_PULLUP);
  digitalWrite(A3, INPUT_PULLUP);
  digitalWrite(A4, INPUT_PULLUP);
  digitalWrite(A5, INPUT_PULLUP);
  digitalWrite(A6, INPUT_PULLUP);
  digitalWrite(A7, INPUT_PULLUP);

  Serial.println(" Finished.");
  printHeader();
} // end of setup

// Interrupt Service Routines for wheel speed sensors
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
  deltaFrontCount  = nowFrontCount - prevFrontCount;
  deltaFrontMicros = nowFrontMicros - prevFrontMicros;
  deltaRearCount   = nowRearCount - prevRearCount;
  deltaRearMicros  = nowRearMicros - prevRearMicros;
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
  Serial.print(LRH); Serial.print(',');
  Serial.println(RRH);
}

void loop ()
{
  loopct++;
  if (loopct >= 40) {
    printHeader();
    loopct = 0;
  }
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

  // send ze data
  printOutput();
  delay(200);
}  // end of loop
