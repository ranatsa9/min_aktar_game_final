import html
import os
import sqlite3
from pathlib import Path

import streamlit as st


DB = Path(__file__).with_name("game.db")
HOST_PIN = os.getenv("HOST_PIN", "2468")
MAX_PLAYERS = 29

QUESTIONS = [
    "مين أكثر شخص يتأخر عن المحاضرات؟",
    "مين أكثر شخص دايم يسأل أستاذة خلود؟",
    "مين أكثر شخص ترشّحونه يكون مدرّب؟",
    "مين أكثر شخص يضحك في المحاضرات؟",
    'مين أكثر شخص يختفي أول ما يقولون "بريك"؟',
    "مين أكثر شخص يعرف يقنع التيم بأي شيء؟",
    "مين أكثر شخص يعتمد عليه التيم وقت الزنقة؟",
    "مين أكثر شخص يخلّص شغله بدري؟",
    "مين أكثر شخص يساعد أعضاء التيم حتى لو خلّص شغله؟",
    "مين أكثر شخص إذا ما اشتغل، التيم كله يتعطل؟",
    "مين أكثر شخص يبدأ يشتكي من الواجب أول ما يشوفه؟",
    "مين أكثر شخص يتمسك برأيه في المشروع؟",
    "مين أكثر شخص يعرف يتصرف مع السؤال المفاجئ؟",
    "مين أكثر شخص ممكن يطلع بفكرة مشروع غير متوقعة؟",
    "مين أكثر شخص عنده أفكار أكثر من الوقت المتاح؟ 😂",
    "مين أكثر شخص يبدأ المشروع بحماس ثم يختفي؟ 😂",
    "مين أكثر شخص تتوقعون يفتح مشروعه الخاص بعد المعسكر؟",
    "مين أكثر شخص ممكن يغيّر تخصصه بعد المعسكر؟",
    "مين أكثر شخص حسبته رسمي، لكن طلع فلّة؟",
    "مين أكثر شخص اكتشفت أنه شاطر جدًا؟",
    "مين أكثر شخص ما يدخل الكلاس بدون مشروب بيده؟",
    'مين أكثر شخص يذكّرك بشخصية "المدير" حتى بدون منصب؟',
]


