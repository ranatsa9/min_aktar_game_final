import streamlit as st
import sqlite3
from pathlib import Path

# =========================================================
# DATABASE
# =========================================================

DB = Path("game.db")


def get_db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id=1),
            question_index INTEGER DEFAULT 0,
            voting_open INTEGER DEFAULT 0,
            game_started INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            question_index INTEGER,
            voter TEXT,
            candidate TEXT,
            PRIMARY KEY(question_index, voter)
        )
    """)

    if con.execute(
        "SELECT COUNT(*) FROM settings"
    ).fetchone()[0] == 0:

        con.execute("""
            INSERT INTO settings
            (id, question_index, voting_open, game_started)
            VALUES (1, 0, 0, 0)
        """)

    con.commit()
    con.close()


init_db()


# =========================================================
# QUESTIONS
# =========================================================

QUESTIONS = [
    "يتأخر عن المحاضرات؟",
    "دااايم يسأل أستاذة خلود؟",
    "ترشحه يكون مدرب؟",
    "يضحك في المحاضرات؟",
    'يختفي أول ما يقولون "بريك"؟',
    "يعرف يقنع التيم بأي شي؟",
    "يعتمد عليه التيم وقت الزنقة؟",
    "يخلص شغله بدري؟",
    "يساعد أعضاء التيم حتى لو خلص شغله؟",
    "إذا ما اشتغل، التيم كله يتعطل؟",
    "يبدأ يشتكي من الواجبات أول ما يشوفه؟",
    "يتمسك برأيه في المشروع؟",
    "إذا سألته المدربة خلود سؤال مفاجئ يعرف يتصرف؟",
    "ممكن يطلع بفكرة مشروع غير متوقعة؟",
    "يكون عنده أفكار أكثر من الوقت المتاح 😂؟",
    "يبدأ المشروع بحماس ثم يختفي 😂؟",
    "تتوقعون يفتح مشروعه الخاص بعد المعسكر؟",
    "تحسونه بيغير تخصصه بعد المعسكر؟",
    "كنت تحسبه رسمي، لكن طلع فلة؟",
    "كنت تحسبه عادي في الشغل، لكن اكتشفت أنه شاطر جدًا؟",
    "ما يدخل الكلاس بدون مشروب بيده؟",
    'يذكرك بشخصية "المدير" حتى بدون منصب؟',
]


# =========================================================
# SETTINGS
# =========================================================

def get_settings():
    con = get_db()

    row = con.execute(
        "SELECT * FROM settings WHERE id=1"
    ).fetchone()

    con.close()

    return row


def update_settings(**kwargs):
    con = get_db()

    for key, value in kwargs.items():
        con.execute(
            f"UPDATE settings SET {key}=? WHERE id=1",
            (value,)
        )

    con.commit()
    con.close()


# =========================================================
# PLAYERS
# =========================================================

def get_players():
    con = get_db()

    rows = con.execute("""
        SELECT name
        FROM players
        ORDER BY rowid
    """).fetchall()

    con.close()

    return [row["name"] for row in rows]


def add_player(name):

    name = name.strip()

    if not name:
        return False, "اكتبي اسمك أولًا."

    if len(name) > 30:
        return False, "الاسم طويل جدًا."

    players = get_players()

    # Prevent duplicate names
    for player in players:

        if player.lower() == name.lower():
            return False, "هذا الاسم مستخدم بالفعل."

    # Maximum 29 players
    if len(players) >= 29:
        return False, "اكتمل عدد اللاعبين (29)."

    try:

        con = get_db()

        con.execute(
            "INSERT INTO players(name) VALUES(?)",
            (name,)
        )

        con.commit()
        con.close()

        return True, "تم التسجيل!"

    except sqlite3.IntegrityError:

        return False, "هذا الاسم مستخدم بالفعل."


# =========================================================
# VOTES
# =========================================================

def has_voted(question_index, voter):

    con = get_db()

    result = con.execute("""
        SELECT 1
        FROM votes
        WHERE question_index=?
        AND voter=?
    """, (
        question_index,
        voter
    )).fetchone()

    con.close()

    return result is not None


def save_vote(question_index, voter, candidate):
    con = get_db()

    try:

        con.execute("""
            INSERT INTO votes
            (question_index, voter, candidate)
            VALUES (?, ?, ?)
        """, (
            question_index,
            voter,
            candidate
        ))

        con.commit()
        con.close()

        return True

    except sqlite3.IntegrityError:

        con.close()

        return False


def get_vote_details(question_index):

    con = get_db()

    rows = con.execute("""
        SELECT voter, candidate
        FROM votes
        WHERE question_index=?
        ORDER BY rowid DESC
    """, (
        question_index,
    )).fetchall()

    con.close()

    return [
        (row["voter"], row["candidate"])
        for row in rows
    ]


def get_vote_counts(question_index):

    con = get_db()

    rows = con.execute("""
        SELECT candidate, COUNT(*) AS total
        FROM votes
        WHERE question_index=?
        GROUP BY candidate
        ORDER BY total DESC
    """, (
        question_index,
    )).fetchall()

    con.close()

    return [
        (row["candidate"], row["total"])
        for row in rows
    ]


def get_total_scores():

    con = get_db()

    rows = con.execute("""
        SELECT candidate, COUNT(*) AS total
        FROM votes
        GROUP BY candidate
        ORDER BY total DESC
    """).fetchall()

    con.close()

    return [
        (row["candidate"], row["total"])
        for row in rows
    ]


# =========================================================
# RESET
# =========================================================

def reset_game():

    con = get_db()

    # Delete votes
    con.execute("DELETE FROM votes")

    # Delete players too
    con.execute("DELETE FROM players")

    # Reset game
    con.execute("""
        UPDATE settings
        SET question_index=0,
            voting_open=0,
            game_started=0
        WHERE id=1
    """)

    con.commit()
    con.close()

    # Clear current player session
    if "player_name" in st.session_state:
        del st.session_state["player_name"]


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="مين أكثر؟",
    page_icon="🏆",
    layout="centered"
)


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap');

:root {
    --night: #090812;
    --panel: #171522;
    --line: #393047;
    --violet: #a855f7;
    --pink: #f472b6;
    --cyan: #22d3ee;
}

html, body, [class*="st-"] { font-family: "Tajawal", sans-serif; }

/* Keep Streamlit's physical layout LTR so the sidebar stays on the left. */
.stApp {
    background:
        radial-gradient(circle at 88% 2%, rgba(244,114,182,.17), transparent 24rem),
        radial-gradient(circle at 5% 32%, rgba(34,211,238,.12), transparent 22rem),
        linear-gradient(145deg, #080710 0%, #100e19 52%, #171022 100%);
}

/* Arabic direction belongs to content—not the entire app shell. */
[data-testid="stMain"] .block-container {
    direction: rtl;
    max-width: 880px;
    padding-top: 4.25rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    direction: rtl;
    background: linear-gradient(180deg, #11101a, #21152f);
    border-right: 1px solid var(--line);
}

/* Reliable open/close controls that do not depend on Material icon fonts. */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] {
    display: block !important;
    z-index: 1000000 !important;
}

[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
    width: 42px !important;
    height: 42px !important;
    min-height: 42px !important;
    border-radius: 12px !important;
    background: #211a2f !important;
    border: 1px solid #514263 !important;
    color: transparent !important;
    position: relative;
}

[data-testid="stSidebarCollapseButton"] button span,
[data-testid="stSidebarCollapsedControl"] button span {
    display: none !important;
}

[data-testid="stSidebarCollapseButton"] button::after {
    content: "×";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: white;
    font: 800 1.65rem/1 Arial, sans-serif;
}

[data-testid="stSidebarCollapsedControl"] button::after {
    content: "☰";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: white;
    font: 800 1.25rem/1 Arial, sans-serif;
}

/* Keep Arabic letters and controls comfortably away from sidebar borders. */
[data-testid="stSidebarContent"] {
    padding: 4.4rem 1.25rem 2rem !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: .85rem;
}

.main-title {
    font-size: clamp(2.7rem, 8vw, 4.4rem);
    line-height: 1.15;
    font-weight: 900;
    text-align: center;
    padding-top: .6rem;
    background: linear-gradient(100deg, var(--cyan), #c084fc 48%, var(--pink));
    -webkit-background-clip: text;
    color: transparent;
    filter: drop-shadow(0 8px 22px rgba(168,85,247,.25));
}

.subtitle {
    text-align: center;
    color: #c9bfd7;
    font-size: 1.12rem;
    margin: .45rem 0 1.25rem;
}

.question {
    font-size: clamp(1.6rem, 5vw, 2.25rem);
    line-height: 1.55;
    font-weight: 900;
    text-align: center;
    color: white;
    padding: 2rem 1.2rem;
    margin: .8rem 0 1.25rem;
    border: 1px solid rgba(255,255,255,.13);
    border-radius: 26px;
    background: linear-gradient(135deg, #5424a5, #853cba 48%, #c33881);
    box-shadow: 0 18px 40px rgba(91,33,182,.24);
}

.waiting {
    text-align: center;
    padding: 2rem;
    border-radius: 24px;
    border: 1px solid var(--line);
    background: rgba(23,21,34,.84);
    box-shadow: 0 14px 34px rgba(0,0,0,.22);
}

[data-testid="stExpander"] {
    direction: rtl;
    background: rgba(23,21,34,.72);
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
}

.rules-drawer {
    direction: rtl;
    margin: .8rem 0 1.5rem;
    border: 1px solid var(--line);
    border-radius: 16px;
    background: rgba(23,21,34,.78);
    overflow: hidden;
}

.rules-drawer summary {
    position: relative;
    cursor: pointer;
    list-style: none;
    padding: 1rem 1.15rem 1rem 3.25rem;
    font-weight: 800;
    user-select: none;
}

.rules-drawer summary::-webkit-details-marker { display: none; }
.rules-drawer summary::after {
    content: "+";
    position: absolute;
    left: 1.1rem;
    top: 50%;
    transform: translateY(-50%);
    width: 1.75rem;
    height: 1.75rem;
    display: grid;
    place-items: center;
    border-radius: 9px;
    color: #e9d5ff;
    background: #33264a;
    font: 800 1.2rem/1 Arial, sans-serif;
}

.rules-drawer[open] summary::after { content: "−"; }
.rules-content {
    border-top: 1px solid var(--line);
    padding: 1rem 1.35rem 1.25rem;
}
.rules-content h3 { margin: 0 0 .8rem; }
.rules-content ol { margin: 0; padding: 0 1.8rem 0 0; }
.rules-content li { padding: .22rem .35rem .22rem 0; line-height: 1.65; }

[data-testid="stForm"] {
    background: rgba(23,21,34,.82);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1rem;
}

.stButton button, [data-testid="stFormSubmitButton"] button {
    min-height: 48px;
    border-radius: 13px;
    border: 1px solid rgba(255,255,255,.12);
    font-weight: 800;
    background: linear-gradient(100deg, #6d28d9, #a83fa6, #db2777);
    color: white;
}

.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    border-color: var(--cyan);
    box-shadow: 0 8px 24px rgba(168,85,247,.28);
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
    background: #1c1926 !important;
    border-color: #4a4059 !important;
}

@media (max-width: 640px) {
    [data-testid="stMain"] .block-container {
        width: 100%;
        padding: 4rem .85rem 3rem;
    }
    [data-testid="stSidebar"] { width: min(88vw, 320px) !important; }
    [data-testid="stSidebarContent"] { padding: 4.5rem 1rem 2rem !important; }
    .main-title { font-size: 2.35rem; padding-top: .35rem; }
    .subtitle { font-size: .98rem; line-height: 1.7; padding-inline: .4rem; }
    .question { font-size: 1.45rem; padding: 1.4rem .85rem; border-radius: 20px; }
    .waiting { padding: 1.35rem .8rem; border-radius: 19px; }
    .rules-drawer summary { padding: .9rem .9rem .9rem 3rem; }
    .rules-content { padding: .9rem .8rem 1rem; }
    .rules-content ol { padding-right: 1.55rem; }
    .rules-content li { padding-right: .2rem; font-size: .94rem; }
    .stButton button, [data-testid="stFormSubmitButton"] button { min-height: 52px; width: 100%; }
    input, textarea, select { font-size: 16px !important; }
    [data-testid="column"] { min-width: 0 !important; }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🏆 مين أكثر...</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'اختاروا الشخص اللي تشوفون أن السؤال ينطبق عليه 👇'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# RULES
# =========================================================

st.markdown("""
<details class="rules-drawer">
  <summary>📜 قوانين اللعبة</summary>
  <div class="rules-content">
    <h3>🎮 كيف نلعب؟</h3>
    <ol>
      <li>👤 كل لاعب يكتب اسمه وينضم للعبة.</li>
      <li>⏳ ننتظر حتى تكتمل المجموعة.</li>
      <li>🚀 المضيفة هي اللي تبدأ اللعبة.</li>
      <li>🗳️ لكل لاعب تصويت واحد فقط في كل سؤال.</li>
      <li>🙋 تقدر تصوّت لأي شخص، حتى لنفسك.</li>
      <li>🔒 بعد إرسال التصويت ما تقدر تغيره.</li>
      <li>👀 التصويت يظهر للجميع مباشرة.</li>
      <li>🏆 أكثر شخص يحصل على الأصوات في كل سؤال يفوز بالجولة.</li>
      <li>📊 في النهاية يتم جمع أصوات جميع الأسئلة.</li>
      <li>👑 أكثر شخص جمع أصوات هو الفائز النهائي.</li>
      <li>🎁 الفائز النهائي له مفاجأة خاصة 😉</li>
    </ol>
  </div>
