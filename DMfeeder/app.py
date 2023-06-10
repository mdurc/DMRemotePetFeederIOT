from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory
import RPi.GPIO as GPIO
import time
import picamera
import socket
import io
import threading
from time import sleep
import os
import subprocess
import argparse
import cv2

app = Flask(__name__,template_folder='DMfeeder/templates', static_url_path='DMfeeder/static')

UPLOAD_DIRECTORY = 'DMfeeder'

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)


GPIO.setup(24, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)
GPIO.setup(14, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)


StepCount= 8

seq= [[1,1,0,0],
        [0,1,1,0],
        [0,0,1,1],
        [1,0,0,1],
    ]



rotationNeeded=0
rotationCount=200


def backward(motor):
    if motor == 1:
        ENA = 17
        IN1=27
        IN2 = 22
        IN3 = 20
        IN4 = 21
    else:
        ENA = 17
        IN1 = 24
        IN2 = 25
        IN3 = 14
        IN4 = 15
    
    ControlPin = [IN1,IN2,IN3,IN4]
    ControlPin_r = [IN4,IN3,IN2,IN1]
    
    GPIO.output(ENA, 1)
    for i in range (rotationCount):
        for fullStep in range(4):
            for pin in range(4):
                GPIO.output(ControlPin[pin], seq[fullStep][pin])
                sleep(0.001)

    GPIO.output(ENA, 0)

def forward(motor):
    if motor == 1:
        ENA = 17
        IN1=27
        IN2 = 22
        IN3 = 20
        IN4 = 21
    else:
        ENA = 17
        IN1 = 24
        IN2 = 25
        IN3 = 14
        IN4 = 15
    
    ControlPin = [IN1,IN2,IN3,IN4]
    ControlPin_r = [IN4,IN3,IN2,IN1]
    
    GPIO.output(ENA, 1)
    for i in range (rotationCount):
        for fullStep in range(4):
            for pin in range(4):
                GPIO.output(ControlPin_r[pin], seq[fullStep][pin])
                sleep(0.001)

    GPIO.output(ENA, 0)

@app.route('/run_motor1', methods=['POST'])
def run_motor1():
    forward(1)
    forward(1)
    forward(1)
    print('Successfully Ran the Food')
    return ''

@app.route('/run_motor2', methods=['POST'])
def run_motor2():
    forward(2)
    sleep(1)
    backward(2)
    print('Successfully Ran the Water')
    return ''


def gen(camera_type):
    if camera_type == 1:
        camera = picamera.PiCamera()
    	camera.resolution = (640, 480)
    	camera.framerate = 30
    	stream = io.BytesIO()

    	for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
        	stream.seek(0)
        	yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n')

        stream.seek(0)
        stream.truncate()
    else:
        camera = cv2.VideoCapture(0)
    	while True:
        	success, frame = camera.read()
        	if not success:
            	    break
        	else:
            	    ret, buffer = cv2.imencode('.jpg', frame)
            	    frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    print('Video Feed is Live')
    return Response(gen(camera_type), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    # Render the HTML template
    return render_template('web.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['audio']
    filename = request.args.get('filename')
    file_path= os.path.join(UPLOAD_DIRECTORY, filename)
    file.save(file_path)
    subprocess.call(['cvlc',file_path])
    print('Audio File Saved')
    return 'Audio file saved.'


# Run the web application
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--picamera', type=int, default=0, help='Use PiCamera if set to 1, otherwise use USB camera')
    args = parser.parse_args()
    app.run(host='0.0.0.0',debug=True, threaded=True)

