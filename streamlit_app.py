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

# モデル候補（順に試す）
PREFERRED = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
]

# ================ ユーティリティ ================
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

# ================ メインUI ================
st.title("第3節 下水道の種類｜短答100字演習")
st.caption("出典：§1.3.1 下水道の種類（第3節 下水道の種類）")
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

# ★ 解答文字数カウンター（100字目安）
st.caption(f"現在の文字数: {len(student)} / 100")

strictness = st.slider("採点の厳しさ（1=寛容, 5=非常に厳格）", 1, 5, 3)
do_eval = st.button("採点する")

# ================ プロンプト生成 ================
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

    # v1 → v1beta の順で試す
    api_versions = ["v1", "v1beta"]
    model_pool = PREFERRED

    errors, text, used = [], None, None
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
        st.error("❌ すべての候補で失敗しました。")
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

    # ======= 結果表示（整形版） =======
    st.success(f"✅ 採点完了（{used[0]} / {used[1]}）")

    score_val = data.get("score", 0)
    st.markdown(
        f"""
        <div style="font-size:28px;font-weight:700;margin:8px 0 2px 0;">スコア</div>
        <div style="font-size:42px;font-weight:800;line-height:1;">{score_val} / 10</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 採点基準（Rubric）")
    st.write(data.get("rubric", ""))

    def norm_list(x):
        if x is None: return []
        if isinstance(x, str): return [x]
        if isinstance(x, (list, tuple)): return [str(i) for i in x if str(i).strip()]
        return [str(x)]

    def render_bullets(items):
        if not items:
            st.markdown("- （記載なし）")
            return
        st.markdown("\n".join([f"- {i}" for i in items]))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👍 良かった点")
        render_bullets(norm_list(data.get("strengths")))
    with col2:
        st.markdown("### ⚠️ 不足・誤り")
        render_bullets(norm_list(data.get("weaknesses")))

    st.markdown("### 🛠 改善提案")
    render_bullets(norm_list(data.get("improvements")))

    with st.expander("🧠 採点ロジック（理由）", expanded=False):
        st.write(data.get("reasoning", ""))

    # 箇条書きの余白調整
    st.markdown(
        """
        <style>
        ul { margin-top: 0.25rem; margin-bottom: 0.75rem; }
        li { margin: 0.25rem 0; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")
st.caption("Powered by Streamlit × Google Gemini（REST） ・ 問題データ: constants.json")