</details>
""", unsafe_allow_html=True)


st.divider()


# =========================================================
# ROLE
# =========================================================

with st.sidebar:

    st.header("👋 الدخول")

    role = st.radio(
        "اختاري نوع الدخول:",
        [
            "🎮 لاعب",
            "🎛️ مضيفة"
        ]
    )

    admin = role == "🎛️ مضيفة"


# =========================================================
# CURRENT GAME STATE
# =========================================================

game = get_settings()

question_index = game["question_index"]

game_started = bool(
    game["game_started"]
)

voting_open = bool(
    game["voting_open"]
)

players = get_players()


# =========================================================
# HOST PANEL
# =========================================================

if admin:

    st.sidebar.divider()

    st.sidebar.header(
        "🎛️ لوحة المضيفة"
    )

    # Player count
    st.sidebar.metric(
        "👥 اللاعبين",
        f"{len(players)} / 29"
    )

    st.sidebar.divider()


    # START GAME
    if not game_started:

        st.sidebar.success(
            "⏳ اللعبة في وضع الانتظار"
        )

        if len(players) > 0:

            if st.sidebar.button(
                "🚀 بدء اللعبة",
                use_container_width=True
            ):

                update_settings(
                    question_index=0,
                    voting_open=1,
                    game_started=1
                )

                st.rerun()

        else:

            st.sidebar.warning(
                "بانتظار دخول اللاعبين..."
            )


    # GAME STARTED
    else:

        st.sidebar.write(
            f"السؤال: "
            f"**{question_index + 1} / {len(QUESTIONS)}**"
        )

        st.sidebar.write(
            f"الأصوات: "
            f"**{len(get_vote_details(question_index))}**"
        )


        # Open voting
        if st.sidebar.button(
            "🔓 فتح التصويت",
            use_container_width=True
        ):

            update_settings(
                voting_open=1
            )

            st.rerun()


        # Close voting
        if st.sidebar.button(
            "🔒 إغلاق التصويت",
            use_container_width=True
        ):

            update_settings(
                voting_open=0
            )

            st.rerun()


        # Next question
        if st.sidebar.button(
            "➡️ السؤال التالي",
            use_container_width=True,
            disabled=(
                question_index >= len(QUESTIONS) - 1
            )
        ):

            update_settings(
                question_index=question_index + 1,
                voting_open=1
            )

            st.rerun()


        # Finish
        if st.sidebar.button(
            "🏁 إنهاء اللعبة",
            use_container_width=True
        ):

            update_settings(
                question_index=len(QUESTIONS),
                voting_open=0,
                game_started=1
            )

            st.rerun()


    # =====================================================
    # PLAYERS LIST
    # =====================================================

    st.sidebar.divider()

    st.sidebar.subheader(
        "👥 اللاعبين المنضمين"
    )

    if players:

        for i, player in enumerate(
            players,
            1
        ):

            st.sidebar.write(
                f"{i}. {player}"
            )

    else:

        st.sidebar.info(
            "ما فيه لاعبين حتى الآن."
        )


    # =====================================================
    # RESET
    # =====================================================

    st.sidebar.divider()

    if st.sidebar.button(
        "⚠️ تصفير اللعبة بالكامل",
        use_container_width=True
    ):

        reset_game()

        st.rerun()


# =========================================================
# WAITING ROOM
# =========================================================

if not game_started:

    # -----------------------------------------------------
    # PLAYER LOGIN
    # -----------------------------------------------------

    if not admin:

        # Already joined
        if "player_name" in st.session_state:

            name = st.session_state["player_name"]

            st.success(
                f"🎮 أهلًا **{name}**!"
            )

            st.markdown(
                """
