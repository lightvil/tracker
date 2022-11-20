//
//
//
//
#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>

const int N = 5;

BLEService               GYROSCOPE_ADVERTISING_SERVICE("66df5109-edde-4f8a-a5e1-02e02a69cbd5");
BLEStringCharacteristic  ANGLE_X_CHARACTERISTIC("741c12b9-e13c-4992-8a5e-fce46dec0bff", BLERead | BLENotify, 8);
BLEStringCharacteristic  ANGLE_Y_CHARACTERISTIC("baad41b2-f12e-4322-9ba6-22cd9ce09832", BLERead | BLENotify, 8);
BLEStringCharacteristic  ANGLE_Z_CHARACTERISTIC("5748a25d-1834-4c68-a49b-81bf3aeb2e50", BLERead | BLENotify, 8);

long   last_gyro_time = 0;
long   last_advertised_time = 0;
int    accumulate_count = 0;
double average_gyroscope_x = 0, average_gyroscope_y = 0, average_gyroscope_z = 0;
double n_average_gyroscope_x = 0, n_average_gyroscope_y = 0, n_average_gyroscope_z = 0;

float  x, y, z;
double accumulated_x = 0, accumulated_y = 0, accumulated_z = 0;
int    fixed_x, fixed_y, fixed_z = 0;

//
// 자이로스코프 센서의 값을 읽는다.
// 초기에 구한 자이로스크포 센서 평균값을 뺀 후 반환한다.
// 원점 주변의 값을 무시하는 방법도 고려할 필요가 있다.
// 지금은 사용하지 않음.
void readGyroScope(double &x, double &y, double &z) {
  float gyroscope_x = 0, gyroscope_y = 0, gyroscope_z = 0;
  IMU.readGyroscope(gyroscope_x, gyroscope_y, gyroscope_z);
 
  x = gyroscope_x - average_gyroscope_x;
  y = gyroscope_y - average_gyroscope_y;
  z = gyroscope_y - average_gyroscope_z;
}

//
// skip_count 만큼 버리고 calibration_count 만큼 센서 데이터를 읽어 평균을 구한다.
//
void calibrate_gyro_sensor() {
  float gyroscope_x = 0, gyroscope_y = 0, gyroscope_z = 0;
  double sum_x = 0, sum_y = 0, sum_z = 0;

  int calibration_count = 100;
  int skip_count        = 50;
  for(int i = 0;i < (calibration_count +  skip_count);i++) {
    // WAIT FOR DATA READY.
    while (!IMU.gyroscopeAvailable()) ;
    if (i < skip_count) continue;
   
    // READ AND SUM SENSOR DATA TO CACLCULATE AVERAGE.
    IMU.readGyroscope(gyroscope_x, gyroscope_y, gyroscope_z);
   
    sum_x += gyroscope_x;
    sum_y += gyroscope_y;
    sum_z += gyroscope_z;
  }
  average_gyroscope_x  = (sum_x / calibration_count);
  average_gyroscope_y  = (sum_y / calibration_count);
  average_gyroscope_z  = (sum_z / calibration_count);
 
  n_average_gyroscope_x = average_gyroscope_x * N;
  n_average_gyroscope_y = average_gyroscope_y * N;
  n_average_gyroscope_z = average_gyroscope_z * N;

  Serial.print("average_gyroscope: ");
  Serial.print(average_gyroscope_x);
  Serial.print('\t');
  Serial.print(average_gyroscope_y);
  Serial.print('\t');
  Serial.println(average_gyroscope_z);
}

//
// 내장 LED를 켜거나 끈다.
//
int LED_STATE = LOW;
void turn_led_on() {
  if (LED_STATE == LOW) {
    LED_STATE = HIGH;
    digitalWrite(LED_BUILTIN, LED_STATE);
  }
}

void turn_led_off() {
  if (LED_STATE == HIGH) {
    LED_STATE = LOW;
    digitalWrite(LED_BUILTIN, LED_STATE);
  }
}

