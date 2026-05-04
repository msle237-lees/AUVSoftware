#include <Arduino.h>
#include <Wire.h>

#define I2C_ADDRESS 0x08

const char message[] = "Hello World";
volatile bool aborted = false;

void onRequest() {
  Wire.write((const uint8_t*)message, sizeof(message) - 1);
}

void onReceive(int bytes) {
  // Drain any unexpected write data to keep bus clean
  while (Wire.available()) Wire.read();
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(onRequest);
  Wire.onReceive(onReceive);  // prevents receive buffer filling up
}

void loop() {
  delay(100);
}