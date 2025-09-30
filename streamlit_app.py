import os
import json
import requests
import streamlit as st

# ================= 基本設定 =================
st.set_page_config(page_title="試験対策アプリ", page_icon="📝", layout="centered")

# （ストレージ監視で固まる環境向けの保険）
os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Secrets に GEMINI_API_KEY（または GOOGLE_API_KEY）がありません。")
    st.stop()

# 優先順に試すモデル（手持ちのキーで404が出た場合に備えて幅広く）
PREFERRED = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
]

# ================ ユーティリティ ================
def list_models(api_ver: str, timeout=15) -> list[str]:
    """指定APIバージョンで generateContent 可能なモデル名を列挙"""
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={API_KEY}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    names = []
    for m in j.get("mo
