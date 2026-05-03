#include <Arduino.h>
#include <Wire.h>

#define I2C_ADDRESS 0x08

const char message[] = "Hello World";

void onRequest() {
  Wire.write((const uint8_t*)message, sizeof(message) - 1);
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(onRequest);
}

void loop() {
  delay(100);
}