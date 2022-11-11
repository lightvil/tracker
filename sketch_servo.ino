#include <Servo.h>

#define _ON_  1
#define _OFF_ 0

Servo servo_x;
Servo servo_z;
int angle_x = 0, angle_z = 0;
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  //
  servo_x.attach(9);
  servo_z.attach(10);

  delay(1000);
  // rotate to center
  rotate_to('x', 90);
  delay(1000);
  rotate_to('z', 90);
}

void turnLED(int on) {
  if (on) {
      digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on
  } else {
      digitalWrite(LED_BUILTIN, LOW);   // turn the LED off
  }
}

void reply_angle(char axis) {
    if (axis == 'X' || axis == 'x') {
      Serial.print("X");
      Serial.println(angle_x);
    } else if (axis == 'Z' || axis == 'z') {
      Serial.print("Z");
      Serial.println(angle_z);
    }
}

void rotate_to(char axis, int angle) {
  turnLED(_ON_);
  if (axis == 'x') {
    angle_x = angle;
    servo_x.write(angle_x);
    delay(20);
    reply_angle(axis);
  } else if (axis == 'z') {
    angle_z = angle;
    servo_z.write(angle_z);
    delay(20);
    reply_angle(axis);
  }
  turnLED(_OFF_);
}

int demo_count = 0;
void loop() {
  if (Serial.available()) {
    char axis = Serial.read();
    // 'X | Z' : report current angle
    //  "X100\n"의 형식
    if (axis == 'X' || axis == 'Z') {
      reply_angle(axis);
    } if (axis == 'x' || axis == 'z') {
      // not 'X|Z' lets see if  'x|z'
      //   "x100\n" 
      //
      int  angle = Serial.parseInt(SKIP_WHITESPACE);
      if (angle < 0) angle = 0;
      else if (angle > 180) angle = 180;
      rotate_to(axis, angle);
    }
  }
  //else {
  //  if (demo_count <= 18) {
  //      int angle = demo_count * 10;
  //      rotate_to('x', angle);
  //      delay(1000);
  //      rotate_to('z', angle);
  //      delay(1000);
  //      demo_count++;
  //    }
  //}
}
