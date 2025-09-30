import os
import json
import requests
import streamlit as st

# ===== 基本設定 =====
st.set_page_config(page_title="試験対策アプリ", page_icon="📝", layout="centered")

# ※ Streamlit の監視上限エラー対策（必要なら .streamlit/config.toml で設定推奨）
os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

# ===== APIキー =====
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Secrets に GEMINI_API_KEY（または GOOGLE_API_KEY）がありません。")
    st.stop()

# 候補モデル（上から優先）
PREFERRED = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
]

# ===== ユーティリティ =====
def list_models(api_version: str) -> list[str]:
    """利用可能モデルを列挙し generateContent 可能なIDだけ返す"""
    url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={API_KEY}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    j = r.json()
    models = []
    for m in j.get("models", []):
        name = (m.get("name") or "").split("/")[-1]  # e.g. models/gemini-1.5-flash-latest
        methods = (
            m.get("supportedGenerationMethods")
            or m.get("supported_generation_methods")
            or []
        )
        if "generateContent" in methods:
            models.append(name)
    return models

@st.cache_data(show_spinner=False, ttl=3600)
def autodetect_model() -> tuple[str, str, list[str]]:
    """
    v1 → v1beta の順で /models を叩いて、使えるモデルから最適を選ぶ。
    return: (api_version, model_name, all_names)
    """
    last_err = None
    for ver in ["v1", "v1beta"]:
        try:
            names = list_models(ver)
            if not names:
                continue
            # 候補の優先順で選択
            for cand in PREFERRED:
                if cand in names:
                    return ver, cand, names
            # 候補に無ければ最初の1件
            return ver, names[0], names
        except Exception as e:
            last_err = e
            continue
    # ここに来る＝どちらのバージョンでも一覧取得不可
    raise RuntimeError(f"モデル一覧の取得に失敗しました: {last_err}")

def call_gemini(prompt: str, api_version: str, model: str, timeout: int = 30) -> str:
    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0}
    }
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]

def parse_json_loose(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        # ```json ... ``` 対応
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1]
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError("JSONブロックを抽出できませんでした。")
    return json.loads(t[s:e+1])

# ===== データ読込 =====
try:
    with open("constants.json", "r", encoding="utf-8") as f:
        QUESTIONS = json.load(f)
except FileNotFoundError:
    st.error("❌ constants.json が見つかりません。")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ constants.json のパースに失敗: {e}")
    st.stop()

# ===== UI =====
st.title("📝試験対策アプリ")
st.markdown("出題を選んで受験者の解答を入力すると、AI が **10点満点** で採点します。")

# モデル自動検出（初回だけ）
try:
    if "API_VER" not in st.session_state:
        api_ver, model_name, all_names = autodetect_model()
        st.session_state.API_VER = api_ver
        st.session_state.MODEL = model_name
        st.session_state.ALL_MODELS = all_names
except Exception as e:
    st.error(f"❌ モデル自動検出に失敗: {e}")
    st.stop()

with st.expander("🔧 使用中のエンドポイント/モデル"):
    st.write(f"- API バージョン: `{st.session_state.API_VER}`")
    st.write(f"- モデル: `{st.session_state.MODEL}`")
    st.write("— 利用可能モデル一覧:")
    st.code("\n".join(st.session_state.ALL_MODELS))

options = {q["id"]: f"{q['id']}: {q.get('subject','No Subject')}" for q in QUESTIONS}
selected_id = st.selectbox("出題を選んでください", options.keys(), format_func=lambda x: options[x])

q = next(q for q in QUESTIONS if q["id"] == selected_id)
problem = q.get("text", "")
reference_default = q.get("modelAnswer", "")

st.subheader("🧩 問題文")
st.write(problem)

with st.expander("📘 模範解答", expanded=False):
    reference = st.text_area("模範解答", value=reference_default, height=140)

student = st.text_area("🧑‍🎓 あなたの解答", height=200, placeholder="ここに回答を入力…")
strictness = st.slider("採点の厳しさ（1=寛容, 5=非常に厳格）", 1, 5, 3)
do_eval = st.button("採点する")

def build_prompt(problem, student, reference, strictness):
    return f"""
あなたは日本語の厳格な採点者です。与えられた問題文と受験者の解答を評価し、JSONで出力してください。
出力スキーマ（余計なテキストは禁止）:
{{"score": <0-10>,"rubric":"...","strengths":["..."],"weaknesses":["..."],"improvements":["..."],"reasoning":"..."}}
採点の厳しさ: {strictness}
問題文:
{problem}
受験者の解答:
{student}
模範解答（任意、空なら参考にしない）:
{reference}
"""

if do_eval:
    if not problem or not student:
        st.warning("⚠️ 問題文と受験者の解答は必須です。")
        st.stop()

    prompt = build_prompt(problem, student, reference, strictness)
    try:
        with st.spinner("Gemini が採点中…"):
            text = call_gemini(prompt, st.session_state.API_VER, st.session_state.MODEL, timeout=30)
    except Exception as e:
        st.error(f"❌ API呼び出し失敗: {e}")
        st.stop()
