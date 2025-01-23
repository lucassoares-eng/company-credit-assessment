import time
import pickle
import traceback
import numpy as np
import requests
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from dotenv import load_dotenv
from unidecode import unidecode
from datetime import datetime
import urllib3
import zipfile
import platform
import random
import urllib.request
import speech_recognition as sr

# Desabilitar avisos de solicitações HTTPS não verificadas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregar variáveis do arquivo .env
load_dotenv()

# Caminhos e configurações
insta_cookies_file = "instagram_cookies.pkl"
insta_url = "https://www.instagram.com"

class DriverManager:
    def __init__(self, insta_url, inst_cookies_file):
        self.insta_url = insta_url
        self.inst_cookies_file = inst_cookies_file
        self.driver = self._initialize_driver(wait_login=False)
        self.chrome_version= get_chrome_version()
        self.chromedriver_url = get_chromedriver_url(self.chrome_version)
        self.chromedriver_update = atualizar_chromedriver(self.chromedriver_url)
    def _initialize_driver(self, wait_login=True):
        """
        Inicializa o WebDriver do Chrome.
        """
        driver = initialize_driver()
        if os.path.exists(self.inst_cookies_file):
            while True:
                try:
                    driver.set_page_load_timeout(30)
                    driver.get(insta_url)
                    break
                except Exception as e:
                    print(f'Erro ao inicializar driver: {e}')
                    driver.quit()
                    driver = initialize_driver()
            self.load_cookies(driver, self.inst_cookies_file)  # Função de carregamento de cookies
        if wait_login:
            input('Faça login no Instagrama e pressione ENTER para continuar')
        self.save_cookies(driver, self.inst_cookies_file)
        return driver
    def reiniciar_driver(self):
        """
        Reinicia o WebDriver e carrega os cookies.
        """
        # Salvar os cookies atuais
        if self.driver:
            self.driver.get(self.insta_url)
            self.save_cookies(self.driver, self.inst_cookies_file)
            self.driver.quit()
            random_sleep = int(random.uniform(30, 90))
            print(f"Driver encerrado, aguardando {random_sleep} segundos para reiniciar...")
            time.sleep(random_sleep)
        # Inicializar novamente o driver
        self.driver = self._initialize_driver(wait_login=False)
        pesquisaprotesto_realizar_login()
        print("Driver reiniciado com sucesso!")
    def get_driver(self):
        return self.driver
    @staticmethod
    def load_cookies(driver, file_path):
        try:
            # Carregar cookies do arquivo
            with open(file_path, "rb") as file:
                cookies = pickle.load(file)
            
            for cookie in cookies:
                # Ajustar o domínio, se necessário
                if "sameSite" in cookie:
                    cookie.pop("sameSite")  # Remove para evitar erros
                
                try:
                    driver.add_cookie(cookie)
                except WebDriverException as e:
                    print(f"Erro ao adicionar cookie {cookie.get('name')}: {e}")
            driver.refresh()  # Recarregar a página para aplicar os cookies
            print("Cookies carregados com sucesso.")
        except FileNotFoundError:
            print(f"Arquivo de cookies '{file_path}' não encontrado.")
        except Exception as e:
            print(f"Erro ao carregar cookies: {e}")
            manager.reiniciar_driver()
    @staticmethod
    def save_cookies(driver, file_path):
        """
        Salva os cookies atuais do WebDriver em um arquivo.
        """
        try:
            cookies = driver.get_cookies()
            with open(file_path, "wb") as file:
                pickle.dump(cookies, file)
            print("Cookies salvos com sucesso.")
        except Exception as e:
            print(f"Erro ao salvar cookies: {e}")

