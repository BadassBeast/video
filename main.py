# main.py

import cv2, requests, json, base64, os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS (optional but useful)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter API key
OPENROUTER_API_KEY = "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"

@app.post("/generate")
async def generate_title_description(
    video: UploadFile = File(...),
    frame_no: int = Form(...),
    clickbait: str = Form(...)
):
    # === 1) Save uploaded video temporarily
    temp_path = f"temp_{video.filename}"
    with open(temp_path, "wb") as f:
        f.write(await video.read())

    # === 2) Extract frame
    cap = cv2.VideoCapture(temp_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    os.remove(temp_path)
    if not ret:
        return JSONResponse(status_code=400, content={"error": f"Cannot read frame {frame_no}"})

    # === 3) Encode frame to base64
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    b64 = base64.b64encode(buf).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    # === 4) Build prompts
    title_prompt = (
        "Generate a catchy, engaging YouTube title with some excitement—use words like 'incredible', 'amazing', 'you won’t believe'. "
        "Keep it under 15 words, specific to the game/app/place, without excessive hype."
    ) if clickbait.lower() in ['y', 'yes'] else (
        "Generate a concise, engaging YouTube title specific to the game/app/place, under 15 words, without excessive hype."
    )

    desc_prompt = (
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
    )

    # === 5) Build payloads
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
                {"type": "text", "text": desc_prompt},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # === 6) Send requests
    tresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=title_payload)
    dresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=desc_payload)

    if tresp.status_code >= 400:
        return JSONResponse(status_code=400, content={"error": "Title generation failed", "details": tresp.json()})
    if dresp.status_code >= 400:
        return JSONResponse(status_code=400, content={"error": "Description generation failed", "details": dresp.json()})

    # === 7) Parse results
    title_json = tresp.json()
    desc_json = dresp.json()

    title = title_json["choices"][0]["message"]["content"].strip()
    description = desc_json["choices"][0]["message"]["content"].strip()

    return {
        "title": title,
        "description": description,
        "title_usage": title_json.get("usage", {}),
        "description_usage": desc_json.get("usage", {}),
    }

@app.get("/")
def home():
    return {"message": "Hello World!"}
