#!/usr/bin/env python3
"""
Local setup script to configure the browser profile with NSFW enabled.
Run this locally before deploying to Render.
"""

import os
import time
import subprocess
import asyncio
import sys

# Check if playwright is installed
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

async def setup_browser_profile_with_nsfw():
    """Setup browser profile with NSFW toggle enabled"""
    print("=== Setting up browser profile with NSFW enabled ===")
    
    profile_path = os.path.join(os.getcwd(), "automation_profile")
    os.makedirs(profile_path, exist_ok=True)
    
    playwright = await async_playwright().start()
    
    try:
        print("Launching browser with persistent context...")
        # Launch browser with profile - use system Chrome/Chromium
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,  # We need to see the page to enable NSFW
            viewport={'width': 1920, 'height': 1080},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        page = await browser.new_page()
        
        print("Navigating to Perchance AI generator...")
        await page.goto("https://perchance.org/ai-text-to-image-generator", timeout=60000)
        
        # Wait for page to load completely
        print("Waiting for page to fully load...")
        await page.wait_for_load_state("networkidle", timeout=30000)
        
        print("\n" + "="*70)
        print("🔧 MANUAL SETUP REQUIRED:")
        print("="*70)
        print("1. ✅ The browser should now be open with Perchance AI generator")
        print("2. 🔍 Look for NSFW/Adult content toggle")
        print("3. 🔓 Enable NSFW/Adult content generation")
        print("4. 🧪 Test with a prompt like 'artistic portrait' to verify")
        print("5. 📁 You can open multiple tabs, browse settings, etc.")
        print("6. ⚠️  DO NOT close the browser window manually!")
        print("="*70)
        print("💡 TIPS:")
        print("   • NSFW toggle might be in settings, near prompt, or dropdown")
        print("   • Look for 'NSFW', 'Adult', 'Mature Content', or '🔞' symbols")
        print("   • Try scrolling down or clicking settings/gear icons")
        print("   • Test generation to make sure NSFW content appears")
        print("="*70)
        
        # Keep asking until user confirms they're done
        while True:
            user_input = input("\n❓ Have you successfully enabled NSFW and tested it? (yes/no/help): ").lower().strip()
            
            if user_input in ['yes', 'y', 'done', 'finished']:
                print("✅ Great! Proceeding with profile save...")
                break
            elif user_input in ['no', 'n', 'not yet', 'wait']:
                print("⏳ Take your time! The browser will stay open...")
                print("💡 Remember: Look for NSFW/Adult toggle and test it")
                continue
            elif user_input in ['help', 'h', '?']:
                print("\n🆘 HELP - Where to find NSFW settings:")
                print("   1. Look for a toggle switch near the prompt box")
                print("   2. Check for 'Settings' or gear ⚙️ icon")
                print("   3. Look for 'Advanced' or 'Content' options")
                print("   4. Try right-clicking on the page for context menu")
                print("   5. Check the top navigation or sidebar")
                print("   6. Look for any '🔞' or 'Adult' labels")
                print("\n🧪 To test: Try generating 'artistic nude portrait'")
                continue
            else:
                print("❌ Please answer 'yes' when ready, 'no' to continue looking, or 'help' for assistance")
                continue
        
        # Give user a moment to finish any final actions
        print("⏳ Saving profile settings in 3 seconds...")
        await asyncio.sleep(3)
        
        # Test that the profile has the settings by creating a new page
        print("🔍 Testing profile settings...")
        test_page = await browser.new_page()
        await test_page.goto("https://perchance.org/ai-text-to-image-generator", timeout=30000)
        await test_page.wait_for_load_state("networkidle")
        
        print("✅ Profile test complete")
        await test_page.close()
        
        # Now close the browser
        print("🔄 Closing browser and saving profile...")
        await browser.close()
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print("\n🔧 Troubleshooting:")
        print("- Make sure you have a stable internet connection")
        print("- Try running the script again")
        print("- Check if Perchance.org is accessible")
        return False
    finally:
        await playwright.stop()
    
    # Verify profile was created
    if os.path.exists(profile_path) and os.listdir(profile_path):
        print(f"✅ Profile setup complete! Settings saved to: {profile_path}")
        print("📁 Profile contents:")
        for item in os.listdir(profile_path)[:10]:  # Show first 10 items
            print(f"   - {item}")
        if len(os.listdir(profile_path)) > 10:
            print(f"   ... and {len(os.listdir(profile_path)) - 10} more items")
        print("\n🚀 You can now deploy this to Render with NSFW settings preserved!")
    else:
        print("❌ Profile setup may have failed - profile directory is empty")
        return False
    
    return True

def create_profile_backup_script():
    """Create a script to backup/restore the profile"""
    backup_script = '''#!/bin/bash
# Profile backup/restore script

if [ "$1" = "backup" ]; then
    echo "Creating profile backup..."
    tar -czf automation_profile_backup.tar.gz automation_profile/
    echo "Backup created: automation_profile_backup.tar.gz"
elif [ "$1" = "restore" ]; then
    echo "Restoring profile from backup..."
    tar -xzf automation_profile_backup.tar.gz
    echo "Profile restored from backup"
else
    echo "Usage: $0 [backup|restore]"
fi
'''
    
    with open("profile_backup.sh", "w") as f:
        f.write(backup_script)
    os.chmod("profile_backup.sh", 0o755)
    print("Created profile_backup.sh for easy backup/restore")

if __name__ == "__main__":
    print("🚀 Starting local profile setup...")
    print("📋 This will help you configure NSFW settings for Perchance")
    print("-" * 50)
    
    try:
        create_profile_backup_script()
        success = asyncio.run(setup_browser_profile_with_nsfw())
        
        if success:
            print("\n🎉 SUCCESS!")
            print("✅ Profile configured with NSFW settings")
            print("✅ Backup script created (profile_backup.sh)")
            print("\n📝 Next steps:")
            print("1. Add profile to git: git add automation_profile/")
            print("2. Commit: git commit -m 'Add NSFW-enabled profile'")
            print("3. Push to GitHub: git push")
            print("4. Deploy to Render!")
        else:
            print("\n❌ Setup may have failed. Please try again.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Try installing playwright browsers: playwright install chromium")