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
int incomingByte = 0;
char command = 'z';  // unassigned char

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
  pinMode(4, INPUT_PULLUP);
  pinMode(5, INPUT_PULLUP);
  pinMode(6, INPUT_PULLUP);
  pinMode(7, INPUT_PULLUP);
  pinMode(8, INPUT_PULLUP);
  pinMode(9, INPUT_PULLUP);  
  pinMode(10, INPUT_PULLUP);
  pinMode(11, INPUT_PULLUP);
  pinMode(12, INPUT_PULLUP);
  // analogs            
  // A1&A2 are ride height sensor
  pinMode(A0, INPUT_PULLUP);
  pinMode(A3, INPUT_PULLUP);
  pinMode(A4, INPUT_PULLUP);
  pinMode(A5, INPUT_PULLUP);
  pinMode(A6, INPUT_PULLUP);
  pinMode(A7, INPUT_PULLUP);

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

void collectReadings() {
  // get wheel speeds
  noInterrupts ();  // dont allow changes while we read the volatiles
  nowFrontCount  = frontCount;
  nowFrontMicros = frontMicros;
  nowRearCount   = rearCount;
  nowRearMicros  = rearMicros;
  interrupts ();
  // gather the ADC inputs. The values returned are 0-1023 based on voltage.
  RRH = analogRead(pRRH); // right ride height
  LRH = analogRead(pLRH); // left ride height
  updateWheelValues();    // prepared for printing
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
  collectReadings();
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
  // we listen for a command   
  if (Serial.available() > 0) {
    // Serial.println("Have input");
    // throw away all but the last command byte
    while (Serial.available() > 0) {
      incomingByte = Serial.read();
      if (incomingByte != 10) {  // strip final line feed for IDE Serial Monitor
        command = incomingByte;
      }
    }
    // we have a Byte - what is it?
    //Serial.print("Command: "); Serial.println(command);
    if (command == 'd') {
      printOutput();
    } else if (command == 'h') {
      printHeader();
    } else {
      Serial.print(" ? Send h for header or d for data. Received: "); Serial.println(command);
    }
  }
  delay(100); // tenth of a second
}  // end of loop
