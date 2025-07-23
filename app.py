# === Streamlit App Principal para Artista ===
# Spotify OAuth + Dashboard + Tendencias + Predicción

import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import urllib.parse as urlparse
from sklearn.linear_model import LinearRegression
from datetime import datetime
import os

# ================== CONFIGURACIÓN ==================
CLIENT_ID = st.secrets.get("SPOTIFY_CLIENT_ID", "TU_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIFY_CLIENT_SECRET", "TU_CLIENT_SECRET")
REDIRECT_URI = "https://artist-app-638wq178jx9.streamlit.app/callback"
SCOPE = "user-read-private user-read-email user-top-read user-read-recently-played"

# ================== FUNCIONES OAUTH ==================
def get_auth_url():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
    }
    return f"https://accounts.spotify.com/authorize?{urlparse.urlencode(params)}"

def get_token_from_code(code):
    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    return response.json()

# ================== FUNCIONES DE DATOS ==================
def get_top_tracks(token):
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get('https://api.spotify.com/v1/me/top/tracks?limit=10', headers=headers)
    if r.status_code != 200:
        st.error("No se pudieron obtener canciones. Verifica permisos.")
        return pd.DataFrame()

    tracks = r.json()['items']
    return pd.DataFrame([{
        'Nombre': t['name'],
        'Popularidad': t['popularity'],
        'Artista': t['artists'][0]['name'],
        'Álbum': t['album']['name'],
        'Duración (min)': round(t['duration_ms'] / 60000, 2)
    } for t in tracks])

def predict_popularity(df):
    df['Fecha'] = datetime.today()
    df['days_since_start'] = 0
    predictions = []
    fig, ax = plt.subplots(figsize=(10, 5))

    for song in df['Nombre'].unique():
        pop = df[df['Nombre'] == song]['Popularidad'].values
        x = np.arange(len(pop)).reshape(-1, 1) if len(pop) > 1 else np.array([[0], [1]])
        y = pop if len(pop) > 1 else np.array([pop[0], pop[0]])
        model = LinearRegression().fit(x, y)
        future_x = np.arange(len(pop), len(pop) + 30).reshape(-1, 1)
        preds = model.predict(future_x)
        ax.plot(np.arange(len(pop)), pop, label=f"{song} (actual)")
        ax.plot(np.arange(len(pop), len(pop)+30), preds, linestyle='--', label=f"{song} (predicción)")
    ax.set_title("Predicción de Popularidad - Top Canciones")
    ax.set_xlabel("Días")
    ax.set_ylabel("Popularidad")
    ax.legend()
    st.pyplot(fig)

# ================== APP ==================
st.set_page_config(page_title="Artista Insights", layout="wide")
st.title("🎧 Artist Insights Dashboard")

query_params = st.experimental_get_query_params()
code = query_params.get("code", [None])[0]

if not code:
    auth_url = get_auth_url()
    st.markdown(f"[Iniciar sesión con Spotify]({auth_url})")
else:
    token_data = get_token_from_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        st.error("❌ No se pudo obtener token. Intenta de nuevo.")
    else:
        st.success("✅ Autenticación exitosa")
        st.subheader("Tus canciones más escuchadas")
        df_top = get_top_tracks(access_token)
        st.dataframe(df_top)

        if not df_top.empty:
            st.subheader("🔮 Predicción de popularidad")
            predict_popularity(df_top)
