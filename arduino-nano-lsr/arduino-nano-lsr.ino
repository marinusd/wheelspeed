// Gen IV module sketch
const long Version = 20180521;  // 2018-05-21
const char subVersion = 'a';

// Digital Pins
// Pins 0 & 1 are for the UART to communicate with the rPi.
// Pins 2 & 3 are interrupt-driven by Hall Effect sensors.
// Pin 13 drives the on-board user LED.
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
// sending-data
const int ledPin =  LED_BUILTIN; // fetches the number of the LED pin


// Analog Pins
//  analogRead() returns ints between 0-1023

// rideHeightSensors - analog, 0V-3.3V return
int rawLeftRideHeight, rawRightRideHeight = 0;  
const int pinRightRideHeight = A0; // small diameter white
const int pinLeftRideHeight  = A1; // small diameter green

// 0V-5V input pins 
int rawAirFuelRatio, rawManifoldAbsolutePressure;
const int pinManifoldAbsolutePressure = A2; //grey
const int pinAirFuelRatio             = A3; // large green

// voltage divider pins; feed 5V in, get something less back
int rawFuelPressure, rawFuelTemperature, rawGearPosition = 0;
const int pinGearPosition    = A4; // small diameter yellow
const int pinFuelPressure    = A5; // orange
const int pinFuelTemperature = A6; // blue

// unknowns
int rawExhaustGasTemperature = 0;
const int pinExhaustGasTemperature = A7; // small diameter white 

// Serial (UART) commands 
int incomingByte = 0;
char command = 'z';  // unassigned char

// Get all the things lined up
void setup ()
{
  Serial.begin(38400);  
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");

  // configure the hall effect pins
  pinMode(pinFW, INPUT_PULLUP);  // frontWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pinFW), frontPulseISR, RISING); // as the magnet leaves, voltage rises
  pinMode(pinRW, INPUT_PULLUP);  // rearWheelSensorPin
  attachInterrupt(digitalPinToInterrupt(pinRW), rearPulseISR, RISING);

  // will be the only sign something is working; serial through the UART does not blink the lights
  pinMode(ledPin, OUTPUT);

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

// this is the main data collection method. 
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
void printVersion() {
  Serial.print("Version: "); Serial.print(Version); Serial.println(subVersion); 
}
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
    
    // throw away all but the last command byte
    while (Serial.available() > 0) {
      incomingByte = Serial.read();
      if (incomingByte != 10) {  // strip final line feed for IDE Serial Monitor
        command = incomingByte;
      }
    }
    digitalWrite(ledPin, HIGH); // showing we're doing something
    
    // we have a Byte - what is it?
    if (command == 'd') {
      printOutput();  // this also does the reads()

    } else if (command == 'h') {
      printHeader();

    } else if (command == 'v') {
      printVersion();

    } else {
      Serial.print(" ? Send h for header, d for data, v for version. Received: "); Serial.println(command);
    }
    
  } // the end of the if; we come here immediately when there's no incoming command 

  delay(100); // pause a tenth of a second; a caller will wait on average 1/2 of that
  digitalWrite(ledPin, LOW); // this may already be off

}  // end of loop()


// fin
