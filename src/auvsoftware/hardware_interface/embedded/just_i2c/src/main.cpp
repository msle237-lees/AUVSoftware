#include <Arduino.h>
#include <Wire.h>

#define I2C_ADDRESS 0x09

const char message[] = "Hello World";

void onRequest() {
  Wire.write((const uint8_t*)message, sizeof(message) - 1);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  digitalWrite(LED_BUILTIN, HIGH);

  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(onRequest);
}

void loop() {
  delay(100);
}