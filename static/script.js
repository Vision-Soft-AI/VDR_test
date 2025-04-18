const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const result = document.getElementById('result');
const ctx = canvas.getContext('2d');

let isProcessing = false;
let lastUrl = null;

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1920, height: 1080 }  // Ограничиваем разрешение
    });
    video.srcObject = stream;
    video.onloadedmetadata = () => {
        video.play();
        requestAnimationFrame(processLoop);
    };
}

function processLoop() {
    if (!isProcessing) {
        sendFrameOnce();
    }
    requestAnimationFrame(processLoop); // вызываем снова, как только браузер готов
}

function sendFrameOnce() {
    isProcessing = true;

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
            if (lastUrl) {
                URL.revokeObjectURL(lastUrl);
            }
            lastUrl = URL.createObjectURL(imageBlob);
            result.src = lastUrl;
            result.style.display = 'block';
        })
        .finally(() => {
            isProcessing = false;
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
