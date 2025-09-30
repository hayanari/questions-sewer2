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
    for m in j.get("models", []):
        name = (m.get("name") or "").split("/")[-1]  # models/xxx → xxx
        methods = m.get("supportedGenerationMethods") or m.get("supported_generation_methods") or []
        if "generateContent" in methods:
            names.append(name)
    return names

def call_gemini(prompt: str, api_ver: str, model: str, timeout=30) -> str:
    """/v1 or /v1beta の generateContent を直接叩く"""
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent?key={API_KEY}"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
               "generationConfig": {"temperature": 0}}
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{api_ver}/{model}: HTTP {r.status_code}: {r.text[:400]}")
    j = r.json()
    try:
        return j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"{api_ver}/{model}: 応答解析エラー: {e} / Raw: {str(j)[:400]}")

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

# ================ 診断UI ================
with st.expander("🔧 診断（まずはここを開いて確認）", expanded=True):
    st.write("- ここで **利用可能モデル** を実際に取得し、採点時の候補に使います。")
    cols = st.columns(3)
    if "ALL_MODELS" not in st.session_state:
        st.session_state.ALL_MODELS = []
    if "API_VER" not in st.session_state:
        st.session_state.API_VER = "v1"  # 仮

    if cols[0].button("モデル一覧取得（v1）"):
        try:
            names = list_models("v1")
            st.session_state.ALL_MODELS = names
            st.session_state.API_VER = "v1"
            st.success(f"v1で取得：{len(names)}件")
            st.code("\n".join(names) or "(なし)")
        except Exception as e:
            st.error(f"v1 取得失敗: {e}")

    if cols[1].button("モデル一覧取得（v1beta）"):
        try:
            names = list_models("v1beta")
            st.session_state.ALL_MODELS = names
            st.session_state.API_VER = "v1beta"
            st.success(f"v1betaで取得：{len(names)}件")
            st.code("\n".join(names) or "(なし)")
        except Exception as e:
            st.error(f"v1beta 取得失敗: {e}")

    # 一覧が空ならPREFERREDで埋めておく（404でも一応試行できる）
    if not st.session_state.ALL_MODELS:
        st.info("モデル一覧が未取得なので、既定候補（PREFERRED）で試行します。")
        st.code("\n".join(PREFERRED))

# ================ メインUI ================
st.title("📝試験対策アプリ")
st.markdown("出題を選んで受験者の解答を入力すると、AI が **10点満点** で採点します。")

# ===== 出題ナビ（戻る／次へ 付き） =====
ID_TO_Q = {q["id"]: q for q in QUESTIONS}
ORDERED_IDS = sorted(ID_TO_Q.keys())

if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0

def on_select_change():
    sel_id = st.session_state.selected_id
    st.session_state.q_idx = ORDERED_IDS.index(sel_id)

def go_prev():
    if st.session_state.q_idx > 0:
        st.session_state.q_idx -= 1
        st.session_state.selected_id = ORDERED_IDS[st.session_state.q_idx]

def go_next():
    if st.session_state.q_idx < len(ORDERED_IDS) - 1:
        st.session_state.q_idx += 1
        st.session_state.selected_id = ORDERED_IDS[st.session_state.q_idx]

selected_id = st.selectbox(
    "出題を選んでください",
    options=ORDERED_IDS,
    index=st.session_state.q_idx,
    format_func=lambda i: f"{i}: {ID_TO_Q[i].get('subject','No Subject')}",
    key="selected_id",
    on_change=on_select_change,
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

with st.expander("📘 模範解答", expanded=False):
    reference = st.text_area("模範解答", value=reference_default, height=140, key=f"ref_{current_id}")
student = st.text_area("🧑‍🎓 あなたの解答", height=200, placeholder="ここに回答を入力…", key=f"ans_{current_id}")


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

# ================ 採点処理 ================
if do_eval:
    if not problem or not student:
        st.warning("⚠️ 問題文と受験者の解答は必須です。")
        st.stop()

    prompt = build_prompt(problem, student, reference, strictness)

    # 試すAPIバージョンとモデルの組み合わせを作成
    api_versions = [st.session_state.API_VER] if st.session_state.ALL_MODELS else ["v1", "v1beta"]
    model_pool = (st.session_state.ALL_MODELS or PREFERRED)

    errors = []
    text = None
    used = None

    with st.spinner("Gemini が採点中…"):
        for ver in api_versions:
            for m in model_pool:
                try:
                    text = call_gemini(prompt, ver, m, timeout=30)
                    used = (ver, m)
                    break
                except Exception as e:
                    errors.append(str(e))
            if text:
                break

    if not text:
        st.error("❌ すべての候補で失敗しました。直近のエラーを表示します。")
        with st.expander("エラーログ（上から順に試行）"):
            st.code("\n\n".join(errors[-10:]) or "(なし)")
        st.stop()

    try:
        data = parse_json_loose(text)
    except Exception:
        st.error("❌ 採点結果の解析に失敗しました。モデルの生出力を表示します。")
        with st.expander("モデルの生出力"):
            st.code(text or "", language="json")
        st.stop()

    st.success(f"✅ 採点完了（{used[0]} / {used[1]}）")
    st.metric("スコア", f"{data.get('score', 0)} / 10")

    st.subheader("採点基準（Rubric）")
    st.write(data.get("rubric", ""))

    colA, colB = st.columns(2)
    with colA:
        st.subheader("👍 良かった点")
        for s in data.get("strengths", []):
            st.markdown(f"- {s}")
    with colB:
        st.subheader("⚠️ 不足・誤り")
        for w in data.get("weaknesses", []):
            st.markdown(f"- {w}")

    st.subheader("🛠 改善提案")
    for i in data.get("improvements", []):
        st.markdown(f"- {i}")

    with st.expander("🧠 採点ロジック（理由）"):
        st.write(data.get("reasoning", ""))

st.markdown("---")
st.caption("Powered by Streamlit × Google Gemini（REST） ・ 問題データ: constants.json")
