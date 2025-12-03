import os
import streamlit as st
from google import genai

from st_copy import copy_button

# ページ設定
st.title("営業メール自動生成アプリ")

# Gemini APIクライアント
@st.cache_resource
def get_client():
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

client = get_client()
model = "gemini-flash-lite-latest"

# ------------ 入力欄 UI -------------
st.subheader("メール情報を入力")

company = st.text_input("会社名")
person = st.text_input("担当者名")
industry = st.text_input("業種")
service = st.text_area("自社サービス説明", height=120)

tone = st.selectbox("トーン（文体）", ["丁寧", "ビジネスライク", "フランク"])

# 生成メールの保持用
generated_title = ""
generated_body = ""

# ------------ メール生成 -------------
if st.button("営業メールを生成"):
    if company and person and industry and service:
        # プロンプト生成
        prompt = f"""
あなたは営業メールの専門ライターです。
以下の情報を元に、営業メールを作成してください。

【ターゲット企業】
会社名：{company}
担当者名：{person}
業種：{industry}

【自社サービス】
{service}

【トーン】
{tone}

【条件】
・件名を必ず作る
・本文は200〜300文字程度
・ビジネスメール形式

出力形式（必ずこの形式で）：
件名：
本文：
"""

        # Gemini API 呼び出し
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        result = response.text.strip()

        # 出力解析
        if "件名：" in result:
            try:
                _, rest = result.split("件名：", 1)
                title, body = rest.split("本文：", 1)
                generated_title = title.strip()
                generated_body = body.strip()
            except:
                generated_title = "営業メール"
                generated_body = result
        else:
            generated_title = "営業メール"
            generated_body = result

        # 出力表示
        st.subheader("生成されたメール")

        # 件名
        st.write("### 件名")
        st.write(generated_title)

        # 本文
        st.write("### 本文")
        st.text_area("", generated_body, height=200, key="generated_body_area")


        copy_button(
            "Text to copy",
            tooltip="Copy this text",
            copied_label="Copied!",
            icon="st",  # または 'material_symbols'
        )


    else:
        st.warning("すべての項目に入力してください。")
st.write("Developed by Sasaki Hiromu") 