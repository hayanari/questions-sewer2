import json
import streamlit as st
import google.generativeai as genai

# ====== 設定 ======
# Streamlit Cloud の [Advanced settings] → [Secrets] に GEMINI_API_KEY を保存してください
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

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
    return f"""
あなたは日本語の厳格な採点者です。与えられた問題文と受験者の解答を評価し、JSONで出力してください。

出力は **必ず** 次のJSONスキーマに従ってください（余計なテキストは出力しない）:
{{
  "score": <number 0-{score_max}>,
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

if do_eval:
    if not problem or not student:
        st.warning("問題文と受験者の解答は必須です。")
        st.stop()

    prompt = build_prompt(problem, student, reference, score_max, strictness)
    with st.spinner("Geminiが採点中…"):
        model = genai.GenerativeModel(MODEL_NAME)
        resp = model.generate_content(prompt)

    text = resp.text or ""
    # JSONだけ返ってくる想定だが、頑健性のためパースを工夫
    try:
        # 余分なバッククォートや前後テキストが混じる場合に備えて抽出
        start = text.find("{")
        end = text.rfind("}")
        data = json.loads(text[start:end+1])
    except Exception:
        st.error("採点結果の解析に失敗しました。出力を表示します。")
        st.code(text)
        st.stop()

    st.success("採点完了")
    st.metric("スコア", f"{data.get('score', 0)} / {score_max}")
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
st.caption("Powered by Streamlit × Google Gemini")