<div class="waiting">

<h2>⏳ بانتظار المضيفة تبدأ اللعبة...</h2>

<p>
لا تطلعين من الصفحة ❤️
</p>

</div>
""",
                unsafe_allow_html=True
            )


        # New player
        else:

            st.markdown(
                "## 👋 أهلًا في مين أكثر!"
            )

            st.write(
                "اكتبي اسمك للانضمام للعبة 🎮"
            )


            player_name = st.text_input(
                "👤 اسمك",
                placeholder="مثال: سارة"
            )


            if st.button(
                "🎮 انضمام للعبة",
                use_container_width=True
            ):

                success, message = add_player(
                    player_name
                )


                if success:

                    st.session_state[
                        "player_name"
                    ] = player_name.strip()

                    st.success(
                        "🎉 تم تسجيلك!"
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ {message}"
                    )


    # -----------------------------------------------------
    # HOST WAITING ROOM
    # -----------------------------------------------------

    else:

        st.markdown(
            "## 🎛️ غرفة الانتظار"
        )

        st.markdown(
            f"""
<div class="waiting">

<h2>👥 اللاعبين المنضمين</h2>

<h1>{len(players)} / 29</h1>

<p>
بانتظار دخول اللاعبين...
</p>

</div>
""",
            unsafe_allow_html=True
        )

        if len(players) > 0:

            st.success(
                f"🎉 دخل {len(players)} لاعب!"
            )

        else:

            st.info(
                "⏳ بانتظار أول لاعب..."
            )

    st.stop()


# =========================================================
# FINAL SCREEN
# =========================================================

if question_index >= len(QUESTIONS):

    st.success(
        "🎉 خلصت اللعبة!"
    )

    scores = get_total_scores()


    if scores:

        top_score = scores[0][1]

        winners = [
            name
            for name, total in scores
            if total == top_score
        ]


        # SINGLE WINNER
        if len(winners) == 1:

            winner = winners[0]

            st.balloons()

            st.markdown(
                "## 👑 الفائز النهائي هو..."
            )

            st.markdown(
                f"""