def check_and_setup_ffmpeg():
    """Verifica se o FFmpeg está presente, baixa e configura se necessário."""
    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg")
    ffmpeg_exe = os.path.join(ffmpeg_dir, "bin", "ffmpeg.exe")
    
    # Verificar se o FFmpeg já está configurado
    if not os.path.exists(ffmpeg_exe):
        print("FFmpeg não encontrado. Baixando e configurando...")
        
        # URL do FFmpeg (versão estática para Windows)
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(os.getcwd(), "ffmpeg.zip")
        
        # Download do FFmpeg
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        print("Download concluído. Extraindo arquivos...")
        
        # Extração dos arquivos
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        os.remove(zip_path)  # Remove o arquivo zip após extração
        
        # Renomeia a pasta extraída para padronizar
        extracted_dir = next((d for d in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, d))), None)
        if extracted_dir:
            extracted_path = os.path.join(ffmpeg_dir, extracted_dir)
            for item in os.listdir(extracted_path):
                os.rename(os.path.join(extracted_path, item), os.path.join(ffmpeg_dir, item))
            os.rmdir(extracted_path)  # Remove a pasta intermediária

    
    # Configurar o Pydub para usar o FFmpeg
    if not os.path.exists(ffmpeg_exe):
        raise FileNotFoundError("FFmpeg não foi encontrado ou configurado corretamente.")

    # Adiciona o caminho ffmpeg_exe ao PATH
    os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_exe)

    return ffmpeg_exe

# Chamar a função para verificar e configurar o FFmpeg
ffmpeg_exe = check_and_setup_ffmpeg()

from pydub import AudioSegment
AudioSegment.converter = ffmpeg_exe

def convert_to_wav(input_path, output_path="converted_audio.wav"):
    """Converte um arquivo de áudio para o formato WAV."""
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path

def download_audio(audio_url, save_path):
    """Faz o download do arquivo de áudio."""
    response = requests.get(audio_url, verify=False)
    with open(save_path, "wb") as file:
        file.write(response.content)
    return save_path

def transcribe_audio(audio_path):
    """Transcreve o áudio usando SpeechRecognition."""
    recognizer = sr.Recognizer()

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {audio_path}")
    
    # Converte o áudio para WAV se necessário
    if not audio_path.endswith(".wav"):
        audio_path = convert_to_wav(audio_path)
    
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return None

