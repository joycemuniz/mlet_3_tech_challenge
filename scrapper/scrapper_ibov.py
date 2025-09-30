# ===================================================
# Import das bibliotecas utilizadas
# ===================================================
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import boto3, io, os, time, re

# ===================================================
# Configurações do Selenium e Scrapper do site 
# ===================================================
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
url = "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBOV?language=pt-br"
driver.get(url)

wait = WebDriverWait(driver, 10)

# Selecionando "120" resultados por página
select_element = wait.until(EC.presence_of_element_located((By.ID, "selectPage")))
Select(select_element).select_by_visible_text("120")
time.sleep(3)
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Pegando a data das informações do site
titulo = soup.find("h2")
data_str = titulo.get_text(strip=True).split("-")[-1].strip()  # "03/07/25"
data_html = datetime.strptime(data_str, "%d/%m/%y").strftime("%Y%m%d")

# Extraindo a tabela tabela
tabela = soup.find("table", class_="table table-responsive-sm table-responsive-md")

cabecalhos = [th.get_text(strip=True) for th in tabela.find("thead").find_all("th")]
dados = []
for linha in tabela.find("tbody").find_all("tr"):
    colunas = [td.get_text(strip=True) for td in linha.find_all("td")]
    dados.append(colunas)

df = pd.DataFrame(dados, columns=cabecalhos)

# ===================================================
# Criando nova coluna e salvando arquivos em parquet
# ===================================================

def _tipo3(s: str) -> str:
    s = str(s).upper()
    tokens = re.findall(r"[A-Z]+", s)
    if not tokens:
        return ""
    
    prefer = ("ON", "PN", "PNA", "PNB", "PNE", "PNS", "UNT", "UNIT")
    for t in tokens:
        if t in prefer:
            return t[:3]
    return tokens[0][:3]

df["Tipo3"] = df["Tipo"].apply(_tipo3)
df["Acao_Tipo"] = df["Ação"].astype(str).str.strip() + " - " + df["Tipo3"]

os.makedirs("output", exist_ok=True)
caminho_parquet_historico = f"output/carteira_ibov_{data_html}.parquet"
caminho_parquet = f"output/carteira_ibov.parquet"
df.to_parquet(caminho_parquet, index=False, engine="pyarrow")
df.to_parquet(caminho_parquet_historico, index=False, engine="pyarrow")

print(f"Dados extraídos da data: {data_html}")
print(f"Arquivo salvo em: {caminho_parquet}")

# =========================
# AWS - S3
# =========================

BUCKET = "mlet-3-tech-challenge"

s3 = boto3.client("s3")

try:
    # Envio da versão "latest"
    s3.upload_file(
        Filename=caminho_parquet,
        Bucket=BUCKET,
        Key="latest/carteira_ibov.parquet"
    )

    # Envio da versão histórica
    s3.upload_file(
        Filename=caminho_parquet_historico,
        Bucket=BUCKET,
        Key=f"historico/carteira_ibov_{data_html}.parquet"
    )

    print(f"Upload efetuado para o s3://{BUCKET}/latest/carteira_ibov.parquet")
    print(f"Upload efetuado para o s3://{BUCKET}/historico/carteira_ibov_{data_html}.parquet")

except Exception as e:
    print("Erro ao enviar para o S3:", e)

driver.quit()