// NANO2 module sketch
const char Version[] = {"20230825.NANO2"};

// Digital Pins
// Pin 2 is interrupt-driven by a cam position (Hall Effect) sensor.
// Pin 13 drives the on-board user LED.
// No other digital pins are used.

// Cam position sensor is Hall Effect. The pulses trigger interrupts because we'd like to count every pulse.
// To get rotation speed, we gather rotation count and elapsed time between readings in the ISR.
//  n.b. volatiles force loading from memory not registers. Required for interrupts.
volatile unsigned int  camPositionCount  = 0u;
volatile unsigned long camPositionMicros = 0ul;
// The 'now' variables are written in the ISR, and used with the others outside the ISR.
unsigned int  nowCamPositionCount,  prevCamPositionCount,  deltaCamPositionCount  = 0u;
unsigned long nowCamPositionMicros, prevCamPositionMicros, deltaCamPositionMicros = 0ul;

// cam position sensor pin - digital
const int pinCamPosition = 2; 

// sending-data
const int ledPin =  LED_BUILTIN; // fetches the number of the LED pin


// Analog Pins
//  analogRead() returns ints between 0-1023
// 0V-5V input pins
int rawEGT1, rawEGT2, rawEGT3, rawEGT4, rawACT = 0;
const int pinEGT1 = A1; 
const int pinEGT2 = A2; 
const int pinEGT3 = A3; 
const int pinEGT4 = A4;
const int pinACT  = A5;

// Serial commands
int incomingByte = 0;
char command = 'u';  // unassigned char

// Get all the things lined up
void setup ()
{
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.print("Starting setup...");

  // configure the hall effect pin
  pinMode(pinCamPosition, INPUT_PULLUP); 
  attachInterrupt(digitalPinToInterrupt(pinCamPosition), camPulseISR, RISING); // as the magnet leaves, voltage rises
  
  // will be the only sign something is working; serial through the UART does not blink the lights
  pinMode(ledPin, OUTPUT);

  // pullup the unused digital pins
  pinMode( 0, INPUT_PULLUP);
  pinMode( 1, INPUT_PULLUP);
  // 2 is the cam position pin
  pinMode( 3, INPUT_PULLUP);
  pinMode( 4, INPUT_PULLUP);
  pinMode( 5, INPUT_PULLUP);
  pinMode( 6, INPUT_PULLUP);
  pinMode( 7, INPUT_PULLUP);
  pinMode( 8, INPUT_PULLUP);
  pinMode( 9, INPUT_PULLUP);
  pinMode(10, INPUT_PULLUP);
  pinMode(11, INPUT_PULLUP);
  pinMode(12, INPUT_PULLUP);

  Serial.println(" Finished setup.");
  printHeader();
} // end of setup

// Interrupt Service Routines for hall effect sensors. ISRs are as short as possible.
//  cam count is 1/2 crank count, the rPi must handle that
void camPulseISR ()
{
  camPositionCount++;
  camPositionMicros = micros();
}

void resetCounts() {
  // zero  wheel sensor data
  noInterrupts ();  // don't allow changes while we write the volatiles
  camPositionCount = 0;
  interrupts (); // interrupts on again
  Serial.println("cam position count reset.");
}

// for tracking rpm
void updateCamPositionValues() {
  deltaCamPositionCount  = nowCamPositionCount  - prevCamPositionCount;
  deltaCamPositionMicros = nowCamPositionMicros - prevCamPositionMicros;
  // step forward once
  prevCamPositionCount  = nowCamPositionCount;
  prevCamPositionMicros = nowCamPositionMicros;
}

// this is the main data collection method.
void collectReadings() {
  // get wheel sensor data
  noInterrupts ();  // don't allow changes while we read the volatiles
  nowCamPositionCount  = camPositionCount;
  nowCamPositionMicros = camPositionMicros;
  interrupts (); // interrupts on again
  // gotta do some calcs on the data we pulled
  updateCamPositionValues();
  
  // gather the ADC inputs. The values returned are 0-1023 based on voltage.
  rawEGT1 = analogRead(pinEGT1);
  rawEGT2 = analogRead(pinEGT2);
  rawEGT3 = analogRead(pinEGT3);
  rawEGT4 = analogRead(pinEGT4);
  rawACT  = analogRead(pinACT);
}

// one of these functions will be asked for by the Linux box
void printSketchVersion() {
  Serial.print("NANO2 Version: "); Serial.println(Version);
}
void printHeader() {
  Serial.print("millis");                 Serial.print(',');
  Serial.print("camPositionCount");       Serial.print(',');
  Serial.print("deltaCamPositionCount");  Serial.print(',');
  Serial.print("deltaCamPositionMicros"); Serial.print(',');
  Serial.print("rawEGT1");                Serial.print(',');
  Serial.print("rawEGT2");                Serial.print(',');
  Serial.print("rawEGT3");                Serial.print(',');
  Serial.print("rawEGT4");                Serial.print(',');
  Serial.println("rawACT");
}
void printOutput () {
  // show we're processing a read
  digitalWrite(ledPin, HIGH);
  collectReadings();
  Serial.print(millis());               Serial.print(',');
  Serial.print(nowCamPositionCount);    Serial.print(',');
  Serial.print(deltaCamPositionCount);  Serial.print(',');
  Serial.print(deltaCamPositionMicros); Serial.print(',');
  Serial.print(rawEGT1);                Serial.print(',');
  Serial.print(rawEGT2);                Serial.print(',');
  Serial.print(rawEGT3);                Serial.print(',');
  Serial.print(rawEGT4);                Serial.print(',');
  Serial.println(rawACT);              // 9 elements total
  digitalWrite(ledPin, LOW);
}

// The main() event
void loop ()
{
  // we check for an incoming command
  if (Serial.available() > 0) {
    command = '?';  // set a non-active value to start
    // throw away all but the last command byte
    while (Serial.available() > 0) {
      incomingByte = Serial.read();
      if (incomingByte != 10) {  // ignore final line feed from the Arduino IDE Serial Monitor
        command = incomingByte;
      }
    }

    // we have a Byte - what is it?
    switch (command) {
      case 'd':
        printOutput();  // this also does the reads()
        break;
      case 'h':
        printHeader();
        break;
      case 'v':
        printSketchVersion();
        break;
      case 'z':
        resetCounts();
        break;
      default:
        Serial.print("Send h for header, d for data, v for version, z to zero cam position count. Received: "); Serial.println(command);
        break;
    }
  } // the end of the if statement; we come here immediately when there's no incoming serial data
  delay(100); // pause a tenth of a second; a caller will wait on average 1/2 of that

}  // end of loop()


// fin
