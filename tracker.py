import asyncio
import cv2
import numpy as np
import serial
import types
from threading import Thread, Event


def gstreamer_pipeline(
    sensor_id=0,
    sensor_mode=3,
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d sensor-mode=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            sensor_mode,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
)


class TrackerCamera:
    __ENCODE_PARAM = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    __PWM_X = 32
    __PWM_Z = 35

    __CAMERA_LEFT = 0
    __CAMERA_RIGHT = 1
    __LEFT = 'left'
    __RIGHT = 'right'
    __AXIS_X = 'x'
    __AXIS_Z = 'z'

    def __init__(self):
        self.__capture_thread_event = None
        self.__capture_thread = None
        self.__sources = {
            self.__LEFT: None,
            self.__RIGHT: None
        }
        self.__images = {
            self.__LEFT: None,
            self.__RIGHT: None
        }
        self.__coordinates = {
            self.__LEFT: 0,
            self.__RIGHT: 0
        }
        self.__serial_port = None

    def init_serial(self):
        self.__serial_port = serial.Serial(
            port="/dev/ttyTHS1",
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        print('SERIAL PORT OPENED')
        print(self.__serial_port)

    def __write_line(self, __line : str):
        if self.__serial_port is not None:
            if __line.endswith('\n'):
                print("WRITING TO SERIAL: " + __line)
                print("WRITING TO SERIAL: " + __line)
                self.__serial_port.write(__line.encode())
            else:
                print("WRITING TO SERIAL: " + __line + '\n')
                self.__serial_port.write(__line.encode())
                self.__serial_port.write(b'\n')

    def release_serial(self):
        self.__serial_port.close()
        self.__serial_port = None

    def init_video(self):
        #self.__sources[self.__LEFT] = cv2.VideoCapture(0)
        #self.__sources[self.__RIGHT] = cv2.VideoCapture(1)
        self.__sources[self.__LEFT] = cv2.VideoCapture(
            gstreamer_pipeline(
                sensor_id=0,
                # sensor_mode=3,
                # flip_method=0,
                # display_height=540,
                # display_width=960,
            )
        )
        self.__sources[self.__RIGHT] = cv2.VideoCapture(
            gstreamer_pipeline(
                sensor_id=1,
                # sensor_mode=3,
                # flip_method=0,
                # framerate=30,
                # display_height=540,
                # display_width=960,
            )
        )
        print(self.__sources)


    def release_video(self):
        if self.__sources[self.__LEFT] is not None:
            self.__sources[self.__LEFT].release()
        if self.__sources[self.__RIGHT] is not None:
            self.__sources[self.__RIGHT].release()

    def release(self):
        self.release_video()
        self.release_serial()

    # x 축 각도
    # z 축 각도
    #   int : -90 ~ 90(또는 0 ~ 180)
    def rotate_to(self, axis : str, angle : int):
        if axis == 'c':
            self.__write_line('x90')
            self.__write_line('z90')
        elif axis == 'x' or axis == 'z':
            __line = axis + str(angle)
            self.__write_line(__line)

    # x 축 각도 증분
    # z 축 각도 증분
    #   int
    def rotate(self, delta_x : int, delta_z : int):
        pass

    def get_coordinates(self):
        return self.__coordinates

    def process_serial_input(self):
        __result = []
        __line = self.__serial_port.readline().decode()
        print("READ FROM SERIAL: " + __line)
        __axis = None
        __angle = 0
        for c in __line:
            if c == 'X' or c == 'Z':
                if __axis is not None:
                    __result.append((__axis, __angle))
                __axis = c
                __angle = 0
                continue
            if __axis is not None:
                if c.isdigit():
                    __angle = __angle * 10 + ord(c) - ord('0')
                else:
                    if c != 'X' or c != 'Z':
                        if __axis is not None:
                            __result.append((__axis, __angle))
                        __axis = None
                        __angle = 0
                    else:
                        if __axis is not None:
                            __result.append((__axis, __angle))
                        __axis = c
                        __angle = 0
        for axis, angle in __result:
            self.__coordinates[axis] = angle
            # TODO FIRE ANGEL CHANGED EVENT HERE

    #
    # VIDEO CAPTURE
    #
    async def __capture_video(self, video_capture):
        ret, frame = video_capture.read()
        result, frame = cv2.imencode('.jpg', frame, self.__ENCODE_PARAM)
        return np.array(frame).tobytes()

    async def __do_capture(self):
        __result = await asyncio.gather(
            self.__capture_video(self.__sources[self.__LEFT]),
            self.__capture_video(self.__sources[self.__RIGHT])
        )
        return __result

    def __capture_thread_main(self):
        self.init_video()
        self.init_serial()
        __loop = asyncio.new_event_loop()
        __count = 0
        while True:
            if self.__capture_thread_event is not None and self.__capture_thread_event.isSet():
                break
            # 시리얼 포트을 먼저 처리하자.
            # 현재는 두 축의 각도만 준다.
            self.process_serial_input()
            # Async COROUTINE __do_capture()를 호출하여 캡처
            capture_result = __loop.run_until_complete(self.__do_capture())
            __count = __count + 1
            # TODO
            #  UPDATE IMAGE AND FIRE EVENT
            self.__images[self.__LEFT] = capture_result[0]
            self.__images[self.__RIGHT] = capture_result[1]
            print("ITERATION: " + str(__count))
            print(capture_result)
            if __count > 3:
                self.stop_capture()
        __loop.close()

    def start_capture(self):
        self.__capture_thread_event = Event()
        self.__capture_thread = Thread(target=self.__capture_thread_main, )
        self.__capture_thread.start()

    def stop_capture(self):
        self.__capture_thread_event.set()

    def wait_for_capture_thread(self):
        self.__capture_thread.join()

    #
    # channel : string : x | y
    #
    def get_images(self):
        return self.__images[self.__LEFT], self.__images[self.__RIGHT]

    def init_pwm(self):
        pass

    def release_pwm(self):
        pass


if __name__ == '__main__':
    tracker = TrackerCamera()
    tracker.init_video()
    tracker.start_capture()
    tracker.wait_for_capture_thread()