<div style="
text-align:center;
font-size:3rem;
font-weight:900;
padding:1rem;
">
{winner}
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
<div style="
text-align:center;
font-size:1.4rem;
">
حصل على <b>{top_score}</b>
تصويت من جميع الأسئلة 🎉
</div>
""",
                unsafe_allow_html=True
            )


            st.divider()

            st.markdown(
                "### 🎁 فيه مفاجأة للفائز..."
            )


            if "prize_revealed" not in st.session_state:

                st.session_state[
                    "prize_revealed"
                ] = False


            if not st.session_state[
                "prize_revealed"
            ]:

                if st.button(
                    "🎁 كشف المفاجأة",
                    use_container_width=True
                ):

                    st.session_state[
                        "prize_revealed"
                    ] = True

                    st.rerun()


            else:

                st.balloons()

                st.markdown(
                    f"""
<div style="
text-align:center;
padding:2rem;
">

<div style="
font-size:2rem;
font-weight:900;
">
🎉🎉🎉 مبرووووك! 🎉🎉🎉
</div>

<br>

<div style="
font-size:1.4rem;
">

مو بس فزت بلقب
<b>مين أكثر...</b>

<br><br>

☕🥤
<b>فزت بكوبون من هاف مليون!</b>
🥤☕

<br><br>

