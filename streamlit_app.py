import os
import json
import requests
import streamlit as st

# --- 基本設定 ---
st.set_page_config(page_title="試験対策アプリ", page_icon="📝", layout="centered")

# --- APIキー（GOOGLE_API_KEY でも可） ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Secrets に GEMINI_API_KEY（または GOOGLE_API_KEY）が設定されていません。")
    st.stop()

PRIMARY_MODEL = "gemini-1.5-pro-latest"    # 厳密評価
FALLBACK_MODEL = "gemini-1.5-flash-latest" # 高速評価

# --- 問題データ ---
try:
    with open("constants.json", "r", encoding="utf-8") as f:
        QUESTIONS = json.load(f)
except FileNotFoundError:
    st.error("❌ constants.json が見つかりません。リポジトリ直下に配置してください。")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ constants.json のパースに失敗: {e}")
    st.stop()

# --- UI ---
st.title("📝試験対策アプリ")
st.markdown("出題を選んで受験者の解答を入力すると、AI が **10点満点** で採点します。")

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

# --- プロンプト生成 ---
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

# --- REST 呼び出し（v1固定・タイムアウト付） ---
def call_gemini_v1(prompt: str, model: str, timeout: int = 30) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0}
    }
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        # エラー本文を短くして提示
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    j = r.json()
    try:
        return j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"応答解析エラー: {e}\nRaw: {j}")

def parse_json_loose(text: str) -> dict:
    # ```json ～ ``` の除去や前後ノイズを吸収
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t else t
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSONブロックが見つかりません。")
    return json.loads(t[start:end+1])

# --- 採点処理 ---
if do_eval:
    if not problem or not student:
        st.warning("⚠️ 問題文と受験者の解答は必須です。")
        st.stop()

    prompt = build_prompt(problem, student, reference, strictness)

    text = None
    used_model = PRIMARY_MODEL
    with st.spinner("Gemini が採点中…"):
        try:
            text = call_gemini_v1(prompt, PRIMARY_MODEL, timeout=30)
        except Exception as e1:
            # pro が失敗したら flash にフォールバック
            used_model = FALLBACK_MODEL
            try:
                text = call_gemini_v1(prompt, FALLBACK_MODEL, timeout=30)
            except Exception as e2:
                st.error(f"❌ API呼び出し失敗\n- {PRIMARY_MODEL}: {e1}\n- {FALLBACK_MODEL}: {e2}")
                st.stop()

    try:
        data = parse_json_loose(text)
    except Exception:
        st.error("❌ 採点結果の解析に失敗しました。モデルの生出力を表示します。")
        with st.expander("モデルの生出力"):
            st.code(text or "", language="json")
        st.stop()

    # --- 結果表示 ---
    st.success(f"✅ 採点完了（{used_model}）")
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

    with st.expander("🧠 採点ロジック詳細（理由）"):
        st.write(data.get("reasoning", ""))

st.markdown("---")
st.caption("Powered by Streamlit × Google Gemini（REST / v1） ・ 問題データ: constants.json")
