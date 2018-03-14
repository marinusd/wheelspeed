// Gen IV module sketch
// 2018-03-14

// Digital Pins
// Pins 0 & 1 are for the UART to communicate with the rPi.
// Pins 2 & 3 are interrupt-driven by Hall Effect sensors.
// No other digital pins are used.

// Wheel Speed sensors are Hall Effect. The pulses trigger interrupts because we'd like to count every pulse. 
// To get rotation speed, we gather rotation count and elapsed time between readings in the ISR.
//  n.b. volatiles force loading from memory not registers. Required for interrupts.
volatile unsigned int  frontCount,  rearCount  = 0u;
volatile unsigned long frontMicros, rearMicros = 0ul;
// The 'now' Wheel Speed variables are written in the ISR, and used with the others outside the ISR.
unsigned int  nowFrontCount,  prevFrontCount,  deltaFrontCount  = 0u;
unsigned int  nowRearCount,   prevRearCount,   deltaRearCount   = 0u;
unsigned long nowFrontMicros, prevFrontMicros, deltaFrontMicros = 0ul;
unsigned long nowRearMicros,  prevRearMicros,  deltaRearMicros  = 0ul;
// wheel sensor pins - digital
const int pinFW = 2; //frontWheelSensorPin
const int pinRW = 3; //rearWheelSensorPin

// Analog Pins
//  analogRead() returns ints between 0-1023

// rideHeightSensors - analog, 0V-3.3V return
int rawLeftRideHeight, rawRightRideHeight = 0;  
const int pinRightRideHeight = A0; 
const int pinLeftRideHeight  = A1; 

// voltage divider pins; feed 5V in, get something less back
int rawFuelPressure, rawFuelTemperature, rawGearPosition = 0;
const int pinFuelPressure    = A2; 
const int pinFuelTemperature = A3; 
const int pinGearPosition    = A4; 

// 0V-5V input pins 
int rawAirFuelRatio, rawManifoldAbsolutePressure, rawExhaustGasTemperature = 0;
const int pinAirFuelRatio             = A5; 
const int pinManifoldAbsolutePressure = A6; 
const int pinExhaustGasTemperature    = A7; 

// Serial (UART) commands 
int incomingByte = 0;
char command = 'z';  // unassigned char

// Get all the things lined up
void setup ()
{
  Serial.begin(9600);  
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");

  // configure the hall effect pins
  pinMode(pinFW, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pinFW), frontPulseISR, RISING); // as the magnet leaves, voltage rises
  pinMode(pinRW, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pinRW), rearPulseISR, RISING);
 
  // pullup the unused digital pins 
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
  // A0&A1 are ride height sensor
  //pinMode(A2, INPUT_PULLUP);
  //pinMode(A3, INPUT_PULLUP);
  //pinMode(A4, INPUT_PULLUP);
  //pinMode(A5, INPUT_PULLUP);
  //pinMode(A6, INPUT_PULLUP);
  //pinMode(A7, INPUT_PULLUP);

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

// for tracking wheel speed
void updateDeltaWheelValues() {
  deltaFrontCount  = nowFrontCount  - prevFrontCount;
  deltaFrontMicros = nowFrontMicros - prevFrontMicros;
  deltaRearCount   = nowRearCount   - prevRearCount;
  deltaRearMicros  = nowRearMicros  - prevRearMicros;
  // step forward once
  prevFrontCount  = nowFrontCount;
  prevFrontMicros = nowFrontMicros;
  prevRearCount   = nowRearCount;
  prevRearMicros  = nowRearMicros;
}

// this is the main data collection method. It'll get called every loop.
void collectReadings() {
  // get wheel sensor data 
  noInterrupts ();  // dont allow changes while we read the volatiles
  nowFrontCount  = frontCount;
  nowFrontMicros = frontMicros;
  nowRearCount   = rearCount;
  nowRearMicros  = rearMicros;
  interrupts (); // interrupts on again
  
  // gather the ADC inputs. The values returned are 0-1023 based on voltage.
  rawRightRideHeight          = analogRead(pinRightRideHeight); 
  rawLeftRideHeight           = analogRead(pinLeftRideHeight); 
  rawFuelPressure             = analogRead(pinFuelPressure);
  rawFuelTemperature          = analogRead(pinFuelTemperature);
  rawGearPosition             = analogRead(pinGearPosition);
  rawAirFuelRatio             = analogRead(pinAirFuelRatio);
  rawManifoldAbsolutePressure = analogRead(pinManifoldAbsolutePressure);
  rawExhaustGasTemperature    = analogRead(pinExhaustGasTemperature);
  
  // gotta do some calcs on the data we pulled 
  updateDeltaWheelValues();   
}

// one of these functions will be asked for by the Linux box
void printHeader() {
  Serial.print("millis");                       Serial.print(',');
  Serial.print("frontCount");                   Serial.print(',');
  Serial.print("deltaFrontCount");              Serial.print(',');
  Serial.print("deltaFrontMicros");             Serial.print(',');
  Serial.print("rearCount");                    Serial.print(',');
  Serial.print("deltaRearCount");               Serial.print(',');
  Serial.print("deltaRearMicros");              Serial.print(',');
  Serial.print("rawLeftRideHeight");            Serial.print(',');
  Serial.print("rawRightRideHeight");           Serial.print(',');
  Serial.print("rawFuelPressure");              Serial.print(',');
  Serial.print("rawFuelTemperature");           Serial.print(',');
  Serial.print("rawGearPosition");              Serial.print(',');
  Serial.print("rawAirFuelRatio");              Serial.print(',');
  Serial.print("rawManifoldAbsolutePressure");  Serial.print(',');
  Serial.println("rawExhaustGasTemperature"); 
}
void printOutput () {
  collectReadings();
  Serial.print(millis());                     Serial.print(',');
  Serial.print(nowFrontCount);                Serial.print(',');
  Serial.print(deltaFrontCount);              Serial.print(',');
  Serial.print(deltaFrontMicros);             Serial.print(',');
  Serial.print(nowRearCount);                 Serial.print(',');
  Serial.print(deltaRearCount);               Serial.print(',');
  Serial.print(deltaRearMicros);              Serial.print(',');
  Serial.print(rawLeftRideHeight);            Serial.print(',');
  Serial.print(rawRightRideHeight);           Serial.print(',');
  Serial.print(rawFuelPressure);              Serial.print(',');
  Serial.print(rawFuelTemperature);           Serial.print(',');
  Serial.print(rawGearPosition);              Serial.print(',');
  Serial.print(rawAirFuelRatio);              Serial.print(',');
  Serial.print(rawManifoldAbsolutePressure);  Serial.print(',');
  Serial.println(rawExhaustGasTemperature); 
}

// The main() event
void loop ()
{ 
  // we check for an incoming command   
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
      printOutput();  // this also does the reads()
    } else if (command == 'h') {
      printHeader();
    } else {
      Serial.print(" ? Send h for header or d for data. Received: "); Serial.println(command);
    }
    
  } // the end of the if; we come here immediately when there's no incoming command 
  delay(100); // tenth of a second
}  // end of loop()

// fin
