import os
import json
import streamlit as st

# Gemini
import google.generativeai as genai

# ====== 設定 ======
# Streamlit Cloud では [App settings] → [Secrets] に "GEMINI_API_KEY" を保存してください
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY が設定されていません。StreamlitのSecretsに追加してください。")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # 速くて安価。厳密評価をしたい場合は gemini-1.5-pro へ

# ====== UI ======
st.set_page_config(page_title="Exam Prep AI Grader (Gemini)", page_icon="📝", layout="centered")
st.title("📝 Exam Prep AI Grader (Gemini) - Streamlit")

st.markdown("**問題文**・**受験者の解答**・（任意）**模範解答**を入力して、Geminiに採点させます。")

col1, col2 = st.columns(2)
with col1:
    score_max = st.selectbox("満点スコア", [10, 20, 100], index=0)
with col2:
    strictness = st.slider("採点の厳しさ（高いほど厳しい）", 1, 5, 3)

problem = st.text_area("🧩 問題文", height=140, placeholder="例）日本の江戸時代の鎖国政策の目的と影響を述べよ。")
student = st.text_area("🧑‍🎓 受験者の解答", height=180, placeholder="ここに回答を貼り付け…")
reference = st.text_area("📘 模範解答（任意）", height=160, placeholder="任意。空でもOK。")

do_eval = st.button("採点する")

def build_prompt(problem, student, reference, score_max, strictness):
    return f"
