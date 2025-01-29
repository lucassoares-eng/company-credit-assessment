from datetime import datetime, timedelta
import os
import random
import re
import time
from dotenv import load_dotenv
import numpy as np
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from unidecode import unidecode
import urllib3
from app.client import DriverManager
from app.utils import download_audio, format_cnpj, transcribe_audio

# Desabilitar avisos de solicitações HTTPS não verificadas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregar variáveis do arquivo .env
load_dotenv()

INSTAGRAM_COOKIES_FILE = "instagram_cookies.pkl"
INSTAGRAM_URL = "https://www.instagram.com"

manager = DriverManager(INSTAGRAM_URL, INSTAGRAM_COOKIES_FILE)

# Function to fetch company data by CNPJ
def fetch_cnpj_data(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        response = requests.get(url, verify=False)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 30))
            print(f"Waiting {retry_after} seconds before retrying...")
            time.sleep(retry_after)
            return fetch_cnpj_data(cnpj)
        else:
            return {"error": f"Unable to fetch CNPJ data: {response.status_code}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Function to fetch complaints and reputation on Reclame Aqui
def fetch_reputation(company_name):
    driver = manager.get_driver()

    def try_fetch(url):
        try:
            driver.get(url)
            ratings = driver.find_elements(By.CLASS_NAME, "go3621686408")
            ratings_text = [rating.text for rating in ratings]
            if ratings_text:
                return float(ratings_text[0].split('/')[0])
            else:
                return np.nan
        except (NoSuchElementException, TimeoutException):
            return np.nan
        except Exception as e:
            return np.nan

    # First attempt with the original name
    search_url = f"https://www.reclameaqui.com.br/empresa/{company_name}/"
    rating = try_fetch(search_url)

    # If not found, try without hyphens
    if np.isnan(rating) and '-' in company_name:
        search_url_alternate = f"https://www.reclameaqui.com.br/empresa/{company_name.replace('-', '')}/"
        rating = try_fetch(search_url_alternate)

    # Return 0 if reputation could not be fetched
    return rating if not np.isnan(rating) else 0

# Function to log in to the "pesquisaprotesto.com.br" website
def pesquisaprotesto_login():
    driver = manager.get_driver()
    username = os.getenv("PESQUISAPROTESTO_USER")
    password = os.getenv("PESQUISAPROTESTO_PASSWORD")

    try:
        driver.get("https://www.pesquisaprotesto.com.br/login")
        wait = WebDriverWait(driver, 5)

        # Fill in username
        username_input = wait.until(EC.visibility_of_element_located((By.ID, "usario")))
        username_input.clear()
        username_input.send_keys(username)

        # Fill in password
        password_input = wait.until(EC.visibility_of_element_located((By.ID, "senha")))
        password_input.clear()
        password_input.send_keys(password)

        # Click "Stay logged in"
        stay_logged_in = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'manter-logado-container')]"))
        )
        stay_logged_in.click()

        # Click "Login"
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar')]")))
        driver.execute_script("arguments[0].click();", login_button)

        # Wait for the "Continue" button to become clickable
        continuar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-success btn-lg' and text()='Continuar']")))
        continuar_button.click()

        # Handle email validation if required
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, "//h3[text()='Valide por E-mail']")))
            print("Email validation required. Enter the code sent to your registered email.")

            # Select email radio button
            email_radio_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @value='email']"))
            )
            driver.execute_script("arguments[0].click();", email_radio_button)

            # Click "Send Code"
            send_code_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ENVIAR CÓDIGO')]"))
            )
            driver.execute_script("arguments[0].click();", send_code_button)

            last_resend_time = datetime.now()
            while True:

                # Wait for code input fields
                inputs = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//input[@maxlength='1' and @class='token-login-input']"))
                )

                # Ask for user input
                code = input("Enter the 6-digit code received via email (or type 0 to resend the code): ")
                
                if code == '0':
                    current_time = datetime.now()
                    if last_resend_time and (current_time - last_resend_time) < timedelta(minutes=2):
                        remaining_time = (last_resend_time + timedelta(minutes=2) - current_time).total_seconds()
                        print(f"Please wait {int(remaining_time)} seconds before resending the code.")
                        continue
                    last_resend_time = current_time
                    print("Resending code...")
                    # Click "Resend Code"
                    resend_code_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'link') and contains(text(), 'Reenviar código')]"))
                    )
                    driver.execute_script("arguments[0].click();", resend_code_button)
                    continue  # Resend the code and prompt again

                if len(code) == 6:
                    # Fill each input field
                    for i, input_field in enumerate(inputs):
                        input_field.clear()
                        input_field.send_keys(code[i])
                    print(f"Code '{code}' entered.")
                    break  # Exit the loop if a valid code is entered
                else:
                    print("Invalid code. Please enter a 6-digit numeric code.")

            # Confirm code
            confirm_button = wait.until(EC.element_to_be_clickable((By.ID, "btnConfirmaToken2fa")))
            driver.execute_script("arguments[0].click();", confirm_button)

        except TimeoutException:
            pass  # Continue if no email validation is required

    except Exception as e:
        raise RuntimeError(f"Error during login: {str(e)}")

