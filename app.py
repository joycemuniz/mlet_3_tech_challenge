# ===================================================
# Import das bibliotecas utilizadas
# ===================================================

import streamlit as st
import yfinance as yf
from datetime import date
import pandas as pd
from prophet import Prophet
from plotly import graph_objs as go

# =========================
# Configurações iniciais
# =========================
data_inicio = '2000-01-01'
data_fim = date.today().strftime('%Y-%m-%d')

st.markdown(
    "<h1 style='text-align: center;'>Análise de Ações Ibovespa</h1>",
    unsafe_allow_html=True
)

st.sidebar.header('Escolha uma ação')

# Horizonte da previsão
n_dias = st.sidebar.slider('Selecione quantidade de dias para a previsão', 7, 60)

# =========================
# Carregando lista de ações
# =========================
import requests

url_api = "https://mlet-3-tech-challenge.onrender.com"

@st.cache_data(ttl=600)
def pegar_dados_acoes():
    resp = requests.get(f"{url_api}/lista_acoes")
    if resp.status_code != 200:
        st.error("Erro ao carregar lista de ações da API")
        return pd.DataFrame()
    data = resp.json()
    return pd.DataFrame(data)

df = pegar_dados_acoes()

# ===================================================
# Seleção da lista de ações e informações adicionais
# ===================================================

opcoes = df['Acao_Tipo'].tolist()
nome_acao_escolhida = st.sidebar.selectbox('Escolha uma ação:', opcoes)

df_acao = df[df['Acao_Tipo'] == nome_acao_escolhida]

st.sidebar.markdown("---")
with st.sidebar.expander("📑 Legenda de Códigos"):
    st.markdown("""
    **Tipos de Ações**
    - **ON** → Ações Ordinárias (direito a voto em assembleias)
    - **PN** → Ações Preferenciais (prioridade em dividendos, geralmente sem voto)
    - **PNA, PNB, PNC...** → Classes de preferenciais (A, B, C…)
    - **UNT / UNIT** → Units (pacote de ações ON + PN negociadas em conjunto)
    """)

ticker_base = str(df_acao.iloc[0]['Código']).strip()
ticker_yf = f'{ticker_base}.SA'

# =========================
# Coleta de preços yfinance
# =========================


@st.cache_data(ttl=3600)
def pegar_valores_online(sigla_acao: str) -> pd.DataFrame:
    dfv = yf.download(
        sigla_acao,
        start=data_inicio,
        end=data_fim,
        progress=False,
        auto_adjust=True
    )
    if dfv is None or dfv.empty:
        return pd.DataFrame()

    # Tratamento se houver MultiIndex nas colunas
    if isinstance(dfv.columns, pd.MultiIndex):
        if len(dfv.columns.get_level_values(1).unique()) == 1:
            dfv.columns = dfv.columns.get_level_values(0)
        else:
            dfv.columns = ['_'.join(map(str, c)).strip('_') for c in dfv.columns.to_list()]

    dfv = dfv.reset_index().rename(columns={'Datetime': 'Date', 'index': 'Date'})
    dfv['Date'] = pd.to_datetime(dfv['Date'], errors='coerce')

    # Garantindo que os valores sejam numéricos
    for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
        if col in dfv.columns:
            dfv[col] = pd.to_numeric(dfv[col], errors='coerce')

    # Forçando a ordenação por data e limpando os valores nulos
    dfv = dfv.sort_values('Date').dropna(subset=['Date', 'Open', 'Close'])
    return dfv

df_valores = pegar_valores_online(ticker_yf)
if df_valores.empty:
    st.warning(f'Nenhum dado retornado para o ticker: {ticker_yf}.')
    st.stop()

# =========================
# Tabela da ação escolhida
# =========================
st.markdown(
    "<div style='border-top: 2px solid #7047fb; margin: 20px 0;'></div>",
    unsafe_allow_html=True
)
st.markdown(
    f"## Informações históricas da ação escolhida - "
    f"<span style='color:#7047fb'>{nome_acao_escolhida} ({ticker_base})</span>",
    unsafe_allow_html=True
)

st.markdown(
    "<div style='border-top: 2px solid #7047fb; margin: 20px 0;'></div>",
    unsafe_allow_html=True
)

st.subheader(f'Tabela dos últimos valores da ação')
st.write(df_valores.tail(10))