def get_db():
    con = sqlite3.connect(DB, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def init_db():
    with get_db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id=1), question_index INTEGER DEFAULT 0,
            voting_open INTEGER DEFAULT 0, game_started INTEGER DEFAULT 0)""")
        con.execute("CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY)")
        con.execute("""CREATE TABLE IF NOT EXISTS votes (
            question_index INTEGER, voter TEXT, candidate TEXT,
            PRIMARY KEY(question_index, voter))""")
        con.execute("INSERT OR IGNORE INTO settings(id) VALUES (1)")


def settings():
    with get_db() as con:
        return dict(con.execute("SELECT * FROM settings WHERE id=1").fetchone())


def set_settings(**values):
    allowed = {"question_index", "voting_open", "game_started"}
    with get_db() as con:
        for key, value in values.items():
            if key not in allowed:
                raise ValueError("Invalid setting")
            con.execute(f"UPDATE settings SET {key}=? WHERE id=1", (value,))


def players():
    with get_db() as con:
        return [r["name"] for r in con.execute("SELECT name FROM players ORDER BY rowid")]


def add_player(name):
    name = " ".join(name.strip().split())
    if not name:
        return False, "اكتب اسمك أولًا."
    if len(name) > 30:
        return False, "الاسم طويل جدًا."
    with get_db() as con:
        current = [r[0] for r in con.execute("SELECT name FROM players")]
        if any(p.casefold() == name.casefold() for p in current):
            return False, "هذا الاسم مستخدم بالفعل."
        if len(current) >= MAX_PLAYERS:
            return False, f"اكتمل عدد اللاعبين ({MAX_PLAYERS})."
        con.execute("INSERT INTO players(name) VALUES(?)", (name,))
    return True, "تم التسجيل!"


def remove_player(name):
    with get_db() as con:
        con.execute("DELETE FROM votes WHERE voter=? OR candidate=?", (name, name))
        con.execute("DELETE FROM players WHERE name=?", (name,))


def vote(question, voter, candidate):
    if voter == candidate or voter not in players() or candidate not in players():
        return False
    try:
        with get_db() as con:
            con.execute("INSERT INTO votes VALUES (?, ?, ?)", (question, voter, candidate))
        return True
    except sqlite3.IntegrityError:
        return False


def vote_details(question):
    with get_db() as con:
        return [(r["voter"], r["candidate"]) for r in con.execute(
            "SELECT voter,candidate FROM votes WHERE question_index=? ORDER BY rowid", (question,))]


def counts(question=None):
    with get_db() as con:
        if question is None:
            rows = con.execute("SELECT candidate,COUNT(*) total FROM votes GROUP BY candidate ORDER BY total DESC,candidate")
        else:
            rows = con.execute("SELECT candidate,COUNT(*) total FROM votes WHERE question_index=? GROUP BY candidate ORDER BY total DESC,candidate", (question,))
        return [(r["candidate"], r["total"]) for r in rows]


def reset_game():
    with get_db() as con:
        con.execute("DELETE FROM votes")
        con.execute("DELETE FROM players")
        con.execute("UPDATE settings SET question_index=0,voting_open=0,game_started=0 WHERE id=1")


def roster_html(roster):
    """Small, safe player badges used in the lobby and above voting."""
    return '<div class="roster">' + "".join(
        f"<span>👤 {html.escape(player)}</span>" for player in roster
    ) + "</div>"


init_db()
st.set_page_config(page_title="مين أكثر؟", page_icon="🏆", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap');
:root { --purple:#6c3ce0; --pink:#ec4899; --ink:#17132b; }
html, body, [class*="st-"] { font-family:'Tajawal',sans-serif; }
.stApp { direction:rtl; background:
 radial-gradient(circle at 88% 4%,rgba(236,72,153,.18),transparent 24rem),
 radial-gradient(circle at 8% 25%,rgba(124,58,237,.18),transparent 22rem),
 linear-gradient(160deg,#fff 0%,#faf7ff 48%,#fff7fb 100%); color:var(--ink); }
.block-container { max-width:880px; padding-top:1.5rem; padding-bottom:4rem; }
.hero { text-align:center; padding:1.1rem .5rem 1.4rem; position:relative; }
.hero:before { content:'✨'; position:absolute; right:12%; top:8%; font-size:1.8rem; transform:rotate(12deg); }
.hero:after { content:'🎉'; position:absolute; left:12%; bottom:18%; font-size:1.7rem; transform:rotate(-12deg); }
.hero h1 { font-size:clamp(2.4rem,8vw,4.3rem); margin:0; font-weight:900;
 background:linear-gradient(120deg,var(--purple),var(--pink)); -webkit-background-clip:text; color:transparent; }
.hero p { color:#655f78; font-size:1.08rem; margin:.25rem 0 0; }
.question-card { direction:rtl; text-align:center; color:white; border-radius:28px; padding:2.2rem 1.2rem;
 background:linear-gradient(135deg,#5b21b6,#8b5cf6 48%,#ec4899); box-shadow:0 18px 45px rgba(109,40,217,.28); margin:1rem 0; border:1px solid rgba(255,255,255,.25); }
.question-card small { opacity:.82; font-weight:700; }
.question-card h2 { font-size:clamp(1.55rem,5vw,2.25rem); margin:.65rem 0 0; line-height:1.55; }
.waiting { text-align:center; background:rgba(255,255,255,.82); backdrop-filter:blur(12px); border:1px solid #e9ddff; border-radius:26px; padding:2rem; box-shadow:0 14px 34px rgba(76,29,149,.10); }
.pill { display:inline-block; padding:.3rem .8rem; border-radius:99px; background:#ede9fe; color:#5b21b6; font-weight:800; }
.section-title { text-align:center; margin:1.5rem 0 .2rem; font-size:1.5rem; font-weight:900; }
.section-hint { text-align:center; color:#746b86; margin-bottom:1rem; }
.roster { display:flex; flex-wrap:wrap; gap:.55rem; justify-content:center; margin:1.1rem 0; }
.roster span { background:white; border:1px solid #eadfff; box-shadow:0 5px 14px rgba(91,33,182,.08); border-radius:99px; padding:.5rem .9rem; font-weight:800; }
.vote-note { text-align:center; padding:.8rem; border-radius:14px; background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; margin:.8rem 0; }
.result-row { background:white; border:1px solid #eee9f8; border-radius:14px; padding:.65rem .85rem; margin:.45rem 0; }
.result-bar { height:9px; background:linear-gradient(90deg,#ec4899,#7c3aed); border-radius:9px; margin-top:.4rem; }
.winner { text-align:center; border-radius:28px; padding:2rem 1rem; color:white; background:linear-gradient(135deg,#f59e0b,#ec4899,#7c3aed); }
.winner h1 { font-size:clamp(2.5rem,9vw,4.5rem); margin:.35rem; }
div[data-testid="stSidebar"] { direction:rtl; background:linear-gradient(180deg,#2e1065,#581c87); }
div[data-testid="stSidebar"] * { color:white; }
div[data-testid="stSidebar"] div[role="radiogroup"] label { background:rgba(255,255,255,.08); border-radius:12px; padding:.35rem .55rem; }
.stButton button { border-radius:14px; font-weight:800; min-height:48px; transition:all .18s ease; }
.stButton button:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(109,40,217,.18); }
div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:22px !important; }
@media(max-width:640px){.block-container{padding:1rem .8rem 4rem}.question-card{padding:1.5rem .9rem}}
</style>
<div class="hero"><h1>🏆 مين أكثر؟</h1><p>اختاروا الشخص اللي تشوفون إن السؤال ينطبق عليه</p></div>
""", unsafe_allow_html=True)