# Função para obter a versão atual do Chrome instalada no sistema
def get_chrome_version():
    try:
        stream = os.popen(r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version')
        output = stream.read()
        return output.split()[-1]
    except Exception as e:
        raise RuntimeError("Não foi possível obter a versão do Chrome instalada.") from e

# Função para identificar o sistema operacional
def get_os_type():
    system = platform.system().lower()
    if system == "windows":
        return "win64"
    elif system == "linux":
        return "linux64"
    elif system == "darwin":  # macOS
        return "mac64"
    else:
        raise RuntimeError(f"Sistema operacional não suportado: {system}")

# Função para obter a URL do ChromeDriver com base no CfT
def get_chromedriver_url(version):
    major_version = version.split('.')[0]  # Obtem a versão principal
    base_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    response = requests.get(base_url, verify=False)
    if response.status_code == 200:
        data = response.json()
        for entry in data["versions"]:
            if entry["version"].startswith(major_version):
                os_type = get_os_type()
                # Verifica a URL do Chrome para o sistema operacional adequado
                for download in entry["downloads"]["chromedriver"]:
                    if download["platform"] == os_type:
                        return download["url"]
                raise RuntimeError(f"Versão do Chrome para {os_type} não encontrada.")
    raise RuntimeError(f"Não foi possível localizar o Chrome para a versão {version}.")

# Função para baixar e extrair o ChromeDriver
def download_chromedriver(url):
    # Verifica se a pasta 'chromedriver' existe, se não, cria
    if not os.path.exists('chromedriver'):
        os.makedirs('chromedriver')
    
    # Realiza o download do arquivo ZIP do ChromeDriver
    response = requests.get(url, stream=True, verify=False)
    if response.status_code == 200:
        zip_path = "chromedriver/chromedriver.zip"
        with open(zip_path, "wb") as file:
            file.write(response.content)
        
        # Extrai o conteúdo do ZIP diretamente para a pasta 'chromedriver'
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Extrai todos os arquivos diretamente para 'chromedriver/'
            for file in zip_ref.namelist():
                zip_ref.extract(file, 'chromedriver')
        
        # Remove o arquivo ZIP após a extração
        os.remove(zip_path)
    else:
        raise RuntimeError(f"Erro ao baixar o ChromeDriver: {response.status_code}")
    
def atualizar_chromedriver(chromedriver_url):
    try:
        download_chromedriver(chromedriver_url)
    except Exception as e:
        print(f'Não foi possível atualizar o chromedriver: {e}')

# Iniciar o driver com as opções configuradas
def initialize_driver():
    # Configurações para o Chrome
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
    # Caminho para o ChromeDriver
    driver_path = f"chromedriver/chromedriver-{get_os_type()}/chromedriver.exe" 
    # Configurar o serviço do ChromeDriver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

manager = DriverManager(insta_url, insta_cookies_file)

def format_cnpj(cnpj):
    """Formata o CNPJ no formato 00.000.000/0000-00"""
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

# Função para buscar dados empresariais de CNPJ
def fetch_cnpj_data(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        # Aguardar antes de tentar novamente
        retry_after = int(response.headers.get('Retry-After', 30))
        print(f"Aguardando {retry_after} segundos antes de tentar novamente...")
        time.sleep(retry_after)
        return fetch_cnpj_data(cnpj)  # Tenta novamente após o tempo de espera
    else:
        return {"error": f"Unable to fetch CNPJ data: {response.status_code}"}

# Função para buscar reclamações e reputação no Reclame Aqui (usando web scraping como exemplo)
def fetch_reputation(company_name):
    driver = manager.get_driver()
    # Função auxiliar para buscar dados
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
            # Captura outros erros não previstos e retorna None
            return np.nan

    # Primeira tentativa com o nome original
    search_url = f"https://www.reclameaqui.com.br/empresa/{company_name}/"
    rating = try_fetch(search_url)

    # Se não encontrar, tenta sem os hífens
    if rating is np.nan and '-' in company_name:
        search_url_alternate = f"https://www.reclameaqui.com.br/empresa/{company_name.replace('-', '')}/"
        rating = try_fetch(search_url_alternate)

    # Retorna 0 se não for possível buscar a reputação ou em caso de erro/404
    return rating

# Função para buscar processos fiscais e protestos em tribunais do estado de SP
def consulta_protestos_sp(cnpj):
    driver = manager.get_driver()
    formatted_cnpj = format_cnpj(cnpj)
    try:    
        # Abrir a página
        search_url = "https://protestosp.com.br/consulta-de-protesto"
        driver.get(search_url)

        wait = WebDriverWait(driver, 5)
    
        # Selecionar "CNPJ" no campo de tipo de documento
        tipo_documento = wait.until(EC.presence_of_element_located((By.ID, "TipoDocumento")))
        Select(tipo_documento).select_by_visible_text("CNPJ")
    
        # Localizar o campo de documento
        input_field = wait.until(EC.visibility_of_element_located((By.ID, "Documento")))
    
        # Preencher o CNPJ no campo de entrada
        input_field.clear()
        input_field.send_keys(formatted_cnpj)
    
        # Localizar o botão "CONSULTAR" pelo atributo de classe ou valor
        consult_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='CONSULTAR']"))
        )
    
        # Clicar no botão
        consult_button.click()

        wait = WebDriverWait(driver, 10)
    
        # Aguardar os resultados e capturá-los
        resultados = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "labelTotalSP")))
        return {"resultados": resultados.text}
    
    except Exception as e:
        return {"error": f"Unable to fetch CNPJ data: {e}"}

