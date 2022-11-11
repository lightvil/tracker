from flask import Flask
from flask import make_response
from subprocess import call
from flask_socketio import SocketIO, send
import tracker


images = {'x': None, 'y': None}
angles = {'x': 0, 'y': 0}
app = Flask(__name__)
app.secret_key = "tracker"
socket_io = SocketIO(app)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World2!'


@app.route('/hello/<name>')
def say_hello2(name: str):  # put application's code here
    return f'Hello World, {name}!'


def send_image(image_blob, content_type='image/jpeg'):
    __response = make_response(image_blob)
    __response.headers.set('ContentType', content_type)
    return __response

@app.route('/camera/images/<channel>')
def get_image(channel: str):  # put application's code here
    left_image, right_image = tracker.get_images()
    if channel == 'left':
        if left_image is not None:
            return send_image(left_image)
        else:
            return make_response("NOT FOUND: " + channel, 404)
    elif channel == 'right':
        if right_image is not None:
            return send_image(right_image)
        else:
            return make_response("NOT FOUND: " + channel, 404)
    return make_response("BAD REQUEST: " + channel, 400)
    return f'Image Channel:{channel}!'


@app.route('/camera/axis/<axis>/')
def get_axis(axis: str):  # put application's code here
    angle = angles[axis]
    return f'Axis:{axis} => {angle}!'


@app.route('/camera/axis/move/<axis>/<angle>')
def rotate(axis: str, angle: int):  # put application's code here
    return f'Axis:{axis}, Angle::{angle}!'


if __name__ == '__main__':
    # app.run()
    tracker.create_capture_thread()
    socket_io.run(app, debug=True, port=9999)
    tracker.stop_capture_thread()

