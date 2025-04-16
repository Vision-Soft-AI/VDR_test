from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
import io

app = Flask(__name__)

# Загрузка одежды
shirt_images = [cv2.imread(f"media/shirts/{i}.png", cv2.IMREAD_UNCHANGED) for i in range(1, 4)]
pants_images = [cv2.imread(f"media/pants/{i}.png", cv2.IMREAD_UNCHANGED) for i in range(1, 4)]

shirt_index = 0
pants_index = 0

# Каскад для лица
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def blend_images(bg, overlay, x, y):
    h, w = overlay.shape[:2]
    if y + h > bg.shape[0] or x + w > bg.shape[1] or x < 0 or y < 0:
        return bg
    alpha = overlay[:, :, 3] / 255.0
    for c in range(3):
        bg[y:y+h, x:x+w, c] = (1 - alpha) * bg[y:y+h, x:x+w, c] + alpha * overlay[:, :, c]
    return bg

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global shirt_index, pants_index
    file = request.files['frame'].read()
    npimg = np.frombuffer(file, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    if len(faces) > 0:
        x, y, w, h = faces[0]

        # Рубашка
        shirt = shirt_images[shirt_index]
        shirt_width = int(w * 2.2)
        shirt_height = int(shirt.shape[0] * shirt_width / shirt.shape[1])
        shirt_resized = cv2.resize(shirt, (shirt_width, shirt_height))
        frame = blend_images(frame, shirt_resized, x - int(w * 0.6), y + h)

        # Штаны
        pants = pants_images[pants_index]
        pants_width = int(w * 2.2)
        pants_height = int(pants.shape[0] * pants_width / pants.shape[1])
        pants_resized = cv2.resize(pants, (pants_width, pants_height))
        frame = blend_images(frame, pants_resized, x - int(w * 0.6), y + h + shirt_height)

    _, buffer = cv2.imencode('.jpg', frame)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')

@app.route('/change_shirt', methods=['POST'])
def change_shirt():
    global shirt_index
    shirt_index = (shirt_index + 1) % len(shirt_images)
    return '', 204

@app.route('/change_pants', methods=['POST'])
def change_pants():
    global pants_index
    pants_index = (pants_index + 1) % len(pants_images)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
