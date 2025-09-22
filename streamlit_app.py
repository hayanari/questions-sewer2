import os
import streamlit as st

st.set_page_config(page_title="Secrets診断", page_icon="🔍")

st.title("🔍 Streamlit Secrets 診断")

# 1) st.secrets に何が入っているか（値は表示しない）
try:
    keys = list(st.secrets.keys())
except Exception as e:
    keys = []
    st.error(f"st.secrets にアクセスできません: {e}")

st.subheader("Secrets に登録されているキー名")
st.write(keys if keys else "（0件）")

# 2) GEMINI_API_KEY 取得テスト（値は伏せる）
has_secret = False
try:
    _ = st.secrets["GEMINI_API_KEY"]
    has_secret = True
except Exception:
    has_secret = False

st.subheader("GEMINI_API_KEY の存在チェック")
st.write("✅ 見つかりました" if has_secret else "❌ 見つかりません")

# 3) 環境変数でも入っているか確認（Cloudだと通常未設定）
env_val = os.getenv("GEMINI_API_KEY")
st.subheader("環境変数 GEMINI_API_KEY の存在チェック")
st.write("✅ 見つかりました" if env_val else "❌ 見つかりません")

st.markdown("---")
st.caption("表示しているのは“キー名”だけで秘密の値は出しません。")