👑 <b>{winner}</b> 👑

</div>

</div>
""",
                    unsafe_allow_html=True
                )

                st.balloons()


        # TIE
        else:

            st.markdown(
                "## 👑 تعادل!"
            )

            st.markdown(
                f"""
### {'، '.join(winners)}

**{top_score} صوت**
"""
            )

            st.warning(
                "فيه تعادل! نحتاج سؤال كسر تعادل."
            )


        # LEADERBOARD
        st.divider()

        st.subheader(
            "📊 الترتيب النهائي"
        )

        medals = [
            "🥇",
            "🥈",
            "🥉"
        ]

        for i, (name, total) in enumerate(
            scores,
            1
        ):

            medal = (
                medals[i - 1]
                if i <= 3
                else f"{i}."
            )

            st.write(
                f"{medal} **{name}** — {total} صوت"
            )


    else:

        st.info(
            "ما فيه أصوات."
        )

    st.stop()


# =========================================================
# PLAYER GAME
# =========================================================

if not admin:

    name = st.session_state.get(
        "player_name"
    )


    if not name:

        st.error(
            "لازم تسجلين دخولك أولًا."
        )

        st.stop()


    st.success(
        f"🎮 أهلًا **{name}**!"
    )


    # =====================================================
    # QUESTION
    # =====================================================

    st.markdown(
        f"""