# Função para buscar processos fiscais e protestos em tribunais de várias estados
def pesquisaprotesto_realizar_login():
    """
    Realiza o login no site 'pesquisaprotesto.com.br' com o usuário e senha fornecidos.
    Solicita validação por e-mail, insere o código de validação e confirma.
    
    Args:
        driver: Instância do WebDriver.
        usuario (str): Nome de usuário.
        senha (str): Senha.
    """

    driver = manager.get_driver()
    # Carregar as credenciais do arquivo .env
    usuario = os.getenv("PESQUISAPROTESTO_USUARIO")  # Variável de ambiente USUARIO
    senha = os.getenv("PESQUISAPROTESTO_SENHA")  # Variável de ambiente SENHA
        
    login_url = "https://www.pesquisaprotesto.com.br/login"
    driver.get(login_url)
    wait = WebDriverWait(driver, 5)

    # Preencher o campo de usuário
    usuario_input = wait.until(
        EC.visibility_of_element_located((By.ID, "usario"))
    )
    usuario_input.clear()
    usuario_input.send_keys(usuario)

    # Preencher o campo de senha
    senha_input = wait.until(
        EC.visibility_of_element_located((By.ID, "senha"))
    )
    senha_input.clear()
    senha_input.send_keys(senha)

    # Clicar em Manter-me conectado
    mantem_conectado = wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'manter-logado-container')]"))
    )
    # Clicar no div mãe
    mantem_conectado.click()

    # Clicar no botão "Entrar"
    entrar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar')]"))
    )
    driver.execute_script("arguments[0].click();", entrar_button)

    # Esperar o botão "Continuar" ficar clicável
    continuar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-success btn-lg' and text()='Continuar']"))
    )
    continuar_button.click()

    # Verificar se a validação por e-mail aparece
    try:
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//h3[text()='Valide por E-mail']"))
        )
        print("Para continuar o login é necessário informar o código de acesso enviado para o email cadastrado")

        # Selecionar o botão de rádio
        radio_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @value='email']"))
        )
        driver.execute_script("arguments[0].click();", radio_button)

        # Aguardar o botão "ENVIAR CÓDIGO" ficar habilitado e clicá-lo
        enviar_codigo_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ENVIAR CÓDIGO')]"))
        )
        driver.execute_script("arguments[0].click();", enviar_codigo_button)

        # Após clicar em "ENVIAR CÓDIGO", esperar que os campos de input apareçam
        inputs = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//input[@maxlength='1' and @class='token-login-input']"))
        )

        # Solicitar o código ao usuário
        codigo = input("Digite o código recebido no e-mail (6 dígitos): ")

        # Validar se o código tem o tamanho correto
        if len(codigo) != 6:
            raise ValueError("O código deve conter exatamente 6 dígitos numéricos.")

        # Preencher cada campo com os caracteres do código
        for i, input_field in enumerate(inputs):
            input_field.clear()
            input_field.send_keys(codigo[i])
        print(f"Código '{codigo}' preenchido")

        # Aguardar e clicar no botão "Confirmar código"
        confirmar_button = wait.until(
            EC.element_to_be_clickable((By.ID, "btnConfirmaToken2fa"))
        )
        driver.execute_script("arguments[0].click();", confirmar_button)
    
    except:
        pass
    time.sleep(5)

def pesquisaprotesto_verificar_login():
    """
    Verifica se o usuário está logado no site 'pesquisaprotesto.com.br'.
    Retorna True se estiver logado, caso contrário, False.
    """
    driver = manager.get_driver()
    try:
        # Espera até o botão de usuário ser visível (indicando que o usuário está logado)
        user_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "__BVID__67__BV_toggle_"))
        )
        if user_button.is_displayed():
            return True  # Usuário está logado
        return False  # Usuário não está logado
    except Exception as e:
        return False  # Caso não encontre o botão ou ocorra algum erro
    

def resolver_recaptcha():
    driver = manager.get_driver()

    try:
        wait = WebDriverWait(driver, 5)

        # Esperar até que o iframe esteja presente no DOM e acessível
        iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='o desafio reCAPTCHA expira em dois minutos']")))
        # Trocar o contexto para o iframe encontrado
        driver.switch_to.frame(iframe)
        
        # Esperar até que o botão de áudio esteja presente e clicável
        audio_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
        audio_button.click()
        audio_source = wait.until(EC.presence_of_element_located((By.ID, "audio-source"))).get_attribute("src")
        audio_path = download_audio(audio_source, "recaptcha_audio.mp3")

        response = transcribe_audio(audio_path)

        # Localizar o campo de entrada 'audio-response'
        audio_response_input = wait.until(EC.presence_of_element_located((By.ID, "audio-response")))
        # Preencher o campo de entrada com o texto transcrito
        # Digitar cada caractere com um pequeno atraso
        for char in response:
            audio_response_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.5))
        time.sleep(random.uniform(0.3, 1))

        # Esperar até que o botão de verificação esteja presente e clicável
        verify_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
        # Clicar no botão de verificação
        verify_button.click()

        time.sleep(random.uniform(1, 5))

    except Exception as e:
        tb_str = traceback.format_exc()  # Obter o traceback como string
        raise RuntimeError(f"Erro ao resolver o reCAPTCHA: {tb_str} \n{e}")

