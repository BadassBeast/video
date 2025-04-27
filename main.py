from fastapi import FastAPI
import cv2
import requests
import pybase64
import numpy as np
from fastapi.responses import JSONResponse

app = FastAPI()

# Route for testing if the app is live
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Example route with a dynamic parameter
@app.get("/item/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

# Example route that uses OpenCV (you can replace this with actual functionality)
@app.get("/opencv-example")
def opencv_example():
    # OpenCV functionality as an example (could be an image processing task)
    image = np.zeros((512, 512, 3), np.uint8)
    image = cv2.putText(image, 'OpenCV Example', (10, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Save image to disk for demonstration purposes
    cv2.imwrite('opencv_example.png', image)
    
    return JSONResponse(content={"message": "OpenCV image generated."})

# Example route using requests to fetch data from a URL
@app.get("/fetch-data")
def fetch_data():
    url = "https://jsonplaceholder.typicode.com/todos/1"
    response = requests.get(url)
    return response.json()

# Example route using pybase64 for encoding data
@app.get("/encode-base64")
def encode_base64():
    sample_data = "This is a test string."
    encoded_data = pybase64.b64encode(sample_data.encode("utf-8")).decode("utf-8")
    return {"encoded_data": encoded_data}

# Example route with query parameters
@app.get("/query")
def read_query(name: str = None, age: int = None):
    return {"name": name, "age": age}

# Example of error handling with FastAPI
@app.get("/error-example")
def error_example():
    try:
        # Trigger an error for demonstration
        1 / 0
    except ZeroDivisionError as e:
        return JSONResponse(status_code=500, content={"error": "A server error occurred", "details": str(e)})
