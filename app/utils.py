import os
import platform
import pickle
import requests
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# General Constants
CHROMEDRIVER_DIR = "chromedriver"

# Driver Management
def initialize_driver():
    """Initialize the WebDriver with Chrome options."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-web-security")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--incognito")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
    driver_path = f"chromedriver/chromedriver-{get_os_type()}/chromedriver.exe" 
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def load_cookies(driver, file_path):
    """Load cookies into the browser session."""
    try:
        with open(file_path, "rb") as file:
            cookies = pickle.load(file)
        for cookie in cookies:
            cookie.pop("sameSite", None)
            driver.add_cookie(cookie)
        driver.refresh()
        print("Cookies successfully loaded.")
    except FileNotFoundError:
        print(f"Cookie file '{file_path}' not found.")
    except Exception as e:
        print(f"Error loading cookies: {e}")

def save_cookies(driver, file_path):
    """Save cookies from the browser session."""
    try:
        with open(file_path, "wb") as file:
            pickle.dump(driver.get_cookies(), file)
        print("Cookies successfully saved.")
    except Exception as e:
        print(f"Error saving cookies: {e}")

# ChromeDriver Management
def get_chrome_version():
    """Retrieve the installed version of Google Chrome."""
    try:
        return os.popen(
            r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
        ).read().split()[-1]
    except Exception:
        raise RuntimeError("Unable to retrieve Chrome version.")

def get_chromedriver_url(version):
    """Get the download URL for the corresponding ChromeDriver version."""
    major_version = version.split('.')[0]
    response = requests.get(
        "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
        verify=False
    )
    if response.status_code == 200:
        data = response.json()
        for entry in data["versions"]:
            if entry["version"].startswith(major_version):
                os_type = get_os_type()
                for download in entry["downloads"]["chromedriver"]:
                    if download["platform"] == os_type:
                        return download["url"]
    raise RuntimeError(f"Unable to find ChromeDriver for version {version}.")

def update_chromedriver(url):
    """Download and update ChromeDriver."""
    os.makedirs(CHROMEDRIVER_DIR, exist_ok=True)
    zip_path = os.path.join(CHROMEDRIVER_DIR, "chromedriver.zip")
    response = requests.get(url, stream=True)
    try:
        if response.status_code == 200:
            with open(zip_path, "wb") as file:
                file.write(response.content)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(CHROMEDRIVER_DIR)
            os.remove(zip_path)
            print("ChromeDriver successfully updated.")
        else:
            raise RuntimeError("Failed to download ChromeDriver.")
    except Exception as e:
        print(f"Failed to update ChromeDriver: {e}")

def get_os_type():
    """Identify the OS type for ChromeDriver compatibility."""
    system = platform.system().lower()
    return {"windows": "win64", "linux": "linux64", "darwin": "mac64"}.get(system, None)

def prompt_login(instagram_url, instagram_cookies_file):
    """Prompt user to log in and save cookies."""
    # Start a new driver without the --headless argument
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    # Access the Instagram URL
    driver.get(instagram_url)
    # Prompt the user to log in manually
    input("Log in to Instagram and press ENTER to continue...")
    # After login, save the cookies
    save_cookies(driver, instagram_cookies_file)
    # Close the driver
    driver.quit()
    
def format_cnpj(cnpj):
    """Formata o CNPJ no formato 00.000.000/0000-00"""
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"