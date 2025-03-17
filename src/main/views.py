from flask import Blueprint, flash, render_template, Response, stream_with_context, request, redirect, url_for
from flask_login import login_required, current_user
from src.account.forms import FormTwoFactor
import cv2
import numpy
import os
from datetime import datetime
import time
from src import celery

video = cv2.VideoCapture(0)
main = Blueprint("main", __name__)
out = None
start = 0
path = "/home/pi/LoginTest1/files"
is_recording = False

@celery.task
def video_stream():
    global is_recording, out, start 
    while True:
        ret, frame = video.read()
        if not ret:
            break;
        else:
            if not is_recording:
                record_start()
            if is_recording:
                last = datetime.now()
                delta = last - start
                cv2.putText(frame, last.strftime("%Y-%m-%d %H:%M:%S"), (20,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_4)
                out.write(frame)
                if int(delta.total_seconds()) > 30:
                    record_stop()
                    auto_delete()
            ret, buffer = cv2.imencode('.jpeg',frame)
            frame = buffer.tobytes()
            yield (b' --frame\r\n' b'Content-type: imgae/jpeg\r\n\r\n' + frame +b'\r\n')

def record_start():
    global is_recording, out, start, path
    if not is_recording:
        start = datetime.now()
        name = 'output_' + str(start.strftime("%Y-%m-%d_%H:%M:%S")) + '.avi'
        codec = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(os.path.join(path, name), codec, 20.0, (640, 480))
        is_recording = True
    return '', 204

def record_stop():
    global is_recording, out, start
    if is_recording:
        out.release()
        start = 0
        is_recording = False
    return '', 204

def auto_delete():
    global path
    now = time.time()
    for filename in os.listdir(path):
        timestamp = os.stat(os.path.join(path, filename)).st_mtime
        extime = now - 600
        if timestamp < extime:
            os.remove(os.path.join(path, filename))
            
def deviceTest():
    if video is None or not video.isOpened():
        return False
    else:
        return True

@main.route("/")
@login_required
def home():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    elif current_user.is_admin and not current_user.is_2FA_enabled:
        flash("You need to setup 2FA first!", "danger")
        return redirect(url_for("account.setup_2fa"))
    else:
        if deviceTest():
            status="Running"
        else:
            status="Error"
        return render_template("main/index.html", status=status)

@main.route("/camera")
@login_required
def camera():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    elif current_user.is_admin and not current_user.is_2FA_enabled:
        flash("You need to setup 2FA first!", "danger")
        return redirect(url_for("account.setup_2fa"))
    else:
        return render_template('main/camera.html')

@main.route("/settings")
@login_required
def settings():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    elif current_user.is_admin and not current_user.is_2FA_enabled:
        flash("You need to setup 2FA first!", "danger")
        return redirect(url_for("account.setup_2fa"))
    else:
        return render_template('main/settings.html')

@main.route('/video_feed')
@login_required
def video_feed():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route("/browse")
def file():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    elif current_user.is_admin and not current_user.is_2FA_enabled:
        flash("You need to setup 2FA first!", "danger")
        return redirect(url_for("account.setup_2fa"))
    else:    
        return render_template('main/file.html')
