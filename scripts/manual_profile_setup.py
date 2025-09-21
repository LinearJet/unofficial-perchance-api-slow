#!/usr/bin/env python3
"""
Alternative manual setup - launches browser and waits for you to manually close it
"""

import os
import subprocess
import time

def manual_browser_setup():
    """Launch browser manually and let user configure everything"""
    print("🚀 MANUAL BROWSER SETUP")
    print("="*50)
    
    profile_path = os.path.join(os.getcwd(), "automation_profile")
    os.makedirs(profile_path, exist_ok=True)
    
    print(f"📁 Profile will be saved to: {profile_path}")
    
    # Try different Chrome/Chromium locations
    browser_commands = [
        ["chromium", "--version"],
        ["google-chrome", "--version"], 
        ["google-chrome-stable", "--version"],
        ["/usr/bin/chromium", "--version"],
        ["/usr/bin/google-chrome", "--version"]
    ]
    
    chrome_binary = None
    for cmd in browser_commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            chrome_binary = cmd[0]
            print(f"✅ Found browser: {chrome_binary}")
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not chrome_binary:
        print("❌ No Chrome/Chromium found. Please install chromium or google-chrome")
        return False
    
    # Launch browser with profile
    command = [
        chrome_binary,
        f"--user-data-dir={profile_path}",
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--disable-default-apps",
        "https://perchance.org/ai-text-to-image-generator"
    ]
    
    print("\n🌐 LAUNCHING BROWSER...")
    print("="*70)
    print("📋 INSTRUCTIONS:")
    print("1. ✅ Browser will open to Perchance AI generator")
    print("2. 🔍 Find the NSFW/Adult content toggle")
    print("3. 🔓 Enable NSFW/Adult content")
    print("4. 🧪 Test with prompts like:")
    print("   • 'artistic nude portrait'")
    print("   • 'sensual photography'") 
    print("   • 'adult content test'")
    print("5. ✅ Verify NSFW content is generated")
    print("6. 🔄 Browse other tabs/settings as needed")
    print("7. ❌ CLOSE THE BROWSER when completely done")
    print("="*70)
    print("💡 TIPS for finding NSFW toggle:")
    print("   • Look near the prompt input box")
    print("   • Check Settings/Advanced/Options menus")
    print("   • Look for 'NSFW', 'Adult', 'Mature', '🔞' symbols")
    print("   • Try scrolling down on the page")
    print("   • Right-click for context menus")
    print("="*70)
    
    input("📝 Press Enter to launch browser...")
    
    try:
        # Start browser process
        process = subprocess.Popen(command)
        print(f"🚀 Browser launched with PID: {process.pid}")
        print("⏳ Waiting for you to close the browser...")
        print("   (The script will wait until you close ALL browser windows)")
        
        # Wait for browser to close
        process.wait()
        print("✅ Browser closed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted! Terminating browser...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        return False
    except Exception as e:
        print(f"❌ Error launching browser: {e}")
        return False
    
    # Verify profile was created
    if os.path.exists(profile_path) and os.listdir(profile_path):
        print(f"\n✅ SUCCESS! Profile saved to: {profile_path}")
        print("📁 Profile contains:")
        items = os.listdir(profile_path)
        for item in items[:5]:
            print(f"   • {item}")
        if len(items) > 5:
            print(f"   • ... and {len(items) - 5} more files/folders")
        
        print("\n🚀 NEXT STEPS:")
        print("1. git add automation_profile/")
        print("2. git commit -m 'Add NSFW-enabled browser profile'")
        print("3. git push")
        print("4. Deploy to Render!")
        return True
    else:
        print("❌ Profile setup failed - no profile data saved")
        print("💡 Try running the setup again and make sure to:")
        print("   • Actually browse to the Perchance site")
        print("   • Enable NSFW settings")
        print("   • Let the browser fully load before closing")
        return False

if __name__ == "__main__":
    print("🔧 MANUAL PROFILE SETUP")
    print("This approach gives you full control over the browser")
    print("-" * 50)
    
    success = manual_browser_setup()
    
    if success:
        print("\n🎉 PROFILE SETUP COMPLETE!")
    else:
        print("\n❌ Setup failed. Please try again.")
        print("💡 Make sure Chrome/Chromium is installed and you follow all steps")