def verificar_recaptcha(verbose=True):
    driver = manager.get_driver()
    try:
        wait = WebDriverWait(driver, 5)
        # Esperar até que o iframe esteja presente no DOM e acessível
        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@title='o desafio reCAPTCHA expira em dois minutos']"))
        )
        # Localizar o iframe do reCAPTCHA
        iframe = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha/api2/bframe')]"))
        )
        # Extrair o atributo 'src' do iframe
        iframe_src = iframe.get_attribute("src")
        # Procurar o parâmetro 'k=' na URL
        from urllib.parse import urlparse, parse_qs
        query_params = parse_qs(urlparse(iframe_src).query)
        # Retornar o valor da 'sitekey'
        site_key = query_params.get('k', [None])[0]
        if verbose:
            print("ReCAPTCHA detectado!")
        return site_key
    except:
        return False

def pesquisaprotesto_buscar_protestos(cnpj):
    """
    Realiza a busca de protestos no site 'pesquisaprotesto.com.br' para o CNPJ fornecido.
    """
    driver = manager.get_driver()
    # URL da página de consulta de documentos
    consulta_url = "https://www.pesquisaprotesto.com.br/servico/consulta-documento"
    # Acessar a página de consulta
    driver.get(consulta_url)

    time.sleep(random.uniform(1, 5))

    # Verificar se o usuário está logado
    if not pesquisaprotesto_verificar_login():
        print("Usuário não está logado, realizando login em pesquisaprotesto.com")
        pesquisaprotesto_realizar_login()
        # Acessar a página de consulta
        driver.get(consulta_url)
    
    try:
        # Aguardar a página carregar
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        formatted_cnpj = format_cnpj(cnpj)
        # Localizar o campo de CPF/CNPJ e preencher com o CNPJ formatado
        cnpj_input = wait.until(EC.presence_of_element_located((By.ID, "cpf_cnpj")))
        cnpj_input.clear()
        for char in formatted_cnpj:
            cnpj_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.5))

        # Localizar o botão "Consultar" e clicar
        consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
        # Executar o script diretamente no botão "Consultar"
        driver.execute_script("arguments[0].click();", consultar_button)

        time.sleep(random.uniform(1, 5))

        try:
            # Aguardar o resultado da busca
            wait = WebDriverWait(driver, 10)
            resultado_texto = wait.until(
                EC.presence_of_element_located((
                    By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                ))
            )
        except:
            try:
                # Localizar o botão "Consultar" e clicar
                consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
                # Executar o script diretamente no botão "Consultar"
                driver.execute_script("arguments[0].click();", consultar_button)
                time.sleep(random.uniform(1, 5))
                # Aguardar o resultado da busca
                wait = WebDriverWait(driver, 10)
                resultado_texto = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                    ))
                )
            except:
                print('\nResolvendo re-Captacha...')
                try:
                    resolver_recaptcha()
                    driver.switch_to.default_content()
                    # Aguardar o resultado da busca
                    wait = WebDriverWait(driver, 10)
                    resultado_texto = wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                        ))
                    )
                except:
                    manager.reiniciar_driver()
                    driver = manager.get_driver()
                    # Acessar a página de consulta
                    driver.get(consulta_url)
                    time.sleep(random.uniform(1, 5))
                    # Aguardar a página carregar
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                    formatted_cnpj = format_cnpj(cnpj)
                    # Localizar o campo de CPF/CNPJ e preencher com o CNPJ formatado
                    cnpj_input = wait.until(EC.presence_of_element_located((By.ID, "cpf_cnpj")))
                    cnpj_input.clear()
                    for char in formatted_cnpj:
                        cnpj_input.send_keys(char)
                        time.sleep(random.uniform(0.1, 0.5))

                    # Localizar o botão "Consultar" e clicar
                    consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
                    # Executar o script diretamente no botão "Consultar"
                    driver.execute_script("arguments[0].click();", consultar_button)

                    time.sleep(random.uniform(1, 5))                
                    try:
                        # Aguardar o resultado da busca
                        wait = WebDriverWait(driver, 10)
                        resultado_texto = wait.until(
                            EC.presence_of_element_located((
                                By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                            ))
                        )
                    except:
                        try:
                            # Localizar o botão "Consultar" e clicar
                            consultar_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "bt-consultar")))
                            # Executar o script diretamente no botão "Consultar"
                            driver.execute_script("arguments[0].click();", consultar_button)
                            time.sleep(random.uniform(1, 5))
                            # Aguardar o resultado da busca
                            wait = WebDriverWait(driver, 10)
                            resultado_texto = wait.until(
                                EC.presence_of_element_located((
                                    By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                                ))
                            )
                        except:
                            print('\nResolvendo re-Captacha...')
                            resolver_recaptcha()
                            driver.switch_to.default_content()
                            # Aguardar o resultado da busca
                            wait = WebDriverWait(driver, 10)
                            resultado_texto = wait.until(
                                EC.presence_of_element_located((
                                    By.XPATH, "//div[@class='alert alert-light shadow-sm mb-5 cardCel']"
                                ))
                            )

        # Capturar e retornar o texto do resultado
        texto_resultado = resultado_texto.text.split(f'\n')[0]

        time.sleep(random.uniform(1, 5))

        # Rolar a página para baixo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Se o texto for igual ao esperado, clicar no botão "Detalhes"
        if texto_resultado == 'Constam protestos nos cartórios participantes do Brasil':
            # Localize as tabelas na página
            tabelas = driver.find_elements(By.XPATH, "//table[@role='table']")

            # Inicialize variáveis para armazenar as somas
            total_quantidade_protestos = 0
            total_valor_protestado = 0.0

            for tabela in tabelas:
                # Localize todas as linhas da tabela (exceto o cabeçalho)
                linhas = tabela.find_elements(By.XPATH, ".//tbody/tr")
                for linha in linhas:
                    # Clicar no botão "Detalhes" correspondente à linha
                    detalhes_button = linha.find_element(By.XPATH, ".//button[text()='Detalhes']")
                    detalhes_button.click()
                    
                    # Esperar a janela de detalhes abrir
                    time.sleep(random.uniform(1, 5))

                    wait = WebDriverWait(driver, 5)
                    # Quantidade de protestos
                    quantidade_protestos = wait.until(EC.presence_of_element_located((By.XPATH, "//p[b[text()='Quantidade de protestos:']]")))
                    quantidade_protestos_value = int(quantidade_protestos.text.split(':')[1].strip() if quantidade_protestos else 0)
                    # Atualizar a soma total de protestos
                    total_quantidade_protestos += quantidade_protestos_value
                    
                    # Extrair o valor protestado
                    valor_protestado = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='list-group']//p[b[text()='Valor Protestado: ']]")))

                    # Somar os valores dos protestos e valores protestados
                    for item in valor_protestado:
                        numero = re.findall(r'\d+[.]?\d*', item.text)
                        if numero:
                            valor = float(numero[0].replace('.', '').replace(',', '.')) + (float(numero[1])/100)
                            total_valor_protestado += valor

                    # Fechar a janela de detalhes clicando no botão "Fechar"
                    close_button = driver.find_element(By.XPATH, '//button[@type="button" and @aria-label="Close"]')
                    close_button.click()

                    # Aguardar o carregamento da página
                    time.sleep(random.uniform(1, 5))      

        else:
            # Caso o texto seja diferente, retornar 0 para ambos os valores
            total_quantidade_protestos = 0
            total_valor_protestado = 0
        
        # Retornar os valores capturados
        return total_quantidade_protestos, total_valor_protestado
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar protestos cnpj {cnpj}: {e}")

