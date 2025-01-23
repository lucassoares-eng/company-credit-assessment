import os
import random
import pandas as pd
from tqdm import tqdm
from app.utils import consulta_cnpj

if __name__ == "__main__":
    # Caminho do arquivo e nome da aba
    file = 'app/data/base_cnpj.csv'

    # Ler o arquivo Excel e a aba específica
    df = pd.read_csv(file, sep=';', encoding='latin1', dtype=str)

    # Transformar a coluna 'CNPJ' em uma lista
    lista_cnpjs = df['CNPJ'].tolist()

    # Caminho dos arquivos
    arquivo_resultados = 'app/data/resultados_cnpjs.xlsx'

    # Carregar resultados existentes para continuar de onde parou
    if os.path.exists(arquivo_resultados):
        df_resultados = pd.read_excel(arquivo_resultados, dtype={'cnpj': str})
        processados = set(df_resultados['cnpj'].astype(str))
    else:
        df_resultados = pd.DataFrame()
        processados = set()

    # Criar lista de CNPJs a serem processados
    cnpjs_restantes = [cnpj for cnpj in lista_cnpjs if str(cnpj) not in processados]

    # Embaralhar a lista de CNPJs restantes
    random.shuffle(cnpjs_restantes)

    # Processar CNPJs
    for cnpj in tqdm(cnpjs_restantes, desc="Processando CNPJs"):
        try:
            resultado = consulta_cnpj(cnpj)  # Função de consulta
            
            # Criar DataFrame com o novo resultado
            df_novo = pd.DataFrame([resultado])
            
            # Concatenar apenas se houver dados válidos
            if not df_novo.empty:
                df_resultados = pd.concat([df_resultados, df_novo], ignore_index=True)
            
            # Garantir que o CNPJ no DataFrame seja texto
            df_resultados['cnpj'] = df_resultados['cnpj'].astype(str)
            
            # Salvar resultados atualizados
            df_resultados.to_excel(arquivo_resultados, index=False)
        except Exception as e:
            print(f"Erro na consulta do CNPJ {cnpj}: {e}")

    print("Processamento concluído.")