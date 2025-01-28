import os
import random
import pandas as pd
from tqdm import tqdm
from app.service import fetch_company_data

def main():
    # File path and sheet name
    file_path = 'app/data/base_cnpj.csv'
    results_file = 'app/data/resultados_cnpjs.xlsx'

    # Read the CSV file
    df = pd.read_csv(file_path, sep=';', encoding='latin1', dtype=str)

    # Convert the 'CNPJ' column to a list
    cnpj_list = df['CNPJ'].tolist()

    # Load existing results to continue from where it stopped
    if os.path.exists(results_file):
        results_df = pd.read_excel(results_file, dtype={'cnpj': str})
        processed = set(results_df['cnpj'].astype(str))
    else:
        results_df = pd.DataFrame()
        processed = set()

    # Filter unprocessed CNPJs
    remaining_cnpjs = [cnpj for cnpj in cnpj_list if str(cnpj) not in processed]

    # Shuffle the remaining CNPJs
    random.shuffle(remaining_cnpjs)

    # Process CNPJs
    for cnpj in tqdm(remaining_cnpjs, desc="Processing CNPJs"):
        try:
            # Fetch company data
            result = fetch_company_data(cnpj)
            
            # Convert the result to a DataFrame if valid
            if result:
                new_df = pd.DataFrame([result])
                results_df = pd.concat([results_df, new_df], ignore_index=True)
            
            # Ensure 'cnpj' column is a string
            results_df['cnpj'] = results_df['cnpj'].astype(str)
            
            # Save updated results
            results_df.to_excel(results_file, index=False)
        except Exception as e:
            print(f"Error processing CNPJ {cnpj}: {e}")

    print("Processing completed.")

if __name__ == "__main__":
    main()