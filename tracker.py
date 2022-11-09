import cv2
import numpy as np
import asyncio
from threading import Thread, Event

LEFT_IMAGE, RIGHT_IMAGE = None, None
STOP_CAPTURE_EVENT = None


def init_camera():
    video_capture_left = cv2.VideoCapture(0)
    video_capture_right = cv2.VideoCapture(1)
    return video_capture_left, video_capture_right


def release_camera(video_capture_left, video_capture_right):
    video_capture_left.release()
    video_capture_right.release()


async def capture_async(video_capture, encode_param):
    ret, frame = video_capture.read()
    result, frame = cv2.imencode('.jpg', frame, encode_param)
    return np.array(frame).tobytes()


def generate_capture(video_capture_left, video_capture_right):
    global STOP_CAPTURE_EVENT
    STOP_CAPTURE_EVENT = Event()
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    loop = asyncio.new_event_loop()
    while True:
        if STOP_CAPTURE_EVENT.isSet():
            break
        left_blob, right_blob = loop.run_until_complete(
            asyncio.gather(
                        capture_async(video_capture_left, encode_param),
                        capture_async(video_capture_right, encode_param)
                    )
        )
        yield left_blob, right_blob
    loop.close()


def capture(video_capture_left, video_capture_right):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    loop = asyncio.new_event_loop()
    left_blob, right_blob = loop.run_until_complete(
        asyncio.gather(
                    capture_async(video_capture_left, encode_param),
                    capture_async(video_capture_right, encode_param)
                )
    )
    loop.close()
    return left_blob, right_blob
#    return await asyncio.gather(
#        capture_async(video_capture_left, encode_param),
#        capture_async(video_capture_right, encode_param)
#    )


def get_images():
    return LEFT_IMAGE, RIGHT_IMAGE


def do_capture():
    global LEFT_IMAGE, RIGHT_IMAGE, STOP_CAPTURE_EVENT
    video_capture_left, video_capture_right = init_camera()
    while True:
        if STOP_CAPTURE_EVENT.is_set():
            break
        LEFT_IMAGE, RIGHT_IMAGE = capture(video_capture_left, video_capture_right)
    LEFT_IMAGE, right_image = None, None
    release_camera(video_capture_left, video_capture_right)


def create_capture_thread():
    global STOP_CAPTURE_EVENT
    STOP_CAPTURE_EVENT = Event()
    capture_tread = Thread(target=do_capture,)
    capture_tread.start()
    return capture_tread


def stop_capture():
    global STOP_CAPTURE_EVENT
    STOP_CAPTURE_EVENT.set()
