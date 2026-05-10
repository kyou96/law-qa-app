import streamlit as st
import json
import random
from pathlib import Path

st.set_page_config(page_title="司法試験 一問一答", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
/* スマホ・タブレット対応 */
@media (max-width: 768px) {
    .card {
        padding: 24px 16px !important;
        font-size: 1rem !important;
        min-height: 160px !important;
    }
    .tag {
        font-size: 0.72rem !important;
        padding: 2px 7px !important;
    }
    section[data-testid="stSidebar"] {
        min-width: 80vw !important;
    }
}
.card {
    background: #1e1e2e;
    border-radius: 16px;
    padding: 40px 32px;
    min-height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 1.15rem;
    line-height: 1.9;
    color: #cdd6f4;
    border: 1px solid #313244;
    margin: 16px 0;
    word-break: break-word;
}
.card-answer {
    background: #1e3a2e;
    border-color: #40a070;
}
.tag {
    display: inline-block;
    background: #313244;
    color: #89b4fa;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 0.8rem;
    margin: 2px;
}
.progress-text {
    color: #a6adc8;
    font-size: 0.85rem;
}
/* ボタンをスマホで大きく */
div[data-testid="stButton"] > button {
    min-height: 48px;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_qa():
    qa_path = Path(__file__).parent / "data" / "qa.json"
    if qa_path.exists():
        with open(qa_path, encoding="utf-8") as f:
            return json.load(f)
    # OCR完了前の動作確認用サンプル
    return [
        {
            "id": 1,
            "question": "弁論主義の第1テーゼとは何か？",
            "answer": "裁判所は、当事者が主張しない事実を判決の基礎にすることができない。主要事実は当事者の弁論に現れたものに限られる。",
            "category": "民事訴訟法",
            "section": "弁論主義",
            "source": "テキスト"
        },
        {
            "id": 2,
            "question": "処分権主義とは何か？",
            "answer": "訴訟の開始・審判対象の特定・訴訟の終了について当事者に主導権を認める原則。裁判所は当事者が申し立てていない事項について判決できない（246条）。",
            "category": "民事訴訟法",
            "section": "基本原則",
            "source": "テキスト"
        },
        {
            "id": 3,
            "question": "既判力の客観的範囲はどこまでか？",
            "answer": "判決主文に包含された判断に限られる（114条1項）。理由中の判断には原則として既判力は生じない。",
            "category": "民事訴訟法",
            "section": "既判力",
            "source": "テキスト"
        },
        {
            "id": 4,
            "question": "自由心証主義とは何か？",
            "answer": "証拠の証明力の評価を裁判官の自由な判断に委ねる原則（247条）。証拠能力に制限がない民事訴訟で特に重要。",
            "category": "民事訴訟法",
            "section": "証拠",
            "source": "テキスト"
        },
        {
            "id": 5,
            "question": "訴えの利益が認められるための要件は？",
            "answer": "①紛争の成熟性（判決を求める必要性）、②訴訟類型の適合性、③現在の法律状態を変更する必要性の3つ。",
            "category": "民事訴訟法",
            "section": "訴訟要件",
            "source": "テキスト"
        },
    ]

def init_session():
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False
    if "results" not in st.session_state:
        st.session_state.results = {}

cards = load_qa()
init_session()

# サイドバー
with st.sidebar:
    st.title("⚖️ 一問一答")
    st.caption("司法試験・予備試験")
    st.divider()

    # ソース選択
    sources = ["すべて", "テキスト", "過去問"]
    selected_src = st.radio("出題ソース", sources, horizontal=True)

    st.divider()

    # 章・セクション 階層ナビ
    nav_labels = ["すべて"]
    nav_values = [("すべて", "すべて")]
    for ch in sorted(set(c["category"] for c in cards)):
        nav_labels.append(ch)
        nav_values.append((ch, "すべて"))
        for s in sorted(set(
            c["section"] for c in cards
            if c["category"] == ch
            and (selected_src == "すべて" or c["source"] == selected_src)
        )):
            nav_labels.append(f"　└ {s}")
            nav_values.append((ch, s))

    nav_idx = st.selectbox(
        "章・セクション",
        range(len(nav_labels)),
        format_func=lambda i: nav_labels[i]
    )
    selected_cat, selected_sec = nav_values[nav_idx]
    show_only_ng = st.checkbox("✗ のみ表示（苦手問題）")

    st.divider()
    if st.button("シャッフル", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.show_answer = False
        st.session_state.pop("deck", None)
        st.rerun()

    ok_count = sum(1 for v in st.session_state.results.values() if v == "ok")
    ng_count = sum(1 for v in st.session_state.results.values() if v == "ng")
    st.markdown(f"正解: **{ok_count}**　　要復習: **{ng_count}**")

# フィルタ
filtered = [
    c for c in cards
    if (selected_src == "すべて" or c["source"] == selected_src)
    and (selected_cat == "すべて" or c["category"] == selected_cat)
    and (selected_sec == "すべて" or c["section"] == selected_sec)
    and (not show_only_ng or st.session_state.results.get(str(c["id"])) == "ng")
]

if not filtered:
    st.info("該当する問題がありません。")
    st.stop()

# デッキ管理（シャッフル順を保持）
if "deck" not in st.session_state or len(st.session_state.deck) != len(filtered):
    deck = list(range(len(filtered)))
    random.shuffle(deck)
    st.session_state.deck = deck

idx = st.session_state.idx % len(filtered)
current_card = filtered[st.session_state.deck[idx]]
card_id = str(current_card["id"])
total = len(filtered)
current_num = idx + 1

# ヘッダー
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(
        f'<span class="tag">{current_card["category"]}</span> '
        f'<span class="tag">{current_card["section"]}</span> '
        f'<span class="tag">{current_card["source"]}</span>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="progress-text" style="text-align:right;padding-top:8px">'
        f'{current_num} / {total}</div>',
        unsafe_allow_html=True
    )

st.progress(current_num / total)

# カード
if not st.session_state.show_answer:
    st.markdown(f'<div class="card">Q. {current_card["question"]}</div>', unsafe_allow_html=True)
    if st.button("答えを見る", use_container_width=True, type="primary"):
        st.session_state.show_answer = True
        st.rerun()
else:
    st.markdown(f'<div class="card">Q. {current_card["question"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card card-answer">A. {current_card["answer"]}</div>', unsafe_allow_html=True)

    col_ok, col_ng = st.columns(2)
    with col_ok:
        if st.button("覚えた", use_container_width=True, type="primary"):
            st.session_state.results[card_id] = "ok"
            st.session_state.idx += 1
            st.session_state.show_answer = False
            st.rerun()
    with col_ng:
        if st.button("もう一度", use_container_width=True):
            st.session_state.results[card_id] = "ng"
            st.session_state.idx += 1
            st.session_state.show_answer = False
            st.rerun()

# 1周完了
if current_num == total and not st.session_state.show_answer:
    st.success(f"1周完了！　正解 {ok_count} 問　要復習 {ng_count} 問")
    if st.button("もう一周する"):
        st.session_state.idx = 0
        st.session_state.show_answer = False
        st.rerun()
