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

company = st.text_input("相手側の会社名")
person = st.text_input("相手側の担当者名")
industry = st.text_input("相手側の業種")
service = st.text_area("自社サービスの説明", height=120)

tone = st.selectbox("トーン（文体）", ["丁寧", "ビジネスライク", "フランク"])

st.markdown("### 文章の長さ（文字数）")
min_length, max_length = st.slider(
    "本文の文字数範囲を選択してください",
    min_value=50,
    max_value=600,
    value=(200, 300),
    step=10
)
length_text = f"{min_length}〜{max_length}文字程度"

st.markdown("---")

st.subheader("業種テンプレート（生成内容に反映）")
template_option = st.selectbox(
    "業種を選択してください",
    ["IT / SaaS", "製造業", "医療・ヘルスケア", "小売・EC", "教育"]
)

st.subheader("あなたの情報（署名として使用）")
your_company = st.text_input("あなたの会社名（自社名）")
your_name = st.text_input("あなたの氏名")
your_email = st.text_input("あなたの連絡先（メールアドレス）")
your_phone = st.text_input("あなたの電話番号")

# セッションステートで改善履歴管理
if "generated_results" not in st.session_state:
    st.session_state.generated_results = []

if st.button("営業メールを生成"):
    if all([company, person, industry, service, your_company, your_name, your_email, your_phone]):

        st.session_state.generated_results = []
        for i in range(3):
            prompt = f"""
あなたは営業メールの専門ライターです。
以下の情報を元に、営業メールを作成してください。

【ターゲット企業】
会社名：{company}
担当者名：{person}
業種：{industry}

【自社サービス】
{service}

【メール作成者（署名）】
会社名：{your_company}
氏名：{your_name}
メール：{your_email}
電話番号：{your_phone}

【業種テンプレート】
{template_option}

【トーン】
{tone}

【本文の長さ】
本文は約{length_text}に収めてください。

【条件】
・件名を必ず作る
・ビジネスメール形式
・末尾に署名（会社名 / 氏名 / メール / 電話番号）を含める

出力形式（必ずこの形式で）：
件名：
本文：
"""
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            result = response.text.strip()
            if "件名：" in result:
                try:
                    _, rest = result.split("件名：", 1)
                    title, body = rest.split("本文：", 1)
                    st.session_state.generated_results.append({
                        "title": title.strip(),
                        "body": body.strip(),
                        "history": []  # 改善履歴
                    })
                except:
                    st.session_state.generated_results.append({
                        "title": "営業メール",
                        "body": result,
                        "history": []
                    })
            else:
                st.session_state.generated_results.append({
                    "title": "営業メール",
                    "body": result,
                    "history": []
                })
    else:
        st.warning("すべての項目に入力してください。")

# ------------ タブ形式で表示 -------------
tabs = st.tabs(["メール案 A", "メール案 B", "メール案 C"])
for idx, (tab, result) in enumerate(zip(tabs, st.session_state.generated_results)):
    with tab:
        st.write("### 件名")
        st.write(result["title"])
        st.write("### 本文")
        body_content = st.text_area("", result["body"], height=250, key=f"generated_body_{idx}")

        # ---------- 改善ボタン ----------
        col1, col2, col3 = st.columns(3)
        for action, col, desc in zip(
            ["丁寧", "簡潔", "フランク"],
            [col1, col2, col3],
            ["もっと丁寧に", "簡潔に", "フランクに変更"]
        ):
            with col:
                if st.button(desc, key=f"{action}_{idx}"):
                    improve_prompt = f"""
以下の営業メールを、{action}な文体に書き換えてください。
元のメール：
件名：{result['title']}
本文：{body_content}
条件：
- ビジネスメール形式
出力形式：
件名：
本文：
"""
                    response = client.models.generate_content(
                        model=model,
                        contents=improve_prompt
                    )
                    improved = response.text.strip()
                    if "件名：" in improved:
                        _, rest = improved.split("件名：", 1)
                        title, body = rest.split("本文：", 1)
                        # 改善履歴に追加
                        result["history"].append({
                            "title": result["title"],
                            "body": result["body"]
                        })
                        result["title"] = title.strip()
                        result["body"] = body.strip()
                        st.experimental_rerun()

        # ---------- 改善履歴表示（折りたたみ式） ----------
        if result["history"]:
            with st.expander("改善履歴を表示"):
                for i, h in enumerate(result["history"]):
                    st.markdown(f"**履歴{i+1}**")
                    st.write(f"件名：{h['title']}")
                    st.text_area("", h['body'], height=150, key=f"history_{idx}_{i}")

        # ---------- コピー ----------
        copy_text = f"件名：{result['title']}\n\n本文：\n{result['body']}"
        copy_button(
            copy_text,
            tooltip="コピーする",
            copied_label="コピーしました！",
            icon="st"
        )

st.write("Developed by Sasaki Hiromu")

