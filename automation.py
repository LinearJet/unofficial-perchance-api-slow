import time
import os
import re
import subprocess
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

def sanitize_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    return text[:100]

async def run_automation_job(prompt: str):
    """
    Render-optimized Playwright automation job.
    Uses pre-configured profile with NSFW enabled for deployment.
    """
    print(f"\n--- [PLAYWRIGHT JOB STARTED] ---\nPrompt: '{prompt}'")
    browser_process = None
    browser = None
    generated_images_b64 = []
    
    try:
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        port = 9222
        
        # Detect Chrome/Chromium binary location
        chrome_binary = None
        possible_locations = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser", 
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome"  # Render Playwright
        ]
        
        for location in possible_locations:
            if os.path.exists(location) or "*" in location:
                chrome_binary = location
                break
        
        if not chrome_binary:
            # Fallback: let system find it
            chrome_binary = "chromium"
        
        print(f"[PLAYWRIGHT] Using Chrome binary: {chrome_binary}")
        
        # Render-optimized Chrome flags
        command = [
            chrome_binary,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_path}",
            # Essential flags for Render's limited environment
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            # Memory optimization for Render's 512MB limit
            "--memory-pressure-off",
            "--max_old_space_size=512",
            "--disable-features=Translate,VizDisplayCompositor",
            # Render-specific optimizations
            "--virtual-time-budget=5000",
            "--run-all-compositor-stages-before-draw",
            "--disable-ipc-flooding-protection",
            # Anti-detection (preserve NSFW access)
            "--window-size=1920,1080",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "--disable-blink-features=AutomationControlled"
        ]

        # Start browser process
        browser_process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        print(f"[PLAYWRIGHT] Browser process started with PID: {browser_process.pid}")
        
        # Initialize Playwright
        playwright = await async_playwright().start()
        browser = None
        
        # Connection retry with optimized timing for Render
        for attempt in range(4):  # Reduced attempts for faster failure
            try:
                wait_time = 2 if attempt == 0 else min(3 * attempt, 8)
                await asyncio.sleep(wait_time)
                print(f"[PLAYWRIGHT] Connection attempt {attempt + 1} (waiting {wait_time}s)...")
                
                # Check if browser process is still running
                if browser_process.poll() is not None:
                    stdout, stderr = browser_process.communicate()
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    raise Exception(f"Browser process died with exit code {browser_process.poll()}: {error_msg}")
                
                # Connect to browser
                browser = await playwright.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{port}",
                    timeout=12000  # 12 second timeout
                )
                print("[PLAYWRIGHT] Successfully connected to browser")
                break
                
            except Exception as e:
                print(f"[PLAYWRIGHT] Connection attempt {attempt + 1} failed: {e}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                    browser = None
                if attempt == 3:  # Last attempt
                    raise Exception(f"Failed to connect to browser: {e}")
                continue

        # Create page using existing context (preserves NSFW settings)
        contexts = browser.contexts
        if contexts:
            print(f"[PLAYWRIGHT] Using existing context with saved settings")
            context = contexts[0]
            page = await context.new_page()
        else:
            print("[PLAYWRIGHT] Creating new context")
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
        
        # Optimize page for speed
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        # Navigate to generator
        await page.goto("https://perchance.org/ai-text-to-image-generator", 
                       wait_until="domcontentloaded", timeout=25000)
        
        # Wait for and switch to main iframe
        iframe_element = await page.wait_for_selector("#output iframe", timeout=25000)
        iframe = await iframe_element.content_frame()
        
        # Fill prompt and generate
        prompt_field = await iframe.wait_for_selector('[data-name="description"]', timeout=25000)
        await prompt_field.click()
        await prompt_field.fill("")
        await prompt_field.type(prompt, delay=20)  # Slight delay to avoid detection
        
        generate_button = await iframe.wait_for_selector("#generateButtonEl")
        await generate_button.click()
        
        # Wait for image generation (reduced timeout for Render)
        await iframe.wait_for_selector("iframe.text-to-image-plugin-image-iframe", timeout=25000)
        nested_iframes = await iframe.query_selector_all("iframe.text-to-image-plugin-image-iframe")
        
        # Process images with timeout optimization
        for i, frame_element in enumerate(nested_iframes[:4]):  # Limit to 4 images max
            try:
                nested_frame = await frame_element.content_frame()
                if not nested_frame:
                    continue
                
                # Reduced timeout for Render's time limits
                img_element = await nested_frame.wait_for_selector("#resultImgEl", timeout=120000)
                
                await nested_frame.wait_for_function(
                    "document.getElementById('resultImgEl').src.includes('data:image')",
                    timeout=120000
                )
                
                b64_src = await img_element.get_attribute("src")
                if b64_src and 'data:image' in b64_src:
                    generated_images_b64.append(b64_src)
                    
            except Exception as e:
                print(f"[PLAYWRIGHT] Error processing iframe {i}: {e}")
                continue
        
        print(f"--- [PLAYWRIGHT JOB FINISHED] ---")
        print(f"Generated {len(generated_images_b64)} images successfully")

    except Exception as e:
        print(f"\n--- [PLAYWRIGHT JOB FAILED] ---\nError: {e}")
        return []
    finally:
        # Optimized cleanup for Render
        if browser:
            try:
                await browser.close()
            except Exception as e:
                print(f"[PLAYWRIGHT] Browser cleanup error: {e}")
        
        if 'playwright' in locals():
            try:
                await playwright.stop()
            except Exception as e:
                print(f"[PLAYWRIGHT] Playwright cleanup error: {e}")
                
        if browser_process and browser_process.poll() is None:
            try:
                print(f"[PLAYWRIGHT] Terminating browser process {browser_process.pid}")
                browser_process.terminate()
                browser_process.wait(timeout=3)  # Quick timeout for Render
            except Exception as e:
                try:
                    browser_process.kill()
                except:
                    pass
        print("[PLAYWRIGHT] Cleanup complete.")
    
    return generated_images_b64

# Synchronous wrapper
def run_automation_job_sync(prompt: str):
    """Synchronous wrapper for the async automation job"""
    return asyncio.run(run_automation_job(prompt))