# =========================
# Gráfico Candlestick
# =========================
st.subheader('Gráfico histórico de preços da ação (Candlestick)')
fig2 = go.Figure(data=[
   go.Candlestick(
    x=df_valores['Date'],
    open=df_valores['Open'],
    high=df_valores['High'],
    low=df_valores['Low'],
    close=df_valores['Close'],
    increasing=dict(
        line=dict(color="#59ac81"),
        fillcolor='rgba(177,222,199,0.6)'
    ),
    decreasing=dict(
        line=dict(color="#fc7373"),
        fillcolor='rgba(255,107,107,0.6)'
    )
)
])

fig2.update_layout(
    xaxis_title='Data', yaxis_title='Preço',
    xaxis_rangeslider_visible=False, template='plotly_white'
)
st.plotly_chart(fig2, use_container_width=True)

# =======================================================
# Previsão (Prophet) — exibir yhat + IC apenas no FUTURO
# =======================================================

st.markdown(
    "<div style='border-top: 2px solid #7047fb; margin: 20px 0;'></div>",
    unsafe_allow_html=True
)

st.markdown(
    f"## Previsões da ação escolhida - "
    f"<span style='color:#7047fb'>{nome_acao_escolhida}</span>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='border-top: 2px solid #7047fb; margin: 20px 0;'></div>",
    unsafe_allow_html=True
)

# Preparando dados no formato que a biblioteca Prophet utiliza: ds, y
df_treino = (
    df_valores[['Date', 'Close']]
    .rename(columns={'Date': 'ds', 'Close': 'y'})
    .copy()
)
df_treino['ds'] = pd.to_datetime(df_treino['ds'], errors='coerce')
df_treino['y'] = pd.to_numeric(df_treino['y'], errors='coerce')
df_treino = df_treino.dropna(subset=['ds', 'y']).sort_values('ds')

# Treinando o modelo
modelo = Prophet(interval_width=0.98, daily_seasonality=False)
modelo.fit(df_treino)

# Criando horizonte futuro (dias úteis = 'B')
futuro = modelo.make_future_dataframe(periods=n_dias, freq='B')
forecast = modelo.predict(futuro)

last_obs = df_treino['ds'].max()
prev_fut = forecast.loc[forecast['ds'] > last_obs].copy()
prev_table = prev_fut.rename(columns={
    'ds': 'Data Previsão',
    'yhat': 'Valor Previsão',
    'yhat_lower': 'Limite Inferior',
    'yhat_upper': 'Limite Superior'
})

# =============================
# Tabela com dados de previsão
# =============================

st.subheader(f'Tabela de valores previstos para os próximos {n_dias} dias')
if not prev_table.empty:
    st.write(prev_table[['Data Previsão', 'Valor Previsão', 'Limite Inferior', 'Limite Superior']].tail(n_dias))

# =============================
# Gráfico com dados de previsão
# =============================

st.subheader(f'Gráfico com previsão de preços para os próximos {n_dias} dias')
fig_forecast = go.Figure()

fig_forecast.add_trace(go.Scatter(
    x=df_treino['ds'], y=df_treino['y'],
    name='Observado', mode='lines',
    line=dict(color="#653be3", width=2)
))

if not prev_fut.empty:
    fig_forecast.add_trace(go.Scatter(
        x=prev_fut['ds'], y=prev_fut['yhat_upper'],
        line=dict(width=0), showlegend=False, hoverinfo='skip'
    ))
    fig_forecast.add_trace(go.Scatter(
        x=prev_fut['ds'], y=prev_fut['yhat_lower'],
        fill='tonexty', fillcolor='rgba(31,119,180,0.2)',
        line=dict(width=0), name='Intervalo 95%', hoverinfo='skip'
    ))
    fig_forecast.add_trace(go.Scatter(
        x=prev_fut['ds'], y=prev_fut['yhat'],
        name='Previsão (futuro)', mode='lines+markers',
        line=dict(color="#22d4f4", width=2)
    ))
    fig_forecast.add_vline(x=last_obs, line_width=1, line_dash='dash', line_color='gray')

fig_forecast.update_layout(
    xaxis_title='Data', yaxis_title='Preço',
    template='plotly_white', legend=dict(orientation='h', y=-0.2)
)
st.plotly_chart(fig_forecast, use_container_width=True)

st.markdown(
    """
    <hr>
    <div style='text-align: center; font-size: 14px;'>
        Desenvolvido por <b>Joyce Muniz</b><br>
        <a href='https://www.linkedin.com/in/joycemoliveira' target='_blank' style='text-decoration:none; color:gray;'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='18' style='vertical-align:middle; filter: grayscale(100%); margin-right:6px;'>
            joycemoliveira
        </a>
    </div>
    """,
    unsafe_allow_html=True
)