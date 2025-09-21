# Perchance AI Image Generator API

🎨 A FastAPI wrapper for Perchance AI image generation with NSFW support.

## Features
- ✅ Generate AI images using Perchance
- ✅ NSFW content support (when configured)
- ✅ Multiple image generation
- ✅ Base64 image output
- ✅ Memory-optimized for deployment
- ✅ Docker & Render deployment ready

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python scripts/profile_setup.py  # Configure NSFW settings
uvicorn main:app --reload


API Usage
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "beautiful landscape"}'
```
```
Deployment
See deployment instructions in the repository.
### 2. Setup NSFW Profile (IMPORTANT!)
# Run profile setup to enable NSFW
python scripts/profile_setup.py
# OR use manual setup
python scripts/manual_profile_setup.py
````