<div style="
text-align:center;
font-size:1rem;
">
السؤال {question_index + 1}
من {len(QUESTIONS)}
</div>
""",
        unsafe_allow_html=True
    )


    st.markdown(
        f"""
<div class="question">
{QUESTIONS[question_index]}
</div>
""",
        unsafe_allow_html=True
    )


    # =====================================================
    # VOTING
    # =====================================================

    if voting_open:

        if has_voted(
            question_index,
            name
        ):

            st.success(
                "✅ تم تسجيل تصويتك!"
            )


        else:

            # Everyone appears in the list, including the current player.
            options = players


            if options:

                candidate = st.selectbox(
                    "🗳️ اختاري شخصًا واحدًا",
                    options
                )


                if st.button(
                    "🔥 تصويت",
                    use_container_width=True
                ):

                    success = save_vote(
                        question_index,
                        name,
                        candidate
                    )


                    if success:

                        st.success(
                            f"🎉 {name} → {candidate}"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "حدث خطأ في التصويت."
                        )


    else:

        st.warning(
            "🔒 التصويت مغلق."
        )


# =========================================================
# HOST GAME SCREEN
# =========================================================

else:

    st.info(
        "🎛️ أنتِ في وضع المضيفة."
    )


    st.markdown(
        f"""
<div class="question">
السؤال {question_index + 1}
<br>
{QUESTIONS[question_index]}
</div>
""",
        unsafe_allow_html=True
    )


# =========================================================
# LIVE VOTES
# =========================================================

st.divider()

st.subheader(
    "🔥 التصويت المباشر"
)


details = get_vote_details(
    question_index
)


if details:

    st.write(
        f"🗳️ **{len(details)} صوت**"
    )


    # -----------------------------------------------------
    # COUNTS
    # -----------------------------------------------------

    st.subheader(
        "📊 عدد الأصوات"
    )


    for candidate, total in get_vote_counts(
        question_index
    ):

        st.write(
            f"**{candidate}** — {total} صوت"
        )


    st.markdown("---")


    # -----------------------------------------------------
    # WHO VOTED FOR WHO
    # -----------------------------------------------------

    st.subheader(
        "👀 مين صوّت لمين؟"
    )


    for voter, candidate in details:

        st.write(
            f"**{voter}** → **{candidate}**"
        )


else:

    st.info(
        "بانتظار أول تصويت..."
    )


# =========================================================
# AUTO REFRESH
# =========================================================

try:

    @st.fragment(run_every="2s")
    def refresh_game():

        st.empty()


    refresh_game()

except Exception:

    pass
