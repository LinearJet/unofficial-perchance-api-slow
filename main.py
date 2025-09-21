from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import os
import subprocess
import asyncio

# Import from the optimized Playwright automation file
from automation import run_automation_job, run_automation_job_sync

app = FastAPI()

# --- MODELS ---
class ImageRequest(BaseModel):
    prompt: str

class ImageResponse(BaseModel):
    message: str
    prompt: str
    image_count: int
    images_base64: List[str]

# --- ENDPOINTS ---
@app.get("/")
def read_root():
    return {"status": "Perchance Automation API is running (Playwright Optimized)"}

@app.post("/setup", status_code=202)
async def setup_browser_profile():
    print("--- [SETUP MODE ACTIVATED] ---")
    browser_process = None
    try:
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        command = [
            "chromium",
            f"--user-data-dir={profile_path}",
            "--disable-blink-features=AutomationControlled", 
            "https://perchance.org/ai-text-to-image-generator"
        ]
        browser_process = subprocess.Popen(command)
        print(f"[SETUP] Browser process started with PID: {browser_process.pid}. Waiting for you to close it...")
        
        # Use asyncio to wait without blocking
        while browser_process.poll() is None:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"--- [SETUP MODE FAILED] ---\nError: {e}")
        if browser_process:
            browser_process.terminate()
        return {"message": f"Setup failed: {e}"}
    print("--- [SETUP MODE FINISHED] ---")
    return {"message": "Setup browser closed. Profile has been updated."}

@app.post("/generate", response_model=ImageResponse)
async def create_generation_job(request: ImageRequest):
    print(f"Received API request for prompt: '{request.prompt}'")
    
    # Use the async version directly
    image_data = await run_automation_job(request.prompt)
    
    if not image_data:
        return ImageResponse(
            message="Image generation failed. Check server logs.",
            prompt=request.prompt, 
            image_count=0, 
            images_base64=[]
        )
    
    return ImageResponse(
        message="Image generation successful.",
        prompt=request.prompt, 
        image_count=len(image_data), 
        images_base64=image_data
    )

# Alternative sync endpoint if needed for compatibility
@app.post("/generate-sync", response_model=ImageResponse)
def create_generation_job_sync(request: ImageRequest):
    print(f"Received sync API request for prompt: '{request.prompt}'")
    image_data = run_automation_job_sync(request.prompt)
    
    if not image_data:
        return ImageResponse(
            message="Image generation failed. Check server logs.",
            prompt=request.prompt, 
            image_count=0, 
            images_base64=[]
        )
    
    return ImageResponse(
        message="Image generation successful.",
        prompt=request.prompt, 
        image_count=len(image_data), 
        images_base64=image_data
    )