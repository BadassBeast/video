import cv2, requests, json, base64, os

# === 1) Get & fix path ===
video_path = input("Enter path to your video file: ").strip().replace("\\", "/")
if not os.path.exists(video_path):
    print("File not found:", video_path)
    exit()

# === 2) Extract frame ===
cap = cv2.VideoCapture(video_path)
frame_no = int(input("Enter frame number to extract: "))
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
ret, frame = cap.read()
cap.release()
if not ret:
    print(f"Cannot read frame {frame_no}")
    exit()

# === 3) Encode to base64 ===
_, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
b64 = base64.b64encode(buf).decode()
data_url = f"data:image/jpeg;base64,{b64}"

# === 4) Ask user if they want a clickbait title ===
clickbait_choice = input("Clickbait title? (y/n): ").strip().lower()
title_prompt = (
    "Generate a catchy, engaging YouTube title with some excitement—use words like 'incredible', 'amazing', 'you won’t believe'. "
    "Keep it under 15 words, specific to the game/app/place, without excessive hype."
) if clickbait_choice in ['y', 'yes'] else (
    "Generate a concise, engaging YouTube title specific to the game/app/place, under 15 words, without excessive hype."
)

# === 5) Build title payload ===
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

# === 6) Build description payload (with clickbait tone) ===
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

# === 7) API key & headers ===
headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}

# === 8) Send title request ===
print("Generating title...")
tresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=title_payload)
if tresp.status_code >= 400:
    print("Title Error:", tresp.json())
    exit()
title_json = tresp.json()

# === 9) Send description request ===
print("Generating description...")
dresp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=desc_payload)
if dresp.status_code >= 400:
    print("Description Error:", dresp.json())
    exit()
desc_json = dresp.json()

# === 10) Parse & print ===
title = title_json["choices"][0]["message"]["content"].strip()
description = desc_json["choices"][0]["message"]["content"].strip()
tuse = title_json.get("usage", {})
duse = desc_json.get("usage", {})

# === 11) Print results ===
print("\n=== Generated Title ===\n", title)
print("\n=== Generated Description ===\n", description)
print("\n=== Usage Details ===")
print(f"Title Prompt tokens: {tuse.get('prompt_tokens')}")
print(f"Title Completion tokens: {tuse.get('completion_tokens')}")
print(f"Title Total tokens: {tuse.get('total_tokens')}")
print(f"Description Prompt tokens: {duse.get('prompt_tokens')}")
print(f"Description Completion tokens: {duse.get('completion_tokens')}")
print(f"Description Total tokens: {duse.get('total_tokens')}")
print("\n=== Full Response JSON ===")
print("\n=== Title Response ===")
print(json.dumps(title_json, indent=2))
print("\n=== Description Response ===")
print(json.dumps(desc_json, indent=2))
