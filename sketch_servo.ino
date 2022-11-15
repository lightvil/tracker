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

int demo = 0;
int DEBUG = 0;
int index = 0;
char buffer[512];
void append(char c) {
  buffer[index] = c;
  index++;
  buffer[index] = 0;
}
void update_reset() {
  // 버퍼에 최소한 두 글자가 있어야 한다. 그렇지 않으면 버린다.
  // x1\r\n
  // x100\r\n
  // x100\r\n
  if (index >= 2) {
    buffer[index] = 0;
    rotate_to(buffer[0], atoi(buffer + 1));
  }
  index = 0;
  buffer[index] = 0;
}

void loop() {
  if (demo > 0) {
    rotate_to('x', demo);     delay(100);
    rotate_to('z', demo);     delay(100);
    demo = (demo + 10) % 180; delay(800);
  }
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (DEBUG) {
      if (c != '\r' || c != '\n') {
        Serial.print("DEBUG C: [");
        Serial.print(c);
        Serial.print("], INDEX: ");
        Serial.print(index);
        Serial.print(", BUFFER: ");
        Serial.println(buffer);
      }
    }
    if (c == 'D' | c == 'd') {
      DEBUG = DEBUG == 0;
    } else if (c == 'T' || c == 't') {
      demo = 10;
    } else if (c == 'C' || c == 'c') {
      rotate_to('x', 90)
      rotate_to('z', 90)
    } else if (c == 'X' || c == 'Z') {
      // 좌표 값을 조회하는 명령어
      // 이미 버퍼에 들어있는 명령어가 있다면 처리한다.
      update_reset();
      reply_angle(c);
    } else if (c == 'x' || c == 'z') {
      // 새로운 좌표 변경 명령어가 시작되었다.
      // 이미 버퍼에 들어있는 명령어가 있다면 처리한다.
      update_reset();
      append(c);
    } else if (c >= '0' && c <= '9') {
      // 좌표변경 명령어인 'x' 또는 'z'가 들어 있어야 한다.
      // 그래서 index > 0 이면 버퍼에 추가
      if (index > 0) {
        append(c);
      }
    } else if (isSpace(c)) {
      // whitespace는 추가하지는 않는다.
      // 좌표 변경 데이터가 있으면 처리하면 된다.
      update_reset();
    }
  }
}