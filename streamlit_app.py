import os
import json
import streamlit as st
import google.generativeai as genai

# ====== 基本設定 ======
st.set_page_config(page_title="Exam Prep AI Grader (Gemini)", page_icon="📝", layout="centered")

# ====== APIキー設定（Secretsから取得） ======
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # 厳密評価にしたい場合は "gemini-1.5-pro"

# ====== constants.json を読み込む ======
try:
    with open("constants.json", "r", encoding="utf-8") as f:
        QUESTIONS = json.load(f)
except FileNotFoundError:
    st.error("❌ constants.json が見つかりません。リポジトリ直下に配置してください。")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ constants.json のパースに失敗しました: {e}")
    st.stop()

# ====== UI ======
st.title("📝 Exam Prep AI Grader (Gemini)")
st.markdown("出題を選んで受験者の解答を入力すると、AI が **10点満点** で採点します。")

# プルダウンで問題選択
options = {q["id"]: f"{q['id']}: {q.get('subject', 'No Subject')}" for q in QUESTIONS}
selected_id = st.selectbox("出題を選んでください", options.keys(), format_func=lambda x: options[x])

# 選択された問題を取得
selected_question = next(q for q in QUESTIONS if q["id"] == selected_id)
problem = selected_question.get("text", "")
reference_default = selected_question.get("modelAnswer", "")

# 表示
st.subheader("🧩 問題文")
st.write(problem)

with st.expander("📘 模範解答", expanded=False):
    reference = st.text_area("模範解答", value=reference_default, height=140)

student = st.text_area("🧑‍🎓 あなたの解答", height=200, placeholder="ここに回答を入力…")

# 厳しさだけ調整可能
strictness = st.slider("採点の厳しさ（1=寛容, 5=非常に厳格）", 1, 5, 3)

do_eval = st.button("採点する")

# ====== プロンプト生成関数 ======
def build_prompt(problem, student, reference, strictness):
    return f"""
あなたは日本語の厳格な採点者です。与えられた問題文と受験者の解答を評価し、JSONで出力してください。

出力は必ず次のJSONスキーマに従ってください（余計なテキストは出力しない）:
{{
  "score": <number 0-10>,
  "rubric": "採点基準の要約",
  "strengths": ["良い点1", "良い点2"],
  "weaknesses": ["不足点1", "不足点2"],
  "improvements": ["改善提案1", "改善提案2"],
  "reasoning": "最終スコアに至った根拠の説明"
}}

採点の厳しさ（1=寛容, 5=非常に厳格）: {strictness}

問題文:
{problem}

受験者の解答:
{student}

模範解答（任意、空なら参考にしない）:
{reference}
"""

# ====== 採点処理 ======
if do_eval:
    if not problem or not student:
        st.warning("⚠️ 問題文と受験者の解答は必須です。")
        st.stop()

    prompt = build_prompt(problem, student, reference, strictness)

    try:
        with st.spinner("Gemini が採点中…"):
            model = genai.GenerativeModel(MODEL_NAME)
            resp = model.generate_content(prompt)
    except Exception as e:
        st.error(f"❌ API呼び出しでエラー: {e}")
        st.stop()

    text = (resp.text or "").strip()
    try:
        start = text.find("{")
        end = text.rfind("}")
        data = json.loads(text[start:end+1])
    except Exception:
        st.error("❌ 採点結果の解析に失敗しました。モデルの生出力を表示します。")
        st.code(text)
        st.stop()

    # ====== 結果表示 ======
    st.success("✅ 採点完了")
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
st.caption("Powered by Streamlit × Google Gemini ・ 問題データ: constants.json")
