const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const result = document.getElementById('result');
const ctx = canvas.getContext('2d');

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
}

function sendFrameOnce() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.blob())
        .then(imageBlob => {
            const url = URL.createObjectURL(imageBlob);
            result.src = url;
            result.style.display = 'block';

            // скрываем обработанное изображение через 500 мс
            setTimeout(() => {
                result.style.display = 'none';
            }, 500);
        });
    }, 'image/jpeg');
}

function changeShirt() {
    fetch('/change_shirt', { method: 'POST' })
        .then(() => sendFrameOnce());
}

function changePants() {
    fetch('/change_pants', { method: 'POST' })
        .then(() => sendFrameOnce());
}

startCamera();
