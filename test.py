import asyncio
import cv2
import numpy as np
import types
from threading import Thread, Event


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
        self.__images = {
            self.__LEFT: 0,
            self.__RIGHT: 0
        }

    def init_video(self):
        self.__sources[self.__LEFT] = cv2.VideoCapture(0)
        self.__sources[self.__RIGHT] = cv2.VideoCapture(1)

    async def __capture_video(self, video_capture):
        ret, frame = video_capture.read()
        result, frame = cv2.imencode('.jpg', frame, self.__ENCODE_PARAM)
        return np.array(frame).tobytes()

    async def __do_capture(self):
        __result = await asyncio.gather(
            self.__capture_video('LEFT'), self.__capture_video('RIGHT')
        )
        return __result

    def __capture_thread_main(self):
        self.init_video()
        __loop = asyncio.new_event_loop()
        __count = 0
        while True:
            if self.__capture_thread_event is not None and self.__capture_thread_event.isSet():
                break
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
    def get_image(self, channel):
        self.__images[channel]


    def init_pwm(self):
        pass

    def release_pwm(self):
        pass

    # x 축 각도
    # z 축 각도
    #   int : -90 ~ 90(또는 0 ~ 180)
    def rotate_to(self, x : int, z : int):
        pass

    # x 축 각도 증분
    # z 축 각도 증분
    #   int
    def rotate(self, delta_x : int, delta_z : int):
        pass

if __name__ == '__main__':
    tracker = TrackerCamera()
    tracker.init_video()
    tracker.start_capture()
    tracker.wait_for_capture_thread()