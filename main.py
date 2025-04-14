from flask import Flask, render_template, Response, request
import cv2
import os
import numpy as np

app = Flask(__name__)

shirt_images = ["media/shirts/1.png", "media/shirts/2.png", "media/shirts/3.png"]
pants_images = ["media/pants/1.png", "media/pants/2.png", "media/pants/3.png"]

shirt_index = 0
pants_index = 0

cap = cv2.VideoCapture(1)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

shirt_scale = 1.2
pants_scale = 0.8

def blend_images(background, overlay):
    if background.shape[0] != overlay.shape[0] or background.shape[1] != overlay.shape[1]:
        overlay = cv2.resize(overlay, (background.shape[1], background.shape[0]))

    if overlay.shape[2] == 4:
        overlay_rgb = overlay[:, :, :3]
        overlay_alpha = overlay[:, :, 3] / 255.0
    else:
        overlay_rgb = overlay
        overlay_alpha = np.ones((overlay.shape[0], overlay.shape[1]))

    alpha_3channel = np.stack([overlay_alpha] * 3, axis=-1)
    blended = (background * (1 - alpha_3channel) + overlay_rgb * alpha_3channel).astype(np.uint8)
    return blended

def generate_frames():
    global shirt_index, pants_index
    while True:
        success, frame = cap.read()
        if not success:
            break

        shirt_img = cv2.imread(shirt_images[shirt_index], cv2.IMREAD_UNCHANGED)
        pants_img = cv2.imread(pants_images[pants_index], cv2.IMREAD_UNCHANGED)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Shirt
            shirt_h, shirt_w = shirt_img.shape[:2]
            shirt_width = int(shirt_scale * 3 * w)
            shirt_height = int(shirt_width * shirt_h / shirt_w)
            x1 = max(0, x - int(shirt_scale * w))
            y1 = y + h
            x2 = min(frame.shape[1], x1 + shirt_width)
            y2 = min(frame.shape[0], y1 + shirt_height)

            if x2 - x1 > 0 and y2 - y1 > 0:
                resized_shirt = cv2.resize(shirt_img, (x2 - x1, y2 - y1))
                roi = frame[y1:y2, x1:x2]
                frame[y1:y2, x1:x2] = blend_images(roi, resized_shirt)

            # Pants
            pants_h, pants_w = pants_img.shape[:2]
            pants_width = int(pants_scale * 3 * w)
            pants_height = int(pants_width * pants_h / pants_w)
            px1 = x - int(pants_scale * w)
            py1 = y2
            px2 = min(frame.shape[1], px1 + pants_width)
            py2 = min(frame.shape[0], py1 + pants_height)

            if px2 - px1 > 0 and py2 - py1 > 0:
                resized_pants = cv2.resize(pants_img, (px2 - px1, py2 - py1))
                roi_pants = frame[py1:py2, px1:px2]
                frame[py1:py2, px1:px2] = blend_images(roi_pants, resized_pants)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/change_shirt', methods=['POST'])
def change_shirt():
    global shirt_index
    shirt_index = (shirt_index + 1) % len(shirt_images)
    return ('', 204)

@app.route('/change_pants', methods=['POST'])
def change_pants():
    global pants_index
    pants_index = (pants_index + 1) % len(pants_images)
    return ('', 204)

if __name__ == '__main__':
    app.run(debug=True)