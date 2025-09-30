import os
import json
import requests
import streamlit as st

# ================= 基本設定 =================
st.set_page_config(page_title="第3節 下水道の種類｜短答100字演習", page_icon="📝", layout="centered")
os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Secrets に GEMINI_API_KEY（または GOOGLE_API_KEY）がありません。")
    st.stop()

# 優先順位（上ほど優先）
PREFERRED = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
]

# ================ 共通ユーティリティ ================
def _list_models(api_ver: str, timeout=15) -> list[str]:
    """指定 API バージョンのモデル一覧（generateContent 可能なもの）"""
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={API_KEY}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    names = []
    j = r.json()
    for m in j.get("models", []):
        name = (m.get("name") or "").split("/")[-1]  # models/xxx → xxx
        methods = m.get("supportedGenerationMethods") or m.get("supported_generation_methods") or []
        if "generateContent" in methods:
            names.append(name)
    return names

@st.cache_resource(show_spinner=False)
def autodetect_model() -> tuple[str, str] | None:
    """
    v1 → v1beta の順で /models を叩いて、使えるモデルを1つ選ぶ。
    return: (api_ver, model) 例 ("v1", "gemini-1.5-pro-latest")
    どちらも空なら None
    """
    last_err = None
    for ver in ["v1", "v1beta"]:
        try:
            names = _list_models(ver)
            if not names:
                continue
            # 優先リストから選ぶ
            for cand in PREFERRED:
                if cand in names:
                    return ver, cand
            # 無ければ最初の1件
            return ver, names[0]
        except Exception as e:
            last_err = e
            continue
    return None

def call_gemini(prompt: str, api_ver: str, model: str, timeout=30) -> str:
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{api_ver}/{model}: HTTP {r.status_code}: {r.text[:400]}")
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]

def parse_json_loose(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1]
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError("JSONブロックが見つかりません。")
    return json.loads(t[s:e+1])

# ================ データ読込 ================
try:
    with open("constants.json", "r", encoding="utf-8") as f:
        QUESTIONS = json.load(f)
except FileNotFoundError:
    st.error("❌ constants.json が見つかりません。")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ constants.json のパースに失敗: {e}")
    st.stop()

# ================ モデル自動検出（UIなし・起動時に一度だけ） ================
detected = autodetect_model()
if not detected:
    st.error("❌ 利用可能な Gemini モデルが見つかりませんでした。")
    st.markdown(
        "- まずブラウザで下記URLを開き、200でモデル一覧が返るか確認してください。  \n"
        f"`https://generativelanguage.googleapis.com/v1/models?key=＜あなたのAPIキー＞`  \n"
        "- 403/404 の場合：AI Studio で **生成言語 API キー** を新規発行し、Secrets を差し替えてください。  \n"
        "- 組織制限がある場合は Vertex AI をご利用ください（必要なら Vertex 版コードをお渡しします）。"
    )
    st.stop()

API_VER, MODEL_NAME = detected  # 例 ("v1", "gemini-1.5-pro-latest")

# ================ メインUI ================
st.title("第3節 下水道の種類｜短答100字演習")
st.caption(f"出典：§1.3.1 下水道の種類（第3節 下水道の種類）｜使用中: {API_VER} / {MODEL_NAME}")
st.markdown("出題を選んで受験者の解答を入力すると、AI が **10点満点** で採点します。")

# ===== 出題ナビ（戻る／次へ 付き） =====
ID_TO_Q = {q["id"]: q for q in QUESTIONS}
ORDERED_IDS = sorted(ID_TO_Q.keys())

# 現在位置（インデックス）だけを状態管理
if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0

# selectbox 変更 → q_idx 同期（Session Stateへの直接代入はしない）
def on_select_change():
    sel = st.session_state.get("selected_id", ORDERED_IDS[st.session_state.q_idx])
    st.session_state.q_idx = ORDERED_IDS.index(sel)

def go_prev():
    if st.session_state.q_idx > 0:
        st.session_state.q_idx -= 1

def go_next():
    if st.session_state.q_idx < len(ORDERED_IDS) - 1:
        st.session_state.q_idx += 1

selected_id = st.selectbox(
    "出題を選んでください",
    options=ORDERED_IDS,
    index=st.session_state.q_idx,                   # ← これが真のソース
    format_func=lambda i: f"{i}: {ID_TO_Q[i].get('subject','No Subject')}",
    key="selected_id",
    on_change=on_select_change,                     # ← 変更時に q_idx を同期
)

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    st.button("← 戻る", use_container_width=True, on_click=go_prev,
              disabled=(st.session_state.q_idx == 0))
with c2:
    st.markdown(
        f"<div style='text-align:center; font-weight:600;'>"
        f"{st.session_state.q_idx + 1} / {len(ORDERED_IDS)}</div>",
        unsafe_allow_html=True
    )
with c3:
    st.button("次へ →", use_container_width=True, on_click=go_next,
              disabled=(st.session_state.q_idx == len(ORDERED_IDS) - 1))

current_id = ORDERED_IDS[st.session_state.q_idx]
selected_question = ID_TO_Q[current_id]
problem = selected_question.get("text", "")
reference_default = selected_question.get("modelAnswer", "")

# --- 問題文と入力欄 ---
st.subheader("🧩 問題文")
st.write(problem)

with st.expander("📘 模範解答", expanded=False):
    reference = st.text_area("模範解答", value=reference_default, height=140, key=f"ref_{current_id}")

student = st.text_area(
    "🧑‍🎓 あなたの解答",
    height=200,
    placeholder="ここに回答を入力…",
    key=f"ans_{current_id}",
)

# 文字数カウンター（100字目安）
st.caption(f"現在の文字数: {len(student)} / 100")

strictness = st.slider("採点の厳しさ（1=寛容, 5=非常に厳格）", 1, 5, 3)
do_eval = st.button("採点する")

# ================ プロンプト生成 ================
def build_prompt(problem, student, reference, strictness):
    return f"""
あなたは日本語の厳格な採点者です。与えられた問題文と受験者の解答を評価し、JSONで出力してください。
出力スキーマ（余計なテキストは禁止）:
{{"s
