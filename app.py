from flask import Flask
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import Response
from subprocess import call
from flask_socketio import SocketIO, send
import tracker

app = Flask(__name__)
app.secret_key = "tracker"
socket_io = SocketIO(app)


@app.route('/')
def hello_world():  # put application's code here
    # return 'Hello World2!'
    return render_template('index.html')


@app.route('/status')
def get_status():  # put application's code here
    uptime, captured_frames = tracker.get_status()
    return '{ uptime : ' + str(uptime) + ', frames : ' + str(captured_frames) + '}'

@app.route('/hello/<name>')
def say_hello2(name: str):  # put application's code here
    return f'Hello World, {name}!'


def __generator_for_image(image_blob):
    yield image_blob


def __send_image(image_blob, content_type='image/jpeg'):
    return Response(__generator_for_image(image_blob), content_type=content_type)


def __send_image_not_working(image_blob, content_type='image/jpeg'):
    __response = make_response(image_blob)
    __response.headers.set('ContentType', content_type)
    return __response


@app.route('/camera/images/<channel>')
def get_image(channel: str):  # put application's code here
    if channel == 'left' or channel == 'right':
        __images = tracker.get_images()
        __image = __images[channel]
        if __image is None:
            return make_response("NOT FOUND: " + channel, 404)
        else:
            return __send_image(__image)
    return make_response("BAD REQUEST: " + channel, 400)


@app.route('/camera/coordinates/')
def get_coordinates():  # put application's code here
    __coordinates = tracker.get_coordinates()
    print("get_coordinates():" + str(__coordinates))
    return jsonify(__coordinates)


@app.route('/camera/coordinates/<axis>/<angle>')
def set_coordinates(axis: str, angle: int):  # put application's code here
    print('set_coordinates(): axis=' + axis + ", angle=" + str(angle))
    tracker.rotate_to(axis, angle)
    return get_coordinates()


if __name__ == '__main__':
    tracker = tracker.TrackerCamera()
    ## start_capture()에서 모두 실행함.
    ##tracker.init_video()
    ##tracker.init_serial()

    tracker.start_capture()

    # app.run()
    # socket_io.run(app, debug=True, port=9999)
    #
    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    # socket_io.run(app, host="0.0.0.0", debug=True, port=8443, ssl_context=('cert.pem', 'key.pem'))
    socket_io.run(app, host="0.0.0.0",
                  # debug=True,
                  port=8443,
                  # ssl_context=('cert.pem', 'key.pem')
                  )
    print("WAITING CAPTURE THREAD")
    tracker.wait_for_capture_thread()
