import time
import os
import json
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def login_and_get_tokens():
    """
    Launches Chrome, waits for user to login to WeChat MP,
    and returns (cookie_string, token).
    """
    print("Launching Browser for Login...")
    
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Cannot be headless for QR scan
    
    try:
        driver_path = ChromeDriverManager().install()
        # Fix for webdriver_manager 4.x bug on Mac where it points to THIRD_PARTY_NOTICES
        if "THIRD_PARTY_NOTICES" in driver_path:
            driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver")
            
        # Ensure it's executable
        os.chmod(driver_path, 0o755)
        
        print(f"Driver path: {driver_path}")
        driver = webdriver.Chrome(service=Service(driver_path), options=options)
        driver.get("https://mp.weixin.qq.com/")
        
        print("Please scan the QR code to login in the browser window...")
        
        token = None
        cookies_str = None
        
        # Wait for login (max 120 seconds)
        for _ in range(120):
            current_url = driver.current_url
            if "token=" in current_url:
                print("Login detected!")
                
                # Extract token from URL
                try:
                    token = current_url.split("token=")[1].split("&")[0]
                except:
                    pass
                
                # Extract cookies
                selenium_cookies = driver.get_cookies()
                cookie_parts = []
                for cookie in selenium_cookies:
                    cookie_parts.append(f"{cookie['name']}={cookie['value']}")
                cookies_str = "; ".join(cookie_parts)
                
                break
            time.sleep(1)
            
        driver.quit()
        
        if token and cookies_str:
            return cookies_str, token, None
        else:
            return None, None, "Timeout: Login not detected within 120 seconds."
            
    except Exception as e:
        error_msg = f"Error in auto-login: {str(e)}"
        print(error_msg)
        return None, None, error_msg

AUTH_CACHE_FILE = ".auth_cache"

def save_credentials(cookie, token):
    """Save credentials to a local file."""
    try:
        data = {
            "cookie": cookie,
            "token": token,
            "timestamp": time.time()
        }
        # Simple obfuscation (not real encryption, but better than plain text)
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

if __name__ == "__main__":
    # Test
    c, t, e = login_and_get_tokens()
    if e:
        print(f"Failed: {e}")
    else:
        print(f"Cookie: {c}")
        print(f"Token: {t}")