with st.expander("📜 طريقة اللعب"):
    st.markdown("""
1. كل لاعب يدخل باسمه وينتظر المضيفة تبدأ اللعبة.
2. لكل لاعب صوت واحد في كل سؤال، ولا يقدر يصوّت لنفسه.
3. النتائج تبقى مخفية أثناء التصويت حتى ما يتأثر أحد.
4. المضيفة تغلق التصويت، تكشف النتيجة، ثم تنتقل للسؤال التالي.
5. صاحب أعلى مجموع أصوات يتوّج في النهاية 👑
""")

with st.sidebar:
    st.header("👋 الدخول")
    role = st.radio("نوع الدخول", ["🎮 لاعب", "🎛️ مضيفة"], label_visibility="collapsed")
    admin = role == "🎛️ مضيفة"
    if admin and not st.session_state.get("host_ok"):
        pin = st.text_input("رمز المضيفة", type="password", placeholder="••••")
        if st.button("دخول لوحة التحكم", use_container_width=True):
            if pin == HOST_PIN:
                st.session_state.host_ok = True
                st.rerun()
            else:
                st.error("الرمز غير صحيح")
        st.caption("الرمز الافتراضي: 2468 — غيّريه بمتغير HOST_PIN قبل النشر.")
    admin_ok = admin and st.session_state.get("host_ok", False)


def render_results(question, reveal):
    details = vote_details(question)
    total_players = len(players())
    st.caption(f"وصل {len(details)} من {total_players} صوت")
    st.progress(min(len(details) / max(total_players, 1), 1.0))
    if not reveal:
        st.info("🔐 النتائج مخفية إلى أن تغلق المضيفة التصويت.")
        return
    rows = counts(question)
    if not rows:
        st.info("ما وصل أي تصويت حتى الآن.")
        return
    top = rows[0][1]
    for name, total in rows:
        width = max(8, round(total / top * 100))
        st.markdown(f'<div class="result-row"><b>{html.escape(name)}</b><span style="float:left">{total} صوت</span><div class="result-bar" style="width:{width}%"></div></div>', unsafe_allow_html=True)
    with st.expander("👀 كشف تفاصيل التصويت"):
        for voter, candidate in details:
            st.write(f"**{voter}** ← {candidate}")