# Função para buscar número de seguidores no instagram
def fetch_instagram_followers(company_name):
    """
    Retorna o número de seguidores da página do Instagram baseada no nome da empresa.
    """
    driver = manager.get_driver()
    url = f"https://www.instagram.com/{company_name.replace('-', '').replace('.', '').lower()}/"  # Formata o URL da empresa

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)

        # Aguarda e busca o elemento contendo o número de seguidores
        followers_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(@class, 'x5n08af') and @title]")
            )
        )

        # Extrai o valor do atributo 'title', que contém o número de seguidores
        followers = followers_element.get_attribute("title")

        return url, int(followers.replace('.', ''))

    except Exception:
        return np.nan, np.nan
    
# Função para buscar número de seguidores no facebook
def fetch_facebook_followers(company_name):
    """
    Retorna o número de seguidores da página do Instagram baseada no nome da empresa.
    """
    driver = manager.get_driver()
    url = f"https://www.facebook.com/{company_name.replace('-', '').replace('.', '').lower()}/"  # Formata o URL da empresa

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        
        # Aguardar até que o formulário apareça na tela
        try:
            # Espera até o formulário estar visível (ajustar o seletor conforme necessário)
            form = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "login_popup_cta_form"))
            )
            
            # Espera até o botão de fechar estar clicável
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Fechar' and @role='button']"))
            )
            # Clicar no botão de fechar
            close_button.click()
        except Exception as e:
            pass

        # Aguarda e busca o elemento contendo o número de seguidores
        followers_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@class, 'x1i10hfl') and contains(text(), 'seguidores')]")
            )
        )
        
        return url, followers_element.text.split('seguidores ')[1]
    except Exception:
        return np.nan, np.nan

