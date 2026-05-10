import streamlit as st
import json
import random
import re
from pathlib import Path

st.set_page_config(page_title="司法試験 一問一答", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
@media (max-width: 768px) {
    .card { padding: 24px 16px !important; font-size: 1rem !important; min-height: 160px !important; }
    .tag { font-size: 0.72rem !important; padding: 2px 7px !important; }
    section[data-testid="stSidebar"] { min-width: 80vw !important; }
}
.card {
    background: #1e1e2e;
    border-radius: 16px;
    padding: 36px 32px 28px;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 1.15rem;
    line-height: 1.9;
    color: #cdd6f4;
    border: 1px solid #313244;
    margin: 16px 0 8px;
    word-break: break-word;
    position: relative;
}
.card-answer {
    background: #1e3a2e;
    border-color: #40a070;
}
.history-badge {
    position: absolute;
    top: 10px;
    right: 14px;
    font-size: 0.72rem;
    padding: 2px 9px;
    border-radius: 20px;
    font-weight: bold;
    letter-spacing: 0.03em;
}
.badge-ok  { background: #1e3a2e; color: #a6e3a1; border: 1px solid #40a070; }
.badge-ng  { background: #3a1e1e; color: #f38ba8; border: 1px solid #a03040; }
.tag {
    display: inline-block;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 0.8rem;
    margin: 2px;
}
.tag-chapter { background: #313244; color: #89b4fa; }
.tag-section { background: #2a2a3e; color: #cba6f7; }
.tag-text    { background: #1e3448; color: #74c7ec; }
.tag-kakomon { background: #3a2e1e; color: #fab387; }
.tag-ronshо  { background: #2e1e3a; color: #cba6f7; }
.progress-text { color: #a6adc8; font-size: 0.85rem; }
div[data-testid="stButton"] > button { min-height: 48px; font-size: 1rem; }
.stat-line { font-size: 0.88rem; color: #a6adc8; margin: 0; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_qa():
    qa_path = Path(__file__).parent / "data" / "qa.json"
    if qa_path.exists():
        with open(qa_path, encoding="utf-8") as f:
            return json.load(f)
    return [
        {"id": 1, "question": "弁論主義の第1テーゼとは何か？",
         "answer": "裁判所は、当事者が主張しない事実を判決の基礎にすることができない。",
         "category": "民事訴訟法", "section": "弁論主義", "source": "テキスト"},
    ]

def init_session():
    for key, default in [("idx", 0), ("show_answer", False), ("results", {})]:
        if key not in st.session_state:
            st.session_state[key] = default

PDF_URL = "https://drive.google.com/file/d/1Ms243AFokd5TvxCajn1tyrbKgcwT_bfR/view"

cards = load_qa()
init_session()

# ─── サイドバー ───────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ 一問一答")
    st.caption("司法試験・予備試験")
    st.divider()

    selected_src = st.radio("出題ソース", ["すべて", "テキスト", "過去問", "論証"], horizontal=True)
    st.divider()

    # 章を数値順にソートするキー
    def ch_num(s):
        m = re.search(r'第(\d+)章', s)
        return int(m.group(1)) if m else 99

    # ── 章セレクト（第1章〜第18章を数値順） ──
    all_chapters = sorted(set(c["category"] for c in cards), key=ch_num)
    ch_labels = ["すべて"] + [
        f"{ch}　({sum(1 for c in cards if c['category']==ch and (selected_src=='すべて' or c['source']==selected_src))}問)"
        for ch in all_chapters
    ]
    ch_values = ["すべて"] + all_chapters

    ch_idx = st.selectbox(
        "章",
        range(len(ch_labels)),
        format_func=lambda i: ch_labels[i]
    )
    selected_cat = ch_values[ch_idx]

    # ── セクションセレクト（選択章に絞って表示） ──
    secs = sorted(set(
        c["section"] for c in cards
        if (selected_cat == "すべて" or c["category"] == selected_cat)
        and (selected_src == "すべて" or c["source"] == selected_src)
    ))
    sec_labels = ["すべて"] + secs
    selected_sec = st.selectbox("セクション", sec_labels)
    show_only_ng = st.checkbox("✗ のみ表示（苦手問題）")
    st.divider()

    col_sh, col_rs = st.columns(2)
    with col_sh:
        if st.button("シャッフル", use_container_width=True):
            st.session_state.idx = 0
            st.session_state.show_answer = False
            st.session_state.pop("deck", None)
            st.rerun()
    with col_rs:
        if st.button("リセット", use_container_width=True):
            st.session_state.results = {}
            st.session_state.idx = 0
            st.session_state.show_answer = False
            st.session_state.pop("deck", None)
            st.rerun()

    results = st.session_state.results
    ok_count  = sum(1 for v in results.values() if v == "ok")
    ng_count  = sum(1 for v in results.values() if v == "ng")
    done_ids  = set(results.keys())
    total_all = len(cards)
    undone    = total_all - len(done_ids)

    st.markdown(
        f'<p class="stat-line">'
        f'<span style="color:#a6e3a1">✓ {ok_count}</span>　'
        f'<span style="color:#f38ba8">✗ {ng_count}</span>　'
        f'<span style="color:#6c7086">？{undone}</span>'
        f'</p>',
        unsafe_allow_html=True
    )

# ─── フィルタ ─────────────────────────────────────────────
filtered = [
    c for c in cards
    if (selected_src == "すべて" or c["source"] == selected_src)
    and (selected_cat == "すべて" or c["category"] == selected_cat)
    and (selected_sec == "すべて" or c["section"] == selected_sec)
    and (not show_only_ng or results.get(str(c["id"])) == "ng")
]

if not filtered:
    st.info("該当する問題がありません。")
    st.stop()

# ─── デッキ管理 ───────────────────────────────────────────
if "deck" not in st.session_state or len(st.session_state.deck) != len(filtered):
    deck = list(range(len(filtered)))
    random.shuffle(deck)
    st.session_state.deck = deck

idx          = st.session_state.idx % len(filtered)
current_card = filtered[st.session_state.deck[idx]]
card_id      = str(current_card["id"])
total        = len(filtered)
current_num  = idx + 1
prev_result  = results.get(card_id)

# ─── ヘッダー ─────────────────────────────────────────────
src_class = {"過去問": "tag-kakomon", "論証": "tag-ronshо"}.get(current_card["source"], "tag-text")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(
        f'<span class="tag tag-chapter">{current_card["category"]}</span> '
        f'<span class="tag tag-section">{current_card["section"]}</span> '
        f'<span class="tag {src_class}">{current_card["source"]}</span>',
        unsafe_allow_html=True
    )
with col2:
    pct = int(current_num / total * 100)
    st.markdown(
        f'<div class="progress-text" style="text-align:right;padding-top:8px">'
        f'{current_num} / {total}　<b>{pct}%</b></div>',
        unsafe_allow_html=True
    )

st.progress(current_num / total)

# ─── 前回バッジ ───────────────────────────────────────────
if prev_result == "ok":
    badge_html = '<span class="history-badge badge-ok">前回 ✓ 覚えた</span>'
elif prev_result == "ng":
    badge_html = '<span class="history-badge badge-ng">前回 ✗ 要復習</span>'
else:
    badge_html = ""

# ─── カード ───────────────────────────────────────────────
q_text = current_card["question"].replace("\n", "<br>")
a_text = current_card["answer"].replace("\n", "<br>")

if not st.session_state.show_answer:
    st.markdown(
        f'<div class="card">{badge_html}Q.&nbsp;{q_text}</div>',
        unsafe_allow_html=True
    )
    btn_col, skip_col = st.columns([3, 1])
    with btn_col:
        if st.button("答えを見る", use_container_width=True, type="primary"):
            st.session_state.show_answer = True
            st.rerun()
    with skip_col:
        if st.button("スキップ →", use_container_width=True):
            st.session_state.idx += 1
            st.session_state.show_answer = False
            st.rerun()
else:
    st.markdown(
        f'<div class="card">{badge_html}Q.&nbsp;{q_text}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="card card-answer">A.&nbsp;{a_text}</div>',
        unsafe_allow_html=True
    )

    # ─── 参照ページ & PDFリンク ────────────────────────────
    ref_page = current_card.get("page")
    ref_col, pdf_col = st.columns([1, 1])
    with ref_col:
        if ref_page:
            st.caption(f"参照: テキスト p.{ref_page}")
    with pdf_col:
        st.link_button("テキストPDFで確認", PDF_URL, use_container_width=True)

    col_ok, col_ng = st.columns(2)
    with col_ok:
        if st.button("✓ 覚えた", use_container_width=True, type="primary"):
            st.session_state.results[card_id] = "ok"
            st.session_state.idx += 1
            st.session_state.show_answer = False
            st.rerun()
    with col_ng:
        if st.button("✗ もう一度", use_container_width=True):
            st.session_state.results[card_id] = "ng"
            st.session_state.idx += 1
            st.session_state.show_answer = False
            st.rerun()

# ─── 1周完了 ──────────────────────────────────────────────
if current_num == total and not st.session_state.show_answer:
    ok_f  = sum(1 for c in filtered if results.get(str(c["id"])) == "ok")
    ng_f  = sum(1 for c in filtered if results.get(str(c["id"])) == "ng")
    rate  = int(ok_f / total * 100) if total else 0
    st.success(f"1周完了！　正解 {ok_f} 問 / {total} 問　正答率 {rate}%　　要復習 {ng_f} 問")

    # 章別正答率
    with st.expander("章別の正答率を見る"):
        chapters = sorted(set(c["category"] for c in filtered))
        for ch in chapters:
            ch_cards = [c for c in filtered if c["category"] == ch]
            ch_ok = sum(1 for c in ch_cards if results.get(str(c["id"])) == "ok")
            ch_total = len(ch_cards)
            ch_rate = ch_ok / ch_total if ch_total else 0
            short = ch.split(" ", 1)[0]  # "第1章" だけ抽出
            st.markdown(f"**{short}** {ch_ok}/{ch_total}")
            st.progress(ch_rate)

    if st.button("もう一周する", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.show_answer = False
        st.rerun()
