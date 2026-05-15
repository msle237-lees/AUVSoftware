#include <Arduino.h>
#include <Wire.h>
#include <Servo.h>

// ── I2C ──────────────────────────────────────────────────────────────────────
#define I2C_ADDRESS  0x08
#define PIN_SDA      4
#define PIN_SCL      5

// ── Motor PWM Pins ────────────────────────────────────────────────────────────
#define PIN_SERVO1   6
#define PIN_SERVO2   7
#define PIN_SERVO3   8

// ── BlueRobotics Basic ESC PWM Range ─────────────────────────────────────────
#define PWM_MIN         1100
#define PWM_NEUTRAL     1500
#define PWM_MAX         1900

#define NUM_SERVOS      3
#define REGISTER_THRUST 0x00

// ─────────────────────────────────────────────────────────────────────────────

Servo motors[NUM_SERVOS];

const uint8_t SERVO_PINS[NUM_SERVOS] = {
    PIN_SERVO1, PIN_SERVO2, PIN_SERVO3
};

static inline int toMicroseconds(uint8_t value) {
    return map(value, 0, 255, PWM_MIN, PWM_MAX);
}

void onReceive(int bytes) {
    uint8_t buf[6];
    uint8_t len = 0;

    while (Wire.available() && len < sizeof(buf)) {
        buf[len++] = Wire.read();
    }
    while (Wire.available()) Wire.read();

    if (len < 6 || buf[0] != REGISTER_THRUST) return;

    for (int i = 0; i < NUM_SERVOS; i++) {
        motors[i].writeMicroseconds(toMicroseconds(buf[i + 1]));
    }
}

void setup() {
    Wire.setSDA(PIN_SDA);
    Wire.setSCL(PIN_SCL);
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(onReceive);

    for (int i = 0; i < NUM_SERVOS; i++) {
        motors[i].attach(SERVO_PINS[i]);
        motors[i].writeMicroseconds(PWM_NEUTRAL);
    }
}

void loop() {
    delay(10);
}