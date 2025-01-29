# Credit Analysis API

This API provides several functionalities to obtain data about companies, including CNPJ information, social media profiles, protests, and government contracts. The API is built with Flask and provides endpoints to access this data.

## API Endpoints

### 1. **`/company-data`** - Displays CNPJ information
- **Method**: `GET`
- **Parameter**: `cnpj` (required) – The CNPJ of the company.
- **Description**: Returns detailed information about the company based on its CNPJ, including data about the company, protests, government contracts, social media, etc.
- **Example response**:
    ```json
    {
        "cnpj": "12345678000195",
        "name": "Example Company",
        "state": "SP",
        "status": "Active",
        "social_capital": 500000.00,
        "protests": 2,
        "protested_value": 15000.00,
        "government_contracts": true,
        "instagram_url": "https://www.instagram.com/examplecompany",
        "instagram_followers": 1500,
        "facebook_url": "https://www.facebook.com/examplecompany",
        "facebook_followers": 2000
    }
    ```

### 2. **`/reputation`** - Checks a company's reputation on Reclame Aqui
- **Method**: `GET`
- **Parameter**: `company_name` (required) – The name of the company.
- **Description**: Returns the company's rating on Reclame Aqui.
- **Example response**:
    ```json
    {
        "company_name": "Example Company",
        "rating": 4.5
    }
    ```

### 3. **`/protests`** - Checks protests against a company using its CNPJ
- **Method**: `GET`
- **Parameter**: `cnpj` (required) – The CNPJ of the company.
- **Description**: Returns information about protests registered against the company.
- **Example response**:
    ```json
    {
        "cnpj": "12345678000195",
        "total_protests": 2,
        "total_protested_value": 15000.00
    }
    ```

### 4. **`/instagram-followers`** - Fetches the number of Instagram followers for a company
- **Method**: `GET`
- **Parameter**: `company_name` (required) – The name of the company.
- **Description**: Returns the number of Instagram followers for the company.
- **Example response**:
    ```json
    {
        "company_name": "Example Company",
        "instagram_url": "https://www.instagram.com/examplecompany",
        "followers": 1500
    }
    ```

### 5. **`/facebook-followers`** - Fetches the number of Facebook followers for a company
- **Method**: `GET`
- **Parameter**: `company_name` (required) – The name of the company.
- **Description**: Returns the number of Facebook followers for the company.
- **Example response**:
    ```json
    {
        "company_name": "Example Company",
        "facebook_url": "https://www.facebook.com/examplecompany",
        "followers": 2000
    }
    ```

### 6. **`/government-contracts`** - Checks if a company has government contracts using its CNPJ
- **Method**: `GET`
- **Parameter**: `cnpj` (required) – The CNPJ of the company.
- **Description**: Returns whether or not the company has government contracts.
- **Example response**:
    ```json
    {
        "cnpj": "12345678000195",
        "has_government_contracts": true
    }
    ```

### 7. **`/cnpj-data`** - Fetches the CNPJ data of a company
- **Method**: `GET`
- **Parameter**: `cnpj` (required) – The CNPJ of the company.
- **Description**: Returns detailed CNPJ data of the company from the Receita Federal (Brazilian Federal Revenue).
- **Example response**:
    ```json
    {
        "cnpj": "12345678000195",
        "name": "Example Company",
        "status": "Active",
        "type": "Ltd",
        "social_capital": 1000000.00
    }
    ```

## ReCAPTCHA Solver

This module provides an automated way to solve Google reCAPTCHA challenges using audio-based recognition. It downloads the reCAPTCHA audio challenge, transcribes it using speech-to-text services, and submits the response automatically.

### Features

- Automates solving of Google reCAPTCHA challenges
- Uses speech-to-text to decode audio challenges
- Handles reCAPTCHA v2 (audio challenges)
- Verifies the installation of FFmpeg and configures it automatically

### Usage
```bash
from recaptcha_solver import ReCAPTCHASolver

solver = ReCAPTCHASolver()
solver.solve_recaptcha(driver)
```

## Example of using the API

To make a request to check information for a company with CNPJ `12345678000195`, you can do the following:

```bash
GET /cnpj?cnpj=12345678000195
```

## Requirements

- Python 3.x
- flask==3.0.3
- flask-swagger-ui==4.11.1
- requests==2.31.0
- selenium==4.27.1
- speechrecognition==3.14.0
- pandas==2.1.1
- python-dotenv==1.0.0
- numpy==1.26.0
- unidecode==1.3.8
- urllib3==2.1.0
- tqdm==4.66.1

## How to Run the Project

1. **Clone the repository**:
    ```bash
    git clone https://github.com/lucassoares-eng/company-credit-assessment
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    - Create a `.env` file in the root directory of the project.
    - Add the following variables to the `.env` file:
      ```plaintext
      PESQUISAPROTESTO_USER=your_username
      PESQUISAPROTESTO_PASSWORD=your_password
      PORTAL_TRANSPARENCIA_API_KEY=your_api_key
      ```
    - **PESQUISAPROTESTO_USER** and **PESQUISAPROTESTO_PASSWORD**: 
      - Visit [Pesquisa Protesto](https://www.pesquisaprotesto.com.br/cadastro) to create an account and obtain your credentials.
    - **PORTAL_TRANSPARENCIA_API_KEY**:
      - Visit [Portal da Transparência](https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email) to register your email and generate an API key.

5. **Run the Flask server**:
    ```bash
    python app.py
    ```

6. **Access the API**:
    Open your browser and visit `http://localhost:5000` to interact with the API.

7. **First-time Instagram login**:
    - On the first run, the system will prompt you to log in to Instagram to allow the API to fetch the number of followers for the companies being analyzed.
    - After the first login, the system will save the login cookies locally, so you won't need to log in again on subsequent runs.

---

### Notes:
- Ensure that the `.env` file is correctly configured with the required credentials.
- The Instagram login is necessary only once, as the cookies are stored locally for future use.

## **Contributions**

Contributions are welcome! Feel free to open issues and submit pull requests to improve the project.

---

## **License**

This project is licensed under the APACHE License. See the `LICENSE` file for more details.

---

## **Contact**

If you have questions or suggestions, feel free to reach out:

Email: lucasjs.eng@gmail.com

LinkedIn: [https://www.linkedin.com/in/lucas-soares-33486b42/](https://www.linkedin.com/in/lucas-soares-33486b42/)
