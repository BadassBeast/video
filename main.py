from fastapi import FastAPI
from pydantic import BaseModel
import cv2
import base64
import requests
import json
import os

app = FastAPI()

class VideoRequest(BaseModel):
    video_path: str
    frame_no: int
    clickbait_choice: str

@app.post("/generate")
async def generate(request: VideoRequest):
    video_path = request.video_path
    frame_no = request.frame_no
    clickbait_choice = request.clickbait_choice

    if not os.path.exists(video_path):
        return {"error": "File not found"}

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return {"error": f"Cannot read frame {frame_no}"}

    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    b64 = base64.b64encode(buf).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    title_prompt = "Generate a catchy, engaging YouTube title..."  # adjust this based on clickbait_choice

    title_payload = {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "messages": [{"role": "user", "content": [{"type": "text", "text": title_prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}]
    }

    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }

    tresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=title_payload)
    if tresp.status_code >= 400:
        return {"error": tresp.json()}
    title_json = tresp.json()

    title = title_json["choices"][0]["message"]["content"].strip()

    # Similar for description generation

    return {"title": title, "description": description}