void toggle_led() {
  LED_STATE = LED_STATE == HIGH ? LOW : HIGH;
  digitalWrite(LED_BUILTIN, LED_STATE);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  turn_led_on();
  Serial.begin(115200);
  while (!Serial) {
    delay(50);
    toggle_led();
    delay(50);
    toggle_led();
  }
  Serial.println("Started");
  toggle_led();
  delay(100);
  toggle_led();
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
 
  toggle_led();
  delay(100);
  toggle_led();
  Serial.print("Gyroscope sample rate = ");
  Serial.print(IMU.gyroscopeSampleRate());
  Serial.println(" Hz");
  calibrate_gyro_sensor();
  last_gyro_time = millis();
  last_advertised_time = last_gyro_time;
  toggle_led();

  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

   BLE.setLocalName("Tracker");
   BLE.setAdvertisedService(GYROSCOPE_ADVERTISING_SERVICE);
   GYROSCOPE_ADVERTISING_SERVICE.addCharacteristic(ANGLE_X_CHARACTERISTIC);
   GYROSCOPE_ADVERTISING_SERVICE.addCharacteristic(ANGLE_Y_CHARACTERISTIC);
   GYROSCOPE_ADVERTISING_SERVICE.addCharacteristic(ANGLE_Z_CHARACTERISTIC);
   BLE.addService(GYROSCOPE_ADVERTISING_SERVICE);
   write_values(0, 0, 0);
   BLE.advertise();

   Serial.println("Bluetooth device active, waiting for connections...");
}

void write_values(int x, int y, int z) {
  ANGLE_X_CHARACTERISTIC.writeValue(String(x));
  ANGLE_Y_CHARACTERISTIC.writeValue(String(y));
  ANGLE_Z_CHARACTERISTIC.writeValue(String(z));
  Serial.print("angle: \t");
  Serial.print(x);
  Serial.print("\t");
  Serial.print(y);
  Serial.print("\t");
  Serial.println(z);
}


void loop() {
  // BLE.central 을 가져온다.
  BLEDevice central = BLE.central();
  if (!IMU.gyroscopeAvailable()) return;

  IMU.readGyroscope(x, y, z);
  long now = millis();
  long delta_t =  now - last_gyro_time;
  last_gyro_time = now;

  //
  // 각도의 변화량(degree) = gyroscope(degrees/second) * delta_t(millisecond) / 1000
  //
  // 아래와 같이 매 Tick마다 계산을 해도 되지만 N개 단위로 모아서 한꺼번에 계산을 해보기로 한다.
  //  double delta_x = ((double)x - average_gyroscope_x) * delta_t / 1000.0;
  //  int angle_x = angle_x + (int)delta_x;

  // N개 단위로 모아서 계산하기
  // 1. 센서의 값을 누적한다.
  accumulated_x = accumulated_x + x;
  accumulated_y = accumulated_y + y;
  accumulated_z = accumulated_z + z;
  accumulate_count++;
 
  // N개 단위로 모아서 계산하기
  // 2. N개 모였을 떄
  if (accumulate_count % N/*몇 개를 모을까*/ == 0) {
    // N개 단위로 모아서 계산하기
    // 3. 마지막으로 계산한 이후 시간을 구하고.
    //    각도를 구한다.
    //    각도(degree) = 마지막 각도(degree) + 각도의 변화량(degree)
    //                = 마지막 각도(degree) + (누적자이로스코프값(degrees/second) - N * 초기평균자이로스코프값(degrees/second)) * 누적시간(millisecond) / 1000
    long time_elapsed = now - last_advertised_time;
    double accumulated_delta_x = 0, accumulated_delta_y = 0, accumulated_delta_z = 0;
    accumulated_delta_x = (accumulated_x - n_average_gyroscope_x) * (time_elapsed); // / 1000.0;
    accumulated_delta_y = (accumulated_y - n_average_gyroscope_y) * (time_elapsed); // / 1000.0;
    accumulated_delta_z = (accumulated_z - n_average_gyroscope_y) * (time_elapsed); // / 1000.0;
    fixed_x = fixed_x + ((int)accumulated_delta_x) / 4000; // 시간의 단위를 맞추기 위해 1000으로 나누는 것은 정수로 바꾼 다음에...
    fixed_y = fixed_y + ((int)accumulated_delta_y) / 4000; // 좌우로 90도를 돌려보면  +,- 400도 정도까지 간다. 그래서 일단 4로 한번더 나눠버린다.
    fixed_z = fixed_z + ((int)accumulated_delta_z) / 4000;

    last_advertised_time = now;
    accumulate_count = 0;
    accumulated_x = 0.0; accumulated_y = 0.0; accumulated_z = 0.0;
    if (central && central.connected()) {
      turn_led_on();
      write_values(fixed_x, fixed_y, fixed_z);
    } else {
      turn_led_off();
    }
  }
 }