def host_controls(game, roster):
    with st.sidebar:
        st.divider()
        st.header("🎛️ لوحة المضيفة")
        st.metric("اللاعبون", f"{len(roster)} / {MAX_PLAYERS}")
        if not game["game_started"]:
            if st.button("🚀 بدء اللعبة", type="primary", use_container_width=True, disabled=len(roster) < 2):
                set_settings(question_index=0, voting_open=1, game_started=1)
                st.rerun()
            if len(roster) < 2:
                st.caption("تحتاجون لاعبين على الأقل.")
        elif game["question_index"] < len(QUESTIONS):
            q = game["question_index"]
            st.caption(f"السؤال {q + 1} من {len(QUESTIONS)}")
            if game["voting_open"]:
                if st.button("🔒 إغلاق وكشف التصويت", type="primary", use_container_width=True):
                    set_settings(voting_open=0); st.rerun()
            else:
                if st.button("🔓 إعادة فتح التصويت", use_container_width=True):
                    set_settings(voting_open=1); st.rerun()
                if st.button("السؤال التالي ←", type="primary", use_container_width=True):
                    if q + 1 >= len(QUESTIONS):
                        set_settings(question_index=len(QUESTIONS), voting_open=0)
                    else:
                        set_settings(question_index=q + 1, voting_open=1)
                    st.rerun()
            if st.button("🏁 إنهاء وعرض النتيجة", use_container_width=True):
                set_settings(question_index=len(QUESTIONS), voting_open=0); st.rerun()
        st.divider()
        with st.expander(f"👥 اللاعبون ({len(roster)})"):
            for p in roster:
                c1, c2 = st.columns([4, 1])
                c1.write(p)
                if c2.button("✕", key=f"rm_{p}", help=f"حذف {p}"):
                    remove_player(p); st.rerun()
        with st.expander("⚠️ تصفير اللعبة"):
            confirm = st.checkbox("أفهم أنه سيتم حذف اللاعبين والأصوات")
            if st.button("تصفير نهائي", disabled=not confirm, use_container_width=True):
                reset_game(); st.session_state.pop("player_name", None); st.rerun()


def render_final():
    scores = counts()
    st.balloons()
    if not scores:
        st.info("انتهت اللعبة بدون أصوات.")
        return
    high = scores[0][1]
    winners = [name for name, score in scores if score == high]
    if len(winners) == 1:
        winner = html.escape(winners[0])
        st.markdown(f'<div class="winner"><div>👑 الفائز النهائي</div><h1>{winner}</h1><div>{high} صوت — مبروك! 🎉</div></div>', unsafe_allow_html=True)
        if st.button("🎁 كشف المفاجأة", use_container_width=True):
            st.session_state.prize = True
        if st.session_state.get("prize"):
            st.success(f"☕🥤 {winners[0]} فاز بكوبون من هاف مليون! 🥤☕")
    else:
        st.warning(f"👑 تعادل بين: {'، '.join(winners)} — {high} أصوات لكل شخص")
    st.subheader("📊 الترتيب النهائي")
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, score) in enumerate(scores):
        st.write(f"{medals[i] if i < 3 else f'{i+1}.'} **{name}** — {score} صوت")