# Função para buscar relações com o governo no Portal da Transparência
def consultar_contratos_governo(cnpj):
    """
    Consulta contratos do Portal da Transparência para um dado CPF ou CNPJ.

    Args:
        cnpj (str): CPF ou CNPJ do contratado a ser consultado.

    Returns:
        boolean
    """
    # URL da API
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos/cpf-cnpj"
    
    # Headers com a chave da API carregada do .env
    headers = {
        "Accept": "application/json",
        "chave-api-dados": os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
    }
    
    # Parâmetros de consulta
    params = {
        "cpfCnpj": cnpj,
        "pagina": 1
    }

    try:
        # Fazer a solicitação GET
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Levanta exceções para códigos de erro HTTP

        # Verificar se a resposta é válida e retorna um JSON
        data = response.json()
        if len(data) > 0:
            return True
        else:
            return False
    except:
        return False
    
def consulta_cnpj(cnpj):
    cnpj_data = fetch_cnpj_data(cnpj)
    if not cnpj_data['fantasia'] == '':
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
    total_quantidade_protestos, total_valor_protestado = pesquisaprotesto_buscar_protestos(cnpj)
    contratos_governo = consultar_contratos_governo(cnpj)
    ultima_atualização = datetime.strptime(cnpj_data['ultima_atualizacao'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%Y')
    url_insta, seguidores_insta = fetch_instagram_followers(company_name)
    url_facebook, seguidores_facebook = fetch_facebook_followers(company_name)

    res = {
        'cnpj' : cnpj,
        'nome': company_name,
        'situacao' : cnpj_data['situacao'],
        'ultima_atualizacao' : ultima_atualização,
        'tipo' : cnpj_data['tipo'],
        'status' : cnpj_data['status'],
        'cod_atividade_principal' : cnpj_data['atividade_principal'][0]['code'],
        'atividade_principal' : cnpj_data['atividade_principal'][0]['text'],
        'porte' : cnpj_data['porte'],
        'capital_social' : float(cnpj_data['capital_social']),
        'protestos' : total_quantidade_protestos,
        'valor_protestado' : total_valor_protestado,
        'contratos_publico' : contratos_governo,
        'instagram' : url_insta,
        'seguidores_instagram' : seguidores_insta,
        'facebook' : url_facebook,
        'seguidores_facebook' : seguidores_facebook
    }

    return res