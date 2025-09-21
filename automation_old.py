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
    Optimized Playwright automation job with memory efficiency and speed improvements.
    Uses real Chromium with connect_over_cdp to avoid bot detection.
    """
    print(f"\n--- [PLAYWRIGHT JOB STARTED] ---\nPrompt: '{prompt}'")
    browser_process = None
    browser = None
    generated_images_b64 = []
    
    try:
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        port = 9222
        
        # Optimized Chrome flags for memory efficiency and stability
        command = [
            "chromium",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_path}",
            # Core stability flags
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            # Memory optimization (less aggressive to avoid crashes)
            "--memory-pressure-off",
            "--max_old_space_size=512",  # Increased from 512
            "--disable-features=Translate",
            "--disable-background-timer-throttling",
            # Remove potentially problematic flags
            # "--single-process",  # Can cause instability
            # "--no-zygote",       # Can cause issues
            "--disable-software-rasterizer",
            "--disable-background-networking",
            # Anti-detection flags
            "--window-size=1920,1080",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "--disable-blink-features=AutomationControlled",
            # Additional stability flags
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-ipc-flooding-protection"
        ]

        browser_process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE,  # Capture output for debugging
            stderr=subprocess.PIPE,  # Capture errors for debugging
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        print(f"[PLAYWRIGHT] Browser process started with PID: {browser_process.pid}")
        
        # Wait for browser to start and be ready for connections
        playwright = await async_playwright().start()
        browser = None
        
        # Retry connection with exponential backoff
        for attempt in range(6):
            try:
                wait_time = 3 if attempt == 0 else min(2 ** attempt, 10)
                await asyncio.sleep(wait_time)
                print(f"[PLAYWRIGHT] Connection attempt {attempt + 1} (waiting {wait_time}s)...")
                
                # Try to connect to the browser
                browser = await playwright.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{port}",
                    timeout=10000  # 10 second timeout
                )
                print("[PLAYWRIGHT] Successfully connected to browser")
                
                # Test the connection by checking browser version
                version = browser.version
                print(f"[PLAYWRIGHT] Browser version: {version}")
                break
                
            except Exception as e:
                print(f"[PLAYWRIGHT] Connection attempt {attempt + 1} failed: {e}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                    browser = None
                if attempt == 5:
                    raise Exception(f"Failed to connect to browser after 6 attempts: {e}")
                continue
        
        # Create new page with comprehensive error handling
        page = None
        context = None
        try:
            # First, try to use existing context if available
            contexts = browser.contexts
            if contexts:
                print(f"[PLAYWRIGHT] Using existing context (found {len(contexts)})")
                context = contexts[0]
                page = await context.new_page()
            else:
                print("[PLAYWRIGHT] Creating new context and page")
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
            print("[PLAYWRIGHT] Page created successfully")
            
            # Test page responsiveness
            await page.goto("about:blank", timeout=10000)
            print("[PLAYWRIGHT] Page is responsive and ready")
            
        except Exception as e:
            print(f"[PLAYWRIGHT] Failed to create page/context: {e}")
            # If we can't create a page, the browser connection is bad
            raise Exception(f"Cannot create page or context: {e}")
        
        # Optimize page settings for speed
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache"
        })
        
        # Block unnecessary resources for speed
        await page.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            and "perchance.org" not in route.request.url
            else route.continue_()
        ))
        
        # Navigate to the page
        await page.goto("https://perchance.org/ai-text-to-image-generator", 
                       wait_until="domcontentloaded", timeout=30000)
        
        # Wait for and switch to the main iframe
        iframe_element = await page.wait_for_selector("#output iframe", timeout=30000)
        iframe = await iframe_element.content_frame()
        
        # Fill prompt and generate
        prompt_field = await iframe.wait_for_selector('[data-name="description"]', timeout=30000)
        await prompt_field.click()
        await prompt_field.fill("")  # Clear field
        await prompt_field.type(prompt, delay=10)  # Small delay to avoid detection
        
        generate_button = await iframe.wait_for_selector("#generateButtonEl")
        await generate_button.click()
        
        # Wait for nested iframes to appear
        nested_iframe_selectors = await iframe.wait_for_selector(
            "iframe.text-to-image-plugin-image-iframe", 
            timeout=30000
        )
        
        # Get all nested iframes
        nested_iframes = await iframe.query_selector_all("iframe.text-to-image-plugin-image-iframe")
        
        # Process each image iframe
        for i, frame_element in enumerate(nested_iframes):
            try:
                nested_frame = await frame_element.content_frame()
                if not nested_frame:
                    continue
                
                # Wait for image to load with longer timeout
                img_element = await nested_frame.wait_for_selector("#resultImgEl", timeout=180000)
                
                # Wait for src attribute to be populated with base64 data
                await nested_frame.wait_for_function(
                    "document.getElementById('resultImgEl').src.includes('data:image')",
                    timeout=180000
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
        # Cleanup resources in proper order
        if browser:
            try:
                # Close all pages first
                for context in browser.contexts:
                    for page in context.pages:
                        await page.close()
                    await context.close()
                await browser.close()
            except Exception as e:
                print(f"[PLAYWRIGHT] Error during browser cleanup: {e}")
        
        if 'playwright' in locals():
            try:
                await playwright.stop()
            except Exception as e:
                print(f"[PLAYWRIGHT] Error stopping playwright: {e}")
                
        if browser_process:
            try:
                print(f"[PLAYWRIGHT] Terminating browser process {browser_process.pid}")
                
                # Check if process is still running
                if browser_process.poll() is None:
                    # Get any error output before terminating
                    try:
                        stdout, stderr = browser_process.communicate(timeout=1)
                        if stderr:
                            print(f"[PLAYWRIGHT] Browser stderr: {stderr.decode()}")
                    except subprocess.TimeoutExpired:
                        pass
                    
                    if os.name != 'nt':
                        os.killpg(os.getpgid(browser_process.pid), 15)  # SIGTERM
                    else:
                        browser_process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        browser_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print("[PLAYWRIGHT] Forcefully killing browser process")
                        if os.name != 'nt':
                            os.killpg(os.getpgid(browser_process.pid), 9)  # SIGKILL
                        else:
                            browser_process.kill()
                        browser_process.wait()
                else:
                    print(f"[PLAYWRIGHT] Browser process already exited with code: {browser_process.poll()}")
                    # Still try to get error output
                    try:
                        stdout, stderr = browser_process.communicate(timeout=0.1)
                        if stderr:
                            print(f"[PLAYWRIGHT] Browser stderr: {stderr.decode()}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"[PLAYWRIGHT] Error terminating browser process: {e}")
                pass
        print("[PLAYWRIGHT] Cleanup complete.")
    
    return generated_images_b64

# Synchronous wrapper for backward compatibility
def run_automation_job_sync(prompt: str):
    """Synchronous wrapper for the async automation job"""
    return asyncio.run(run_automation_job(prompt))