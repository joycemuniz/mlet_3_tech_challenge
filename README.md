# 📊 Análise de Ações Ibovespa

## 🚀 Objetivo

Este projeto foi desenvolvido como parte do **3° Tech Challenge - Pós Tech FIAP (Machine Learning Engineering)**. Ele tem como objetivo criar um produto de dados capaz de realizar a **coleta das ações que compõem a carteira do Ibovespa** por meio de um scraper, armazenar os dados em formato **Parquet** em um **bucket S3**, disponibilizar a lista de ações através de uma **API construída em FastAPI** e, posteriormente, consumi-la em um **aplicativo Streamlit**. O aplicativo consulta informações históricas de preços pela **API do Yahoo Finance** e aplica técnicas de análise e previsão utilizando a biblioteca **Prophet (Meta/Facebook)**.

---

## 🧩 Arquitetura da Solução

1. **Scraper (Selenium + BeautifulSoup)**  
   - Extrai a carteira de ações do site da **B3**.  
   - Salva os dados em **Parquet**.  
   - Envia os arquivos para o **Amazon S3**:
     - `latest/carteira_ibov.parquet` → versão mais recente.  
     - `historico/carteira_ibov_YYYYMMDD.parquet` → versões históricas.

2. **API (FastAPI + Uvicorn)**  
   - Lê os dados diretamente do S3.  
   - Disponibiliza endpoints para consumo.  
   - Documentada automaticamente no Swagger (`/docs`).

   **Endpoints**:
   - `GET /status` → Healthcheck da API  
   - `GET /lista_acoes` → Lista de ações disponíveis (colunas `Código` e `Acao_Tipo`)

3. **App (Streamlit)**  
   - Consome os dados da **API FastAPI** para listar as ações disponíveis.  
   - Permite ao usuário selecionar uma ação. 
   - Integra-se com a **API do Yahoo Finance** para coletar dados históricos de preços da ação escolhida.
   - Exibição dos valores recentes e **Gráfico Candlestick** para análise visual da evolução do preço.

3. **Modelo de Previsão (Prophet)**  
   - Utilização dos dados históricos de preços coletados no Yahoo Finance.
   - Aplicação do modelo **Prophet (Meta/Facebook)**, uma técnica de séries temporais que considera tendências, sazonalidade e eventos.
   - Gera previsões de preços futuros com intervalo de confiança.

---

## ⚙️ Tecnologias Utilizadas

- **Python 3.10+**
- **Selenium / BeautifulSoup** → Web scraping  
- **Pandas / PyArrow** → Manipulação e salvamento em Parquet  
- **Boto3** → Integração com AWS S3  
- **FastAPI + Uvicorn** → API  
- **Streamlit** → Aplicativo interativo  
- **Prophet** → Modelagem e previsão de séries temporais  
- **Plotly** → Visualizações interativas  

---

## 📂 Estrutura do Projeto

```bash
├── scrapper/
│   └── scrapper_ibov.py   # Extração e upload para S3
├── api/
│   └── main.py            # API FastAPI
├── app.py                 # Aplicativo em Streamlit
├── requirements.txt       # Dependências do projeto
└── README.md              # Documentação
```

---

## ▶️ Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/seuusuario/ibov-analytics.git
cd ibov-analytics
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Rodar o Scraper
```bash
python scrapper/scrapper_ibov.py
```

### 5. Rodar a API
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
- Documentação Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Rodar o App Streamlit
```bash
streamlit run app.py
```
- Acesse: [http://localhost:8501](http://localhost:8501)

---

## 🌐 Deploy

- **API**: [Render](https://mlet-3-tech-challenge.onrender.com/lista_acoes) 
- **App Streamlit**: [Streamlit Cloud](https://app-ibovespa.streamlit.app)

---

## 🎥 Demonstração em Vídeo

📽️ Link: [Youtube]()

## 📌 Próximos Passos / Melhorias

- Salvar previsões no S3 para registros de históricos
- Desenvolvimento de estrutura que permita escolher/selecionar o modelo de previsão

## 👥 Equipe
| Integrante                   | RM      | Contato                               |
|-----------------------------|---------|----------------------------------------|
| **Joyce Muniz de Oliveira** | 364278  | [joyce.muniz@hotmail.com](mailto:joyce.muniz@hotmail.com) |
