import os
import platform
import pickle
import requests
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import speech_recognition as sr

import warnings
# Suprimir o aviso específico emitido pelo pydub
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work", category=RuntimeWarning)

from pydub import AudioSegment


# General Constants
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
CHROMEDRIVER_DIR = "chromedriver"
FFMPEG_DIR = "ffmpeg"


# Driver Management
def initialize_driver():
    """Initialize the WebDriver with Chrome options."""
    options = Options()
    #options.add_argument("--headless")  # Para rodar em modo headless
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
        "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
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
    if response.status_code == 200:
        with open(zip_path, "wb") as file:
            file.write(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(CHROMEDRIVER_DIR)
        os.remove(zip_path)
        print("ChromeDriver successfully updated.")
    else:
        raise RuntimeError("Failed to download ChromeDriver.")


def get_os_type():
    """Identify the OS type for ChromeDriver compatibility."""
    system = platform.system().lower()
    return {"windows": "win64", "linux": "linux64", "darwin": "mac64"}.get(system, None)


# FFmpeg and Audio Utilities
def check_and_setup_ffmpeg():
    """Download and configure FFmpeg if not already installed."""
    ffmpeg_exe = os.path.join(FFMPEG_DIR, "bin", "ffmpeg.exe")
    if not os.path.exists(ffmpeg_exe):
        print("Downloading FFmpeg...")
        zip_path = os.path.join(FFMPEG_DIR, "ffmpeg.zip")
        os.makedirs(FFMPEG_DIR, exist_ok=True)
        response = requests.get(FFMPEG_URL)
        with open(zip_path, "wb") as file:
            file.write(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(FFMPEG_DIR)
        os.remove(zip_path)
    if not os.path.exists(ffmpeg_exe):
        raise FileNotFoundError("FFmpeg setup failed.")
    os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_exe)
    AudioSegment.converter = ffmpeg_exe
    print('FFmpeg successfully configured!')


def convert_to_wav(input_path, output_path="converted_audio.wav"):
    """Convert audio to WAV format."""
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path


def download_audio(audio_url, save_path):
    """Download audio from a given URL."""
    response = requests.get(audio_url)
    with open(save_path, "wb") as file:
        file.write(response.content)
    return save_path


def transcribe_audio(audio_path):
    """Transcribe audio using Google's Speech Recognition."""
    recognizer = sr.Recognizer()
    if not audio_path.endswith(".wav"):
        audio_path = convert_to_wav(audio_path)
    with sr.AudioFile(audio_path) as source:
        return recognizer.recognize_google(recognizer.record(source))
    

def format_cnpj(cnpj):
    """Formata o CNPJ no formato 00.000.000/0000-00"""
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"