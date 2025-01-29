# Credit Analysis API

This API provides several functionalities to obtain data about companies, including CNPJ information, social media profiles, protests, and government contracts. The API is built with Flask and provides endpoints to access this data.

## API Endpoints

### 1. **`/cnpj`** - Displays CNPJ information
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

## Example of using the API

To make a request to check information for a company with CNPJ `12345678000195`, you can do the following:

```bash
GET /cnpj?cnpj=12345678000195
```

## Requirements

- Python 3.x
- Flask
- Additional dependencies (like requests, selenium, etc.) that you can install with:

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

4. **Run the Flask server**:
    ```bash
    python app.py
    ```

5. **Access the API**:
    Open your browser and visit `http://localhost:5000` to interact with the API.

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
