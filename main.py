from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
import io
import os

app = Flask(__name__)

# Загрузка одежды
shirt_images = [cv2.imread(f"media/shirts/{i}.png", cv2.IMREAD_UNCHANGED) for i in range(1, 4)]
pants_images = [cv2.imread(f"media/pants/{i}.png", cv2.IMREAD_UNCHANGED) for i in range(1, 4)]

shirt_index = 0
pants_index = 0

# Установленные размеры одежды (можно изменить здесь)
shirt_scale = 1.3  # Масштаб рубашки (например, 1.5 — в 1.5 раза больше стандартного)
pants_scale = 1.7  # Масштаб штанов

# Каскад для лица
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def blend_images(bg, overlay, x, y):
    if overlay.shape[2] != 4:
        return bg
    h, w = overlay.shape[:2]
    if y + h > bg.shape[0] or x + w > bg.shape[1] or x < 0 or y < 0:
        return bg

    alpha = overlay[:, :, 3] / 255.0
    for c in range(3):
        bg[y:y+h, x:x+w, c] = (
            (1 - alpha) * bg[y:y+h, x:x+w, c] +
            alpha * overlay[:, :, c]
        )
    return bg


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    global shirt_index, pants_index, shirt_scale, pants_scale
    file = request.files['frame'].read()
    npimg = np.frombuffer(file, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    if len(faces) > 0:
        x, y, w, h = faces[0]

        # Наложение рубашки с фиксированным размером
        shirt = shirt_images[shirt_index]
        if shirt is not None:
            shirt_width = int(w * 2.2 * shirt_scale)  # ширина рубашки с масштабом
            shirt_height = int(shirt.shape[0] * shirt_width / shirt.shape[1])  # пропорциональная высота
            shirt_resized = cv2.resize(shirt, (shirt_width, shirt_height))

            # Смещение по оси X и Y для более точного наложения
            shirt_x = x - int(w * 0.8)  # немного сдвигаем по X
            shirt_y = y + int(h * 1)  # немного сдвигаем по Y
            frame = blend_images(frame, shirt_resized, shirt_x, shirt_y)

        # Наложение штанов с фиксированным размером
        # Наложение штанов с исправленной высотой
        pants = pants_images[pants_index]
        if pants is not None:
            # Масштабируем штаны
            pants_width = int(w * 2.2 * pants_scale)  # ширина штанов с масштабом
            pants_height = int(pants.shape[0] * pants_width / pants.shape[1])  # пропорциональная высота
            pants_resized = cv2.resize(pants, (pants_width, pants_height))

            # Устанавливаем позицию штанов, чтобы они располагались ниже рубашки
            pants_x = x - int(w * 1.3)  # Сдвиг по X для штанов (для лучшего выравнивания по телу)
            
            # Для высоты штанов корректируем смещение относительно лица
            pants_y = y + int(h * 3.7)  # Размещение ниже лица и рубашки (можно подкорректировать это значение)

            # Наложение штанов на изображение
            frame = blend_images(frame, pants_resized, pants_x, pants_y)


    _, buffer = cv2.imencode('.jpg', frame)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')


# Смена рубашки
@app.route('/change_shirt', methods=['POST'])
def change_shirt():
    global shirt_index
    shirt_index = (shirt_index + 1) % len(shirt_images)
    return '', 204

# Смена штанов
@app.route('/change_pants', methods=['POST'])
def change_pants():
    global pants_index
    pants_index = (pants_index + 1) % len(pants_images)
    return '', 204


if __name__ == '__main__':
    app.run(debug=True)
