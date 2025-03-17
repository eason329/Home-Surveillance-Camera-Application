from flask import Blueprint, render_template, Response, stream_with_context, request, redirect, url_for
from flask_login import login_required, current_user
from src.account.forms import FormTwoFactor
import cv2
import numpy

video = cv2.VideoCapture(0)
main = Blueprint("main", __name__)

def video_stream():
    while True:
        ret, frame = video.read()
        if not ret:
            break;
        else:
            ret, buffer = cv2.imencode('.jpeg',frame)
            frame = buffer.tobytes()
            yield (b' --frame\r\n' b'Content-type: imgae/jpeg\r\n\r\n' + frame +b'\r\n')

@main.route("/")
@login_required
def home():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    else:
        return render_template("main/index.html")

@main.route("/camera")
@login_required
def camera():
    return render_template('main/camera.html')

@main.route("/settings")
@login_required
def settings():
    if current_user.is_2FA_enabled and not current_user.is_2FA_verified:
        return redirect(url_for("account.verify_2fa"))
    else:
        return render_template('main/settings.html')

@main.route('/video_feed')
@login_required
def video_feed():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route("/browse")
def file():    
    return render_template('main/file.html')