# Function to check if the user is logged in
def is_logged_in():
    driver = manager.get_driver()
    try:
        user_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "__BVID__67__BV_toggle_"))
        )
        return user_button.is_displayed()
    except Exception:
        return False

# Function to solve reCAPTCHA challenges
def solve_recaptcha():
    driver = manager.get_driver()

    try:
        wait = WebDriverWait(driver, 5)

        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='o desafio reCAPTCHA expira em dois minutos']"))
        )
        driver.switch_to.frame(iframe)

        audio_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
        audio_button.click()

        audio_source = wait.until(EC.presence_of_element_located((By.ID, "audio-source"))).get_attribute("src")
        audio_path = download_audio(audio_source, "recaptcha_audio.mp3")

        response = transcribe_audio(audio_path)

        audio_response_input = wait.until(EC.presence_of_element_located((By.ID, "audio-response")))
        for char in response:
            audio_response_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.5))

        verify_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
        verify_button.click()

    except Exception as e:
        raise RuntimeError(f"Error solving reCAPTCHA: {str(e)}")
    
def check_recaptcha():
    driver = manager.get_driver()
    try:
        wait = WebDriverWait(driver, 5)
        # Wait until the iframe is present in the DOM and accessible
        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='The reCAPTCHA challenge expires in two minutes']"))
        )
        # Locate the reCAPTCHA iframe
        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha/api2/bframe')]"))
        )
        # Extract the 'src' attribute from the iframe
        iframe_src = iframe.get_attribute("src")
        # Look for the 'k=' parameter in the URL
        from urllib.parse import urlparse, parse_qs
        query_params = parse_qs(urlparse(iframe_src).query)
        # Return the 'sitekey' value
        site_key = query_params.get('k', [None])[0]
        print("ReCAPTCHA detected!")
        return site_key
    except:
        return False


def pesquisaprotesto_search_protests(cnpj):
    """
    Searches for protests on the 'pesquisaprotesto.com.br' website for the provided CNPJ.
    """
    driver = manager.get_driver()
    # URL for the document consultation page
    consulta_url = "https://www.pesquisaprotesto.com.br/servico/consulta-documento"
    # Access the consultation page
    driver.get(consulta_url)

    time.sleep(random.uniform(1, 5))

    # Check if the user is logged in
    if not is_logged_in():
        print("User is not logged in, performing login on pesquisaprotesto.com.br")
        pesquisaprotesto_login()
        # Access the consultation page
        driver.get(consulta_url)
    
    try:
        # Wait for the page to load
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        formatted_cnpj = format_cnpj(cnpj)
        # Locate the CPF/CNPJ field and fill it with the formatted CNPJ
        cnpj_input = wait.until(EC.presence_of_element_located((By.ID, "cpf_cnpj")))
        cnpj_input.clear()
        for char in formatted_cnpj:
            cnpj_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.5))

        # Locate the "Consultar" button and click it
        consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
        driver.execute_script("arguments[0].click();", consultar_button)

        time.sleep(random.uniform(1, 5))

        try:
            # Wait for the search results
            wait = WebDriverWait(driver, 10)
            result_text = wait.until(
                EC.presence_of_element_located((
                    By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                ))
            )
        except:
            try:
                # Locate the "Consultar" button and click it
                consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
                driver.execute_script("arguments[0].click();", consultar_button)
                time.sleep(random.uniform(1, 5))
                # Aguardar o resultado da busca
                wait = WebDriverWait(driver, 10)
                result_text = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                    ))
                )
            except:
                print("\nResolving reCAPTCHA...")
                try:
                    solve_recaptcha()
                    driver.switch_to.default_content()
                    # Wait for the search results
                    wait = WebDriverWait(driver, 10)
                    result_text = wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                        ))
                    )
                except:
                    manager.restart_driver()
                    # Retry the search process from the beginning
                    return pesquisaprotesto_search_protests(cnpj)

        # Extract and return the result text
        search_result = result_text.text.split(f'\n')[0]

        time.sleep(random.uniform(1, 5))

        # Scroll down the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        if search_result == 'Constam protestos nos cartórios participantes do Brasil':
            # Logic to handle protest details, aggregating quantities and values
            total_protests = 0
            total_protested_value = 0.0

            tables = driver.find_elements(By.XPATH, "//table[@role='table']")
            for table in tables:
                rows = table.find_elements(By.XPATH, ".//tbody/tr")
                for row in rows:
                    details_button = row.find_element(By.XPATH, ".//button[text()='Detalhes']")
                    details_button.click()
                    time.sleep(random.uniform(1, 5))

                    wait = WebDriverWait(driver, 5)
                    protest_count = wait.until(EC.presence_of_element_located((By.XPATH, "//p[b[text()='Quantidade de protestos:']]")))
                    protest_count_value = int(protest_count.text.split(':')[1].strip() if protest_count else 0)
                    total_protests += protest_count_value

                    protested_values = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='list-group']//p[b[text()='Valor Protestado: ']]")))

                    for item in protested_values:
                        numbers = re.findall(r'\d+[.]?\d*', item.text)
                        if numbers:
                            value = float(numbers[0].replace('.', '').replace(',', '.')) + (float(numbers[1]) / 100)
                            total_protested_value += value

                    close_button = driver.find_element(By.XPATH, '//button[@type="button" and @aria-label="Close"]')
                    close_button.click()
                    time.sleep(random.uniform(1, 5))
        else:
            # If no protests are found, set totals to zero
            total_protests = 0
            total_protested_value = 0.0

        # Return aggregated results
        return total_protests, total_protested_value
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def fetch_instagram_followers(company_name):
    """
    Fetches the number of followers from the company's Instagram page based on its name.
    
    Args:
        company_name (str): The name of the company.

    Returns:
        tuple: Instagram URL and the number of followers.
    """
    driver = manager.get_driver()
    url = f"https://www.instagram.com/{company_name.replace('-', '').replace('.', '').lower()}/"

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)

        followers_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(@class, 'x5n08af') and @title]")
            )
        )

        followers = followers_element.get_attribute("title")
        return url, int(followers.replace('.', ''))

    except Exception:
        return np.nan, np.nan

