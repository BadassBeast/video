from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2, requests, json, base64, os
from io import BytesIO

app = FastAPI()

# Allow all CORS for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/generate", response_class=JSONResponse)
async def generate(
    file: UploadFile,
    frame_no: int = Form(...),
    clickbait: str = Form(...)
):
    # Save the uploaded video temporarily
    video_path = f"temp_{file.filename}"
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract frame
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    os.remove(video_path)

    if not ret:
        return {"error": f"Cannot read frame {frame_no}"}

    # Encode frame to base64
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    b64 = base64.b64encode(buf).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    # Prepare prompts
    title_prompt = (
        "Generate a catchy, engaging YouTube title with some excitement—use words like 'incredible', 'amazing', 'you won’t believe'. "
        "Keep it under 15 words, specific to the game/app/place, without excessive hype."
    ) if clickbait.lower() in ['y', 'yes'] else (
        "Generate a concise, engaging YouTube title specific to the game/app/place, under 15 words, without excessive hype."
    )

    # Payloads
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
                    "Now generate:"
                )},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }]
    }

    # Headers
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    # Request title
    tresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=title_payload)
    if tresp.status_code >= 400:
        return {"error": tresp.json()}

    # Request description
    dresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=desc_payload)
    if dresp.status_code >= 400:
        return {"error": dresp.json()}

    # Parse
    title_json = tresp.json()
    desc_json = dresp.json()

    title = title_json["choices"][0]["message"]["content"].strip()
    description = desc_json["choices"][0]["message"]["content"].strip()

    return {
        "title": title,
        "description": description,
        "title_tokens": title_json.get("usage", {}),
        "desc_tokens": desc_json.get("usage", {})
    }
