# ===================================================
# Import das bibliotecas utilizadas
# ===================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os, time, io
import pandas as pd
import boto3
from botocore.config import Config

# ===================================================
# Configurações via variáveis de ambiente
# ===================================================

S3_BUCKET = os.getenv("S3_BUCKET", "mlet-3-tech-challenge")
S3_KEY_LATEST = os.getenv("S3_KEY_LATEST", "latest/carteira_ibov.parquet")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")

# ===================================================
# Metadados da API (aparecem no Swagger /docs)
# ===================================================

app = FastAPI(
    title="IBOV Data API",
    version="1.0.0",
    description=(
        "API que lê o arquivo **latest** (Parquet) no Amazon S3 contendo a carteira do IBOV "
        "e expõe endpoints para uso pelo app Análise de Ações Ibovespa - Streamlit.<br><br>"
        "**Endpoints:**<br>"
        "- `GET /status` — Healthcheck e diagnóstico de configuração.<br>"
        "- `GET /lista_acoes` — Lista de ações (colunas `Código`, `Acao_Tipo`)."
    ),
    contact={"name": "Joyce Muniz - joyce.muniz@hotmail.com"},
    license_info={"name": "MIT"}
)

# ===================================================
# CORS
# ===================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================================
# Cliente S3 e Cache
# ===================================================

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4")
)
_cache = {"ts": 0.0, "dados_cache": None}

def carregar_latest_do_s3() -> pd.DataFrame:
    obj = _s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY_LATEST)
    buf = io.BytesIO(obj["Body"].read())
    df = pd.read_parquet(buf, engine="pyarrow")
    return df

# ===================================================
# Endpoints
# ===================================================

@app.get("/status")
def status_api():
    return {"status": "ok", "bucket": S3_BUCKET, "key": S3_KEY_LATEST}

@app.get("/lista_acoes")
def listar_acoes_ibov():
    now = time.time()
    if _cache["dados_cache"] is None or now - _cache["ts"] > CACHE_TTL_SECONDS:
        try:
            df = carregar_latest_do_s3()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Falha ao ler do S3: {e}")

        cols = [c for c in ["Código", "Acao_Tipo"] if c in df.columns]
        if not cols:
            raise HTTPException(status_code=500, detail="Colunas esperadas não encontradas no parquet.")
        dados_cache = df[cols].to_dict(orient="records")

        _cache["dados_cache"] = dados_cache
        _cache["ts"] = now

    return JSONResponse(content=_cache["dados_cache"])