def fetch_facebook_followers(company_name):
    """
    Fetches the number of followers from the company's Facebook page based on its name.

    Args:
        company_name (str): The name of the company.

    Returns:
        tuple: Facebook URL and the number of followers.
    """
    driver = manager.get_driver()
    url = f"https://www.facebook.com/{company_name.replace('-', '').replace('.', '').lower()}/"

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)

        try:
            wait.until(
                EC.visibility_of_element_located((By.ID, "login_popup_cta_form"))
            )
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Fechar' and @role='button']"))
            )
            close_button.click()
        except Exception:
            pass

        followers_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@class, 'x1i10hfl') and contains(text(), 'seguidores')]")
            )
        )

        return url, followers_element.text.split('seguidores ')[1]
    except Exception:
        return np.nan, np.nan

def fetch_government_contracts(cnpj):
    """
    Checks for contracts in the Transparency Portal for a given CPF or CNPJ.

    Args:
        cnpj (str): CPF or CNPJ to be queried.

    Returns:
        bool: Whether the company has contracts with the government.
    """
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos/cpf-cnpj"

    headers = {
        "Accept": "application/json",
        "chave-api-dados": os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
    }

    params = {
        "cpfCnpj": cnpj,
        "pagina": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return len(data) > 0
    except:
        return False

def fetch_company_data(cnpj):
    """
    Fetches company data based on its CNPJ, including followers on social media and government contracts.

    Args:
        cnpj (str): The company's CNPJ.

    Returns:
        dict: Consolidated company data.
    """
    cnpj_data = fetch_cnpj_data(cnpj)
    if cnpj_data['fantasia']:
        raw_name = cnpj_data['fantasia']
    else:
        raw_name = cnpj_data['nome']

    raw_name = (
        unidecode(raw_name.lower())
        .replace(" ", "-")
        .replace(",", "")
        .replace("+", "mais")
    )

    remove_words = r'\b(comercio-de-medicamentos|ltda|eireli|me|sa|s\/a|epp|limitada|sociedade-anonima|com-br)\b'
    company_name = re.sub(remove_words, '', raw_name, flags=re.IGNORECASE).strip('-')

    total_protests, total_protested_value = pesquisaprotesto_search_protests(cnpj)
    government_contracts = fetch_government_contracts(cnpj)
    last_update = datetime.strptime(cnpj_data['ultima_atualizacao'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%Y')

    url_insta, followers_insta = fetch_instagram_followers(company_name)
    url_facebook, followers_facebook = fetch_facebook_followers(company_name)

    return {
        'cnpj': cnpj,
        'name': company_name,
        'state': cnpj_data['uf'],
        'status': cnpj_data['situacao'],
        'last_update': last_update,
        'type': cnpj_data['tipo'],
        'registration_status': cnpj_data['status'],
        'main_activity_code': cnpj_data['atividade_principal'][0]['code'],
        'main_activity': cnpj_data['atividade_principal'][0]['text'],
        'size': cnpj_data['porte'],
        'social_capital': float(cnpj_data['capital_social']),
        'protests': total_protests,
        'protested_value': total_protested_value,
        'government_contracts': government_contracts,
        'instagram_url': url_insta,
        'instagram_followers': followers_insta,
        'facebook_url': url_facebook,
        'facebook_followers': followers_facebook
    }