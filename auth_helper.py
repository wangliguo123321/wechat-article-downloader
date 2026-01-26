import time
import os
import json
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Constants
AUTH_CACHE_FILE = ".auth_cache"

def get_system_chrome_path():
    """Detect system installed Chromium/Chrome path."""
    paths = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def init_login_driver():
    """
    Initializes Chrome in headless mode and navigates to the login page.
    Returns the driver instance.
    """
    print("Initializing Headless Browser for Login...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # Try to use system installed Chromium (common in Linux/Streamlit Cloud)
    chrome_binary = get_system_chrome_path()
    if chrome_binary:
        print(f"Found system Chrome/Chromium at: {chrome_binary}")
        options.binary_location = chrome_binary
    
    try:
        service = None
        # On Linux/Streamlit Cloud, we often need to specify the matching driver manually or rely on system path
        if chrome_binary and "/usr/bin" in chrome_binary:
             # Assuming chromedriver is also in /usr/bin or /usr/lib/chromium-browser/chromedriver
             # But usually Selenium Manager or standard system path handles it if we don't force a service.
             # However, to be safe, we try standard webdriver_manager IF we are not sure.
             # In Streamlit cloud, 'chromium-driver' package installs to /usr/bin/chromedriver usually.
             if os.path.exists("/usr/bin/chromedriver"):
                 service = Service("/usr/bin/chromedriver")
                 print("Using system chromedriver at /usr/bin/chromedriver")
        
        if not service:
            try:
                driver_path = ChromeDriverManager().install()
                if "THIRD_PARTY_NOTICES" in driver_path:
                    driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver")
                os.chmod(driver_path, 0o755)
                service = Service(driver_path)
            except Exception as e:
                print(f"ChromeDriverManager failed: {e}. Trying default service...")
                # If manager fails, try default (assuming in PATH)
                pass

        if service:
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
            
        driver.get("https://mp.weixin.qq.com/")
        return driver, None
    except Exception as e:
        return None, f"Error initializing driver: {str(e)}"

def get_login_qr(driver):
    """
    Captures the login QR code from the driver.
    Returns: base64_image_string, error_message
    """
    try:
        # Wait for the QR code image to be present
        # The QR code usually is an img with class 'login__type__container__scan__qrcode' or inside a specific container
        # We will try to find the QR code image. If elusive, we screenshot a relevant area.
        
        # Strategy A: Screenshot the specific element (best UX)
        # Using a generic wait for the main QR code container
        wait = WebDriverWait(driver, 10)
        qr_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "login__type__container__scan__qrcode")) 
        )
        
        # Give it a moment to render fully
        time.sleep(1)
        
        # Screenshot the element
        base64_str = qr_element.screenshot_as_base64
        return base64_str, None
        
    except Exception as e:
        print(f"Failed to find specific QR code element: {e}")
        # Strategy B: Fallback to full page screenshot
        try:
            return driver.get_screenshot_as_base64(), None
        except Exception as e2:
            return None, f"Error capturing QR code: {str(e2)}"

def check_login_status(driver):
    """
    Checks if the driver has redirected to the logged-in page (has 'token' in URL).
    Returns: (success, cookies_str, token)
    """
    try:
        current_url = driver.current_url
        if "token=" in current_url:
            print("Login detected!")
            
            # Extract token
            token = current_url.split("token=")[1].split("&")[0]
            
            # Extract cookies
            selenium_cookies = driver.get_cookies()
            cookie_parts = []
            for cookie in selenium_cookies:
                cookie_parts.append(f"{cookie['name']}={cookie['value']}")
            cookies_str = "; ".join(cookie_parts)
            
            return True, cookies_str, token
            
        return False, None, None
    except Exception as e:
        print(f"Error checking login status: {e}")
        return False, None, None

def save_credentials(cookie, token):
    """Save credentials to a local file."""
    try:
        data = {
            "cookie": cookie,
            "token": token,
            "timestamp": time.time()
        }
        # Simple obfuscation
        json_str = json.dumps(data)
        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        with open(AUTH_CACHE_FILE, "w") as f:
            f.write(encoded_str)
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

def load_credentials():
    """Load credentials from local file."""
    if not os.path.exists(AUTH_CACHE_FILE):
        return None, None
        
    try:
        with open(AUTH_CACHE_FILE, "r") as f:
            encoded_str = f.read()
            
        json_str = base64.b64decode(encoded_str).decode('utf-8')
        data = json.loads(json_str)
        
        # Optional: Check if expired (e.g., > 24 hours)
        if time.time() - data.get("timestamp", 0) > 86400:
            print("Credentials expired.")
            return None, None
            
        return data.get("cookie"), data.get("token")
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None, None

def clear_credentials():
    """Clear saved credentials."""
    if os.path.exists(AUTH_CACHE_FILE):
        try:
            os.remove(AUTH_CACHE_FILE)
            return True
        except Exception as e:
            print(f"Error clearing credentials: {e}")
            return False
    return True
