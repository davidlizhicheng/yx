import streamlit as st
import random
from openai import OpenAI
from datetime import datetime
import time
import re

# ================= 0. 页面配置 =================
st.set_page_config(layout="wide", page_title="CoC7模组: 岭下暗影 | 规则严谨版")

# CSS 样式优化
st.markdown("""
<style>
    .stApp { background-color: #f5f5f0; color: #2b2b2b; }
    .stat-box {
        border: 1px solid #8b4513; padding: 10px; border-radius: 8px;
        background: #f8f4e9; text-align: center; margin-bottom: 5px;
    }
    .stat-label { font-size: 12px; color: #5a3e2b; font-weight: bold; }
    .stat-value { font-size: 18px; font-weight: bold; color: #8b0000; }
    .pool-box {
        padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; font-weight: bold;
    }
    .pool-ok { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .pool-warn { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .pool-err { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .skill-row { font-size: 0.9em; padding: 5px 0; border-bottom: 1px solid #eee; }
    .cap-warning { color: #dc3545; font-size: 0.8em; font-weight: bold; }
    .intro-box {
        background-color: #2b2b2b; color: #f0f0f0; padding: 20px; border-radius: 10px;
        margin-bottom: 20px; border-left: 5px solid #8b0000;
    }
    .rule-box {
        background-color: #e9ecef; padding: 15px; border-radius: 5px;
        border: 1px solid #ced4da; margin-bottom: 10px;
    }
    .dice-anim {
        font-size: 40px; font-weight: bold; text-align: center; color: #8b0000;
        border: 2px dashed #8b0000; padding: 20px; border-radius: 10px; margin: 10px 0;
    }
    .dice-result-critical { background-color: #ffd700; color: #000; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    .dice-result-success { background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    .dice-result-fail { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    .dice-result-fumble { background-color: #343a40; color: #fff; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }

    .log-entry {
        border-bottom: 1px solid #ddd; padding: 10px 0; font-size: 0.95em;
    }
    .log-time { color: #666; font-size: 0.8em; }
    .clue-item {
        background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-bottom: 8px; border-radius: 4px;
    }
    .check-request-box {
        background-color: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 10px; text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# ================= 1. 数据常量 (CoC 7e 核心规则) =================

BASE_SKILLS = {
    "会计": 5, "人类学": 1, "估价": 5, "考古学": 1, "魅惑(Charm)": 15,
    "攀爬": 20, "计算机使用": 5, "信用评级": 0, "克苏鲁神话": 0,
    "乔装": 5, "闪避": 0, "驾驶(汽车)": 20, "电气维修": 10,
    "电子学": 1, "斗殴": 25, "射击(手枪)": 20, "急救": 30,
    "历史": 20, "恐吓": 15, "跳跃": 20, "外语(拉丁文)": 1,
    "母语": 0, "法律": 5, "图书馆使用": 20, "聆听": 20,
    "锁匠": 1, "机械维修": 10, "医学": 1, "博物学": 10,
    "领航": 10, "神秘学": 5, "操作重型机械": 1, "说服": 10,
    "驾驶(飞行器)": 1, "心理学": 10, "骑术": 5, "科学(生物学)": 1,
    "科学(化学)": 1, "妙手": 10, "侦查": 25, "潜行": 20,
    "生存": 10, "游泳": 20, "投掷": 25, "追踪": 10
}

JOBS_DATA = {
    "私家侦探": {
        "skills": ["艺术/手艺(摄影)", "乔装", "法律", "图书馆使用", "心理学", "侦查", "追踪", "话术", "射击(手枪)",
                   "斗殴"],
        "formula": 4,
        "cr_range": (20, 50)
    },
    "古董商": {
        "skills": ["会计", "估价", "历史", "图书馆使用", "领航", "外语(拉丁文)", "侦查", "魅惑"],
        "formula": 1,
        "cr_range": (30, 70)
    },
    "教授": {
        "skills": ["图书馆使用", "外语(拉丁文)", "母语", "心理学", "科学(生物学)", "历史", "考古学", "说服"],
        "formula": 1,
        "cr_range": (50, 90)
    },
    "医生": {
        "skills": ["急救", "医学", "心理学", "科学(生物学)", "外语(拉丁文)", "药剂学", "学术(任意)", "侦查"],
        "formula": 1,
        "cr_range": (30, 80)
    },
    "记者": {
        "skills": ["艺术/手艺(摄影)", "历史", "图书馆使用", "母语", "心理学", "说服", "魅惑", "潜行"],
        "formula": 1,
        "cr_range": (9, 30)
    }
}


# ================= 2. 核心逻辑函数 =================

def calculate_osp(job_key, stats):
    formula = JOBS_DATA[job_key]["formula"]
    edu = stats.get("EDU", 50)
    dex = stats.get("DEX", 50)
    str_stat = stats.get("STR", 50)

    if formula == 1:
        return edu * 4
    elif formula == 2:
        return edu * 2 + str_stat * 2
    elif formula == 3:
        return edu * 2 + dex * 2
    elif formula == 4:
        return edu * 2 + max(dex, str_stat) * 2
    return edu * 2


def roll_stat(stat_name):
    if stat_name in ["STR", "CON", "DEX", "APP", "POW", "幸运"]:
        return sum(random.randint(1, 6) for _ in range(3)) * 5
    elif stat_name in ["SIZ", "INT", "EDU"]:
        return (sum(random.randint(1, 6) for _ in range(2)) + 6) * 5
    return 0


def process_clues(text):
    clue_pattern = r"【线索：(.*?)】"
    found_clues = re.findall(clue_pattern, text)
    for clue in found_clues:
        if clue not in st.session_state.notebook:
            st.session_state.notebook.append({
                "time": datetime.now().strftime("%H:%M"),
                "content": clue
            })
    return text.replace("【线索：", "**【线索：").replace("】", "】**")


def add_log(action_type, content, result=None):
    st.session_state.action_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "type": action_type,
        "content": content,
        "result": result
    })


def check_coc7_success(roll_val, skill_val):
    if roll_val == 1: return "大成功", "dice-result-critical"
    if skill_val < 50 and roll_val >= 96: return "大失败", "dice-result-fumble"
    if skill_val >= 50 and roll_val == 100: return "大失败", "dice-result-fumble"
    if roll_val <= skill_val // 5: return "极难成功", "dice-result-critical"
    if roll_val <= skill_val // 2: return "困难成功", "dice-result-success"
    if roll_val <= skill_val: return "常规成功", "dice-result-success"
    return "失败", "dice-result-fail"


# ================= 3. AI 接口 =================
def get_ai_client():
    if "api_key" not in st.session_state or not st.session_state.api_key:
        return None
    return OpenAI(api_key=st.session_state.api_key, base_url=st.session_state.base_url)


def ai_judge_check(action_context, player_skills):
    """
    AI 裁决：只判断是否需要检定，不生成剧情
    返回：(NeedRoll: bool, Skill: str, Difficulty: str)
    """
    client = get_ai_client()
    if not client: return False, "", ""

    prompt = f"""
    【指令】你是 CoC 7e 的守密人。
    玩家声明了行动："{action_context}"。
    玩家当前技能列表：{list(player_skills.keys())}。

    【判断逻辑】
    1. 这个行动是否困难、有风险或对抗性？如果是，需要检定。
    2. 如果只是简单的观察、对话或日常行为，通常无需检定。

    【输出格式】
    如果需要检定，请严格输出：CHECK|技能名称|难度(常规/困难/极难)
    如果无需检定（自动成功或失败），请严格输出：NONE

    **绝对不要生成剧情故事，只输出判断代码。**
    """
    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # 低温以保证格式稳定
        )
        content = response.choices[0].message.content.strip()
        if "CHECK" in content:
            parts = content.split("|")
            if len(parts) >= 3:
                return True, parts[1], parts[2]
        return False, "", ""
    except:
        return False, "", ""


def ai_narrate_outcome(action_context, check_info=None):
    """
    AI 叙事：根据行动和（可选的）检定结果生成剧情
    """
    client = get_ai_client()
    if not client: return "系统提示：API未连接。"

    outcome_str = "自动成功"
    if check_info:
        outcome_str = f"技能【{check_info['skill']}】检定结果：{check_info['result_level']} (掷骰 {check_info['roll']}/目标 {check_info['target']})"

    prompt = f"""
    【指令】你是 CoC 7e 守密人。
    【上下文】{st.session_state.dm_text[-500:]}
    【玩家行动】{action_context}
    【判定结果】{outcome_str}

    【任务】
    请根据上述判定结果，描写接下来的剧情发展。
    - 如果是大成功/极难成功，给予更多奖励或细节。
    - 如果是失败/大失败，描述挫折或负面后果。
    - 风格：恐怖、悬疑、洛夫克拉夫特式。
    - 如果有线索，末尾附加【线索：...】。
    """
    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 错误: {e}"


# ================= 4. 初始化状态 =================
if "investigator" not in st.session_state: st.session_state.investigator = None
if "char_create_step" not in st.session_state: st.session_state.char_create_step = 1
if "temp_stats" not in st.session_state: st.session_state.temp_stats = {}
if "allocations" not in st.session_state: st.session_state.allocations = {}
if "dm_text" not in st.session_state: st.session_state.dm_text = "等待游戏开始..."
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "base_url" not in st.session_state: st.session_state.base_url = "https://api.deepseek.com"
if "model_name" not in st.session_state: st.session_state.model_name = "deepseek-chat"
if "intro_acknowledged" not in st.session_state: st.session_state.intro_acknowledged = False

if "notebook" not in st.session_state: st.session_state.notebook = []
if "action_log" not in st.session_state: st.session_state.action_log = []
if "last_dice_result" not in st.session_state: st.session_state.last_dice_result = None
if "pending_check" not in st.session_state: st.session_state.pending_check = None  # 新增：等待检定状态


# ================= 5. 界面渲染 =================

def render_character_creation():
    st.header("📝 调查员建卡")
    # --- 步骤 1 ---
    if st.session_state.char_create_step == 1:
        st.subheader("1. 身份信息")
        col1, col2 = st.columns(2)
        name_val = st.session_state.get("temp_name", "亚瑟·摩根")
        job_idx = 0
        if "temp_job" in st.session_state and st.session_state.temp_job in JOBS_DATA:
            job_idx = list(JOBS_DATA.keys()).index(st.session_state.temp_job)
        name = col1.text_input("调查员姓名", value=name_val)
        job = col2.selectbox("职业", list(JOBS_DATA.keys()), index=job_idx)
        st.info(f"职业特性：{', '.join(JOBS_DATA[job]['skills'])}")
        if st.button("下一步：属性投掷"):
            st.session_state.temp_name = name
            st.session_state.temp_job = job
            st.session_state.char_create_step = 2
            st.rerun()
    # --- 步骤 2 ---
    elif st.session_state.char_create_step == 2:
        st.subheader("2. 属性投掷 (3D6x5 / 2D6+6x5)")
        stats_list = ["STR", "CON", "SIZ", "DEX", "APP", "INT", "POW", "EDU", "幸运"]
        cols = st.columns(3)
        for i, stat in enumerate(stats_list):
            with cols[i % 3]:
                if stat in st.session_state.temp_stats:
                    st.markdown(
                        f"<div class='stat-box'><div class='stat-label'>{stat}</div><div class='stat-value'>{st.session_state.temp_stats[stat]}</div></div>",
                        unsafe_allow_html=True)
                else:
                    if st.button(f"投掷 {stat}"):
                        st.session_state.temp_stats[stat] = roll_stat(stat)
                        st.rerun()
        if len(st.session_state.temp_stats) == 9:
            st.divider()
            if st.button("下一步：技能加点"):
                st.session_state.allocations = {}
                base_skills = BASE_SKILLS.copy()
                current_job = st.session_state.temp_job
                job_specific_skills = JOBS_DATA[current_job]["skills"]
                for skill_name in job_specific_skills:
                    if skill_name not in base_skills:
                        if "艺术" in skill_name or "手艺" in skill_name:
                            base_skills[skill_name] = 5
                        else:
                            base_skills[skill_name] = 1
                base_skills["闪避"] = st.session_state.temp_stats["DEX"] // 2
                base_skills["母语"] = st.session_state.temp_stats["EDU"]
                st.session_state.base_skills_snapshot = base_skills
                for sk in base_skills.keys(): st.session_state.allocations[sk] = {'osp': 0, 'pip': 0}
                st.session_state.char_create_step = 3
                st.rerun()
    # --- 步骤 3 ---
    elif st.session_state.char_create_step == 3:
        st.subheader("3. 技能点分配")
        job_key = st.session_state.temp_job
        stats = st.session_state.temp_stats
        total_osp = calculate_osp(job_key, stats)
        total_pip = stats["INT"] * 2
        spent_osp = 0
        spent_pip = 0
        all_skills = list(st.session_state.base_skills_snapshot.keys())
        job_skills = JOBS_DATA[job_key]["skills"] + ["信用评级"]
        for sk in all_skills:
            if sk not in st.session_state.allocations: st.session_state.allocations[sk] = {'osp': 0, 'pip': 0}
            spent_osp += st.session_state.allocations[sk]['osp']
            spent_pip += st.session_state.allocations[sk]['pip']
        remain_osp = total_osp - spent_osp
        remain_pip = total_pip - spent_pip
        c1, c2 = st.columns(2)
        style_osp = "pool-ok" if remain_osp >= 0 else "pool-err"
        style_pip = "pool-ok" if remain_pip >= 0 else "pool-err"
        c1.markdown(f"<div class='pool-box {style_osp}'>职业点数 (OSP)<br>剩余: {remain_osp} / {total_osp}</div>",
                    unsafe_allow_html=True)
        c2.markdown(f"<div class='pool-box {style_pip}'>兴趣点数 (PIP)<br>剩余: {remain_pip} / {total_pip}</div>",
                    unsafe_allow_html=True)
        st.caption("⚠️ 规则：单项技能在建卡阶段上限为 **80%**。职业点数只能加在职业技能上。")

        def render_skill_input(skill_name, is_job_skill):
            if skill_name not in st.session_state.base_skills_snapshot: st.session_state.base_skills_snapshot[
                skill_name] = 1
            if skill_name not in st.session_state.allocations: st.session_state.allocations[skill_name] = {'osp': 0,
                                                                                                           'pip': 0}
            base_val = st.session_state.base_skills_snapshot[skill_name]
            alloc = st.session_state.allocations[skill_name]
            col_name, col_base, col_osp, col_pip, col_final = st.columns([2, 1, 2, 2, 1])
            with col_name:
                st.markdown(f"**{skill_name}**")
                if is_job_skill: st.caption("职业技能")
            with col_base:
                st.markdown(f"<span style='color:gray'>{base_val}%</span>", unsafe_allow_html=True)
            with col_osp:
                if is_job_skill:
                    new_osp = st.number_input(f"OSP: {skill_name}", min_value=0, max_value=999, value=alloc['osp'],
                                              key=f"osp_{skill_name}", label_visibility="collapsed")
                    if new_osp != alloc['osp']:
                        st.session_state.allocations[skill_name]['osp'] = new_osp
                        st.rerun()
                else:
                    st.markdown("<span style='color:#ccc'>--</span>", unsafe_allow_html=True)
            with col_pip:
                new_pip = st.number_input(f"PIP: {skill_name}", min_value=0, max_value=999, value=alloc['pip'],
                                          key=f"pip_{skill_name}", label_visibility="collapsed")
                if new_pip != alloc['pip']:
                    st.session_state.allocations[skill_name]['pip'] = new_pip
                    st.rerun()
            with col_final:
                final_val = base_val + st.session_state.allocations[skill_name]['osp'] + \
                            st.session_state.allocations[skill_name]['pip']
                color = "green" if final_val <= 80 else "red"
                st.markdown(f"<strong style='color:{color}'>{final_val}%</strong>", unsafe_allow_html=True)
                if final_val > 80: st.markdown("<div class='cap-warning'>超限!</div>", unsafe_allow_html=True)

        tab_job, tab_other = st.tabs(["💼 职业技能", "🌍 其他技能"])
        with tab_job:
            for sk in job_skills: render_skill_input(sk, True)
        with tab_other:
            other_skills = [sk for sk in all_skills if sk not in job_skills]
            for sk in other_skills: render_skill_input(sk, False)
        st.divider()
        can_finish = True
        err_msg = []
        if remain_osp < 0:
            can_finish = False
            err_msg.append("职业点数透支")
        if remain_pip < 0:
            can_finish = False
            err_msg.append("兴趣点数透支")
        for sk, alloc in st.session_state.allocations.items():
            final = st.session_state.base_skills_snapshot.get(sk, 0) + alloc['osp'] + alloc['pip']
            if final > 80:
                can_finish = False
                err_msg.append(f"{sk} > 80%")
                break
        if can_finish:
            if st.button("✅ 完成建卡", type="primary"):
                finalize_character()
                st.rerun()
        else:
            if err_msg: st.error(f"无法完成：{', '.join(err_msg)}")


def finalize_character():
    final_skills = {}
    for sk, alloc in st.session_state.allocations.items():
        val = st.session_state.base_skills_snapshot.get(sk, 0) + alloc['osp'] + alloc['pip']
        final_skills[sk] = val
    con = st.session_state.temp_stats["CON"]
    siz = st.session_state.temp_stats["SIZ"]
    pow_stat = st.session_state.temp_stats["POW"]
    hp = (con + siz) // 10
    san = pow_stat
    mp = pow_stat // 5
    st.session_state.investigator = {
        "name": st.session_state.temp_name,
        "job": st.session_state.temp_job,
        "stats": st.session_state.temp_stats,
        "derived": {
            "HP": hp, "MAX_HP": hp,
            "SAN": san, "MAX_SAN": san,
            "MP": mp, "MAX_MP": mp
        },
        "skills": final_skills,
        "inventory": ["调查员手册", "铅笔", "钱包", "打火机"]
    }
    intro_prompt = f"""
    【指令】你是《克苏鲁的呼唤》7版模组《岭下暗影》KP。
    【当前场景】罗德岛普罗维登斯，帕沃尔大街79号。1920年代。阴郁的殖民时代老宅。
    NPC：乔什·文斯考特，兴奋神经质，喝咖啡抽烟。
    【玩家】{st.session_state.temp_name} ({st.session_state.temp_job})
    【任务】生成开场剧情。描述环境压抑感和乔什的反常。结尾让乔什带玩家去地窖。
    """
    with st.spinner("守密人正在翻阅《岭下暗影》剧本..."):
        raw_text = ai_narrate_outcome("游戏开始")  # 使用通用叙事函数
        st.session_state.dm_text = process_clues(raw_text)
        add_log("system", "模组开始：岭下暗影", "导入完成")


def render_intro_page():
    st.markdown("## 📜 模组介绍：岭下暗影 (The Darkness Beneath the Hill)")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class='intro-box'>
        <h3>背景故事</h3>
        <p>时间是1920年代，地点位于美国罗德岛州的普罗维登斯（Providence）。</p>
        <p>你的老朋友（或亲戚）<b>乔什·文斯考特 (Josh Winscott)</b> 最近继承了一栋位于帕沃尔大街79号的古老殖民时代老宅。</p>
        <p>前几天，你收到了一封来自乔什的信。信中语焉不详，但他显得异常兴奋，声称他在修缮地窖时发现了一些<b>“惊人的历史秘密”</b>，并邀请你务必尽快来访。</p>
        <p>出于好奇，或者对这位老友精神状态的担忧，你来到了这栋被疯长灌木遮挡的阴郁老宅门前……</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 我已准备好，开始调查！", type="primary", use_container_width=True):
            st.session_state.intro_acknowledged = True
            st.rerun()
    with col2:
        st.markdown("### 🎲 CoC 7e 核心规则速查")
        st.markdown("""
        <div class='rule-box'>
        <b>1. 技能检定 (D100)</b><br>
        投掷 1D100。结果 <b>小于等于</b> 技能值即为成功。
        </div>
        <div class='rule-box'>
        <b>2. 成功等级</b><br>
        常规(≤技能) / 困难(≤1/2) / 极难(≤1/5) / 大成功(1) / 大失败(96-100)
        </div>
        """, unsafe_allow_html=True)


def render_game_interface():
    st.sidebar.markdown("### 🕵️ 角色面板")
    inv = st.session_state.investigator
    st.sidebar.markdown(f"**{inv['name']}** ({inv['job']})")

    c1, c2, c3 = st.sidebar.columns(3)
    c1.metric("HP", f"{inv['derived']['HP']}/{inv['derived']['MAX_HP']}")
    c2.metric("SAN", f"{inv['derived']['SAN']}/{inv['derived']['MAX_SAN']}")
    c3.metric("MP", f"{inv['derived']['MP']}/{inv['derived']['MAX_MP']}")

    with st.sidebar.expander("技能列表"):
        sorted_skills = sorted(inv["skills"].items(), key=lambda x: x[1], reverse=True)
        for k, v in sorted_skills:
            if v > 10: st.markdown(f"{k}: **{v}%**")

    tab1, tab2, tab3 = st.tabs(["📖 剧情互动", "📝 行动记录", "📓 调查笔记本"])

    with tab1:
        st.info(st.session_state.dm_text)

        # 显示投骰结果
        if st.session_state.get("last_dice_result"):
            res_data = st.session_state.last_dice_result
            st.markdown(
                f"<div class='{res_data['css']}'>🎲 {res_data['skill']} 检定：{res_data['val']} / {res_data['target']} → {res_data['level']}</div>",
                unsafe_allow_html=True)

        st.divider()

        # ================== 核心交互区：判定等待逻辑 ==================

        # 1. 检查是否存在等待中的判定
        if st.session_state.pending_check:
            check = st.session_state.pending_check
            st.markdown(f"""
            <div class='check-request-box'>
                <h3>🛑 守密人要求检定</h3>
                <p>你的行动：<b>{check['action']}</b></p>
                <p>需要进行：<b>{check['skill']}</b> 检定（难度：{check['difficulty']}）</p>
            </div>
            """, unsafe_allow_html=True)

            col_roll, col_skip = st.columns([1, 1])
            with col_roll:
                if st.button(f"🎲 投掷 {check['skill']}", type="primary", use_container_width=True):
                    # 动画
                    ph = st.empty()
                    for _ in range(10):
                        ph.markdown(f"<div class='dice-anim'>{random.randint(1, 100)}</div>", unsafe_allow_html=True)
                        time.sleep(0.05)

                    final_roll = random.randint(1, 100)
                    skill_val = inv['skills'].get(check['skill'], inv['stats'].get(check['skill'], 15))  # 兼容属性和技能
                    if check['skill'] == '幸运': skill_val = inv['stats']['幸运']

                    level, css = check_coc7_success(final_roll, skill_val)
                    ph.markdown(f"<div class='dice-anim {css}'>{final_roll}</div>", unsafe_allow_html=True)

                    # 记录结果并清除等待状态
                    st.session_state.last_dice_result = {
                        "skill": check['skill'], "val": final_roll, "target": skill_val, "level": level, "css": css
                    }
                    add_log("dice", f"{check['skill']} 检定", f"{final_roll} ({level})")

                    # 第二阶段：生成剧情
                    with st.spinner("守密人正在判定后果..."):
                        check_info = {"skill": check['skill'], "roll": final_roll, "target": skill_val,
                                      "result_level": level}
                        narrative = ai_narrate_outcome(check['action'], check_info)
                        st.session_state.dm_text = process_clues(narrative)

                    st.session_state.pending_check = None  # 清除锁
                    st.rerun()

            with col_skip:
                if st.button("放弃行动 (取消)", use_container_width=True):
                    st.session_state.pending_check = None
                    st.warning("你放弃了这次尝试。")
                    st.rerun()

        # 2. 正常行动输入 (当没有判定等待时显示)
        else:
            st.markdown("#### 🗣️ 采取行动")
            action = st.text_input("你的行动...", placeholder="例如：我仔细观察那个奇怪的雕像")

            if st.button("执行行动", type="primary"):
                if action:
                    add_log("action", action)

                    # 第一阶段：AI 裁决 (是否需要检定)
                    with st.spinner("守密人正在判断是否需要检定..."):
                        need_roll, skill, diff = ai_judge_check(action, inv['skills'])

                        if need_roll:
                            # 进入判定等待状态，暂停叙事
                            st.session_state.pending_check = {
                                "action": action,
                                "skill": skill,
                                "difficulty": diff
                            }
                            st.rerun()
                        else:
                            # 无需检定，直接生成剧情
                            narrative = ai_narrate_outcome(action)
                            st.session_state.dm_text = process_clues(narrative)
                            st.rerun()

    with tab2:
        st.markdown("### 📝 行动日志")
        if st.session_state.action_log:
            for log in reversed(st.session_state.action_log):
                icon = "👤" if log['type'] == 'action' else "🎲" if log['type'] == 'dice' else "🤖"
                st.markdown(f"""
                <div class='log-entry'>
                    <span class='log-time'>[{log['time']}]</span> {icon} <b>{log['content']}</b><br>
                    {f"结果: {log['result']}" if log['result'] else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("暂无记录")

    with tab3:
        st.markdown("### 📓 调查笔记本")
        if st.session_state.notebook:
            for note in st.session_state.notebook:
                st.markdown(f"<div class='clue-item'><b>[{note['time']}]</b> {note['content']}</div>",
                            unsafe_allow_html=True)
        else:
            st.info("目前还没有发现任何线索...")


def main():
    st.sidebar.header("⚙️ 设置")
    st.session_state.api_key = st.sidebar.text_input("DeepSeek API Key", value=st.session_state.api_key,
                                                     type="password")
    st.session_state.base_url = st.sidebar.text_input("Base URL", value=st.session_state.base_url)

    st.title("🕯️ CoC 7e: 岭下暗影 (规则严谨版)")

    if not st.session_state.investigator:
        render_character_creation()
    elif not st.session_state.intro_acknowledged:
        render_intro_page()
    else:
        render_game_interface()


if __name__ == "__main__":
    main()