@st.fragment(run_every="2s")
def live_game():
    game = settings()
    roster = players()
    if admin_ok:
        host_controls(game, roster)
    if admin and not admin_ok:
        st.info("أدخلي رمز المضيفة من القائمة الجانبية.")
        return
    if not game["game_started"]:
        if admin_ok:
            st.markdown(f'<div class="waiting"><h2>🎛️ غرفة الانتظار</h2><h1>{len(roster)} / {MAX_PLAYERS}</h1><p>بانتظار دخول اللاعبين…</p></div>', unsafe_allow_html=True)
            if roster:
                st.markdown(roster_html(roster), unsafe_allow_html=True)
            return
        current = st.session_state.get("player_name")
        if current and current in roster:
            st.markdown(f'<div class="waiting"><span class="pill">تم الانضمام ✓</span><h2>أهلًا {html.escape(current)}!</h2><p>بانتظار المضيفة تبدأ اللعبة… لا تقفل الصفحة 🤍</p></div>', unsafe_allow_html=True)
            if len(roster) > 1:
                st.markdown('<div class="section-title">الموجودون في الغرفة</div>', unsafe_allow_html=True)
                st.markdown(roster_html(roster), unsafe_allow_html=True)
            else:
                st.info("أنت أول لاعب 🎉 عندما يدخل أصدقاؤك ستظهر أسماؤهم هنا تلقائيًا.")
        else:
            st.subheader("انضم للعبة 🎮")
            with st.form("join", clear_on_submit=False):
                name = st.text_input("اسمك", placeholder="مثال: سارة", max_chars=30)
                submitted = st.form_submit_button("انضمام", type="primary", use_container_width=True)
            if submitted:
                ok, message = add_player(name)
                if ok:
                    st.session_state.player_name = " ".join(name.strip().split()); st.rerun()
                else:
                    st.error(message)
        return
    if game["question_index"] >= len(QUESTIONS):
        render_final(); return
    q = game["question_index"]
    st.markdown(f'<div class="question-card"><small>السؤال {q+1} من {len(QUESTIONS)}</small><h2>{QUESTIONS[q]}</h2></div>', unsafe_allow_html=True)
    if not admin_ok:
        name = st.session_state.get("player_name")
        if not name or name not in roster:
            st.info("اللعبة بدأت، لكن تقدر تنضم الآن وتلحق الجولة 🎉")
            with st.form(f"late_join_{q}"):
                late_name = st.text_input("اسمك", placeholder="اكتب اسمك هنا", max_chars=30)
                late_submit = st.form_submit_button("دخول اللعبة", type="primary", use_container_width=True)
            if late_submit:
                ok, message = add_player(late_name)
                if ok:
                    st.session_state.player_name = " ".join(late_name.strip().split())
                    st.toast("دخلت اللعبة!", icon="🎮")
                    st.rerun()
                else:
                    st.error(message)
            return
        already = any(voter == name for voter, _ in vote_details(q))
        if game["voting_open"] and not already:
            options = [p for p in roster if p != name]
            if not options:
                st.markdown('<div class="vote-note">👋 أنت اللاعب الوحيد حاليًا. يحتاج شخص آخر أن ينضم حتى يظهر لك خيار للتصويت.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="section-title">🎯 اختار مين ينطبق عليه السؤال</div><div class="section-hint">اضغط على الاسم لتثبيت صوتك — اسمك مستبعد تلقائيًا</div>', unsafe_allow_html=True)
                cols = st.columns(2 if len(options) > 1 else 1)
                for index, candidate in enumerate(options):
                    icon = ["😎", "🔥", "⭐", "🎭", "🚀", "💫"][sum(map(ord, candidate)) % 6]
                    with cols[index % len(cols)]:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align:center;font-size:2rem'>{icon}</div><div style='text-align:center;font-size:1.15rem;font-weight:900;margin:.2rem'>{html.escape(candidate)}</div>", unsafe_allow_html=True)
                            if st.button(f"اختيار {candidate}", key=f"pick_{q}_{candidate}", use_container_width=True, type="primary"):
                                if vote(q, name, candidate):
                                    st.toast(f"صوّت لـ {candidate}!", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("تم تسجيل صوتك مسبقًا.")
        elif already:
            st.success("✅ تم تسجيل تصويتك — انتظر البقية.")
        else:
            st.warning("🔒 التصويت مغلق.")
    render_results(q, reveal=not bool(game["voting_open"]))


live_game()
