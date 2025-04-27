from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
import shutil
import cv2
import base64
import requests
import os

app = FastAPI()

# Serve the HTML form at the root endpoint
@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open("static/index.html", "r") as f:
        return f.read()

# Handle file upload and other form inputs
@app.post("/generate")
async def generate_title_and_description(
    file: UploadFile = File(...),
    frame_no: int = Form(...),
    clickbait: str = Form(...)
):
    # Save the uploaded file temporarily
    video_path = f"temp_video_{file.filename}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract frame from video
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return {"error": f"Cannot read frame {frame_no}"}

    # Encode frame to base64
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    b64 = base64.b64encode(buf).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    # Generate title and description based on clickbait choice
    title_prompt = (
        "Generate a catchy, engaging YouTube title with some excitement—use words like 'incredible', 'amazing', 'you won’t believe'. "
        "Keep it under 15 words, specific to the game/app/place, without excessive hype."
    ) if clickbait in ['y', 'yes'] else (
        "Generate a concise, engaging YouTube title specific to the game/app/place, under 15 words, without excessive hype."
    )

    # Title payload
    title_payload = {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": title_prompt},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }]
    }

    # Description payload
    desc_payload = {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Write a first-person, moderately engaging YouTube description based on this image:\n"
                    "- Use 'I', 'me', 'my'. Add some curiosity: 'You won’t believe what happened next', 'I had to share this with you', etc.\n"
                    "- Include 4–6 relevant hashtags about the game/app/place.\n"
                    "- Provide 3–5 timestamps, each on its own line formatted 'MM:SS - Event'.\n"
                    "- Avoid UI details like round numbers or buy phases.\n"
                    "Example:\n"
                    "\"I just pulled off something crazy in Valorant—check this out!\"\n"
                    "#Valorant #GamerLife #EpicPlays #GameHighlights\n\n"
                    "Timestamps:\n"
                    "00:00 - Intense Start\n"
                    "00:30 - First Blood\n"
                    "01:15 - Clutch Moment\n"
                    "Now generate:"
                )},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }]
    }

    # API key & headers for OpenRouter API
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }

    # Send title request
    tresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=title_payload)
    if tresp.status_code >= 400:
        return {"error": f"Title generation failed: {tresp.json()}"}
    title_json = tresp.json()

    # Send description request
    dresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=desc_payload)
    if dresp.status_code >= 400:
        return {"error": f"Description generation failed: {dresp.json()}"}
    desc_json = dresp.json()

    # Parse and return results
    title = title_json["choices"][0]["message"]["content"].strip()
    description = desc_json["choices"][0]["message"]["content"].strip()

    return {
        "title": title,
        "description": description
    }
