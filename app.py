import streamlit as st
import random
from openai import OpenAI
from datetime import datetime
import time
import re

# ================= 0. 页面配置 =================
st.set_page_config(layout="wide", page_title="CoC7模组: 罗德岛的黄金梦魇 | 规则严谨版")

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
    /* 助手建议样式 */
    .helper-box {
        background-color: #e3f2fd; border: 1px solid #90caf9; padding: 10px; border-radius: 8px; margin-top: 10px; color: #0d47a1; font-size: 0.9em;
    }
    /* 规则书样式 */
    .coc-rules-intro {
        font-size: 0.95em; color: #333; background-color: #fff; padding: 20px; border-radius: 5px; 
        border: 1px solid #ddd; line-height: 1.6;
    }
    .coc-rules-intro h4 { color: #8b0000; border-bottom: 3px solid #8b0000; padding-bottom: 10px; margin-top: 0; font-size: 1.5em; text-align: center;}
    .coc-rules-intro h5 { color: #2b2b2b; background-color: #e9ecef; padding: 8px; margin-top: 20px; font-weight: bold; border-left: 5px solid #8b0000;}
    .coc-rules-intro ul { padding-left: 20px; }
    .coc-rules-intro table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .coc-rules-intro th, .coc-rules-intro td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .coc-rules-intro th { background-color: #f2f2f2; font-weight: bold; color: #8b0000; }
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

# 2. 职业定义 (扩展版)
JOBS_DATA = {
    # --- 🧠 学术 / 知识 / 研究类 ---
    "会计师": {"skills": ["会计", "法律", "图书馆使用", "聆听", "说服", "计算机使用", "侦查", "信用评级"], "formula": 1,
               "cr_range": (30, 70)},
    "人类学家": {"skills": ["人类学", "考古学", "外语(任意)", "历史", "图书馆使用", "生存", "聆听", "信用评级"],
                 "formula": 1, "cr_range": (20, 50)},
    "考古学家": {"skills": ["考古学", "历史", "鉴定", "图书馆使用", "机械维修", "导航", "科学(任意)", "信用评级"],
                 "formula": 1, "cr_range": (30, 60)},
    "建筑师": {
        "skills": ["艺术/手艺(绘图)", "计算机使用", "法律", "图书馆使用", "说服", "科学(物理)", "心理学", "信用评级"],
        "formula": 1, "cr_range": (30, 70)},
    "艺术家": {"skills": ["艺术/手艺(任意)", "历史", "心理学", "侦查", "艺术/手艺(另一项)", "魅惑", "聆听", "信用评级"],
               "formula": 5, "cr_range": (9, 50)},
    "图书管理员": {"skills": ["会计", "图书馆使用", "外语(任意)", "母语", "历史", "鉴定", "神秘学", "信用评级"],
                   "formula": 1, "cr_range": (9, 35)},
    "教授": {"skills": ["图书馆使用", "外语(任意)", "母语", "心理学", "科学(任意)", "历史", "考古学", "信用评级"],
             "formula": 1, "cr_range": (50, 90)},

    # --- 📰 调查 / 信息 / 社会活动类 ---
    "记者": {"skills": ["艺术/手艺(摄影)", "历史", "图书馆使用", "母语", "心理学", "说服", "魅惑", "信用评级"],
             "formula": 1, "cr_range": (9, 30)},
    "私家侦探": {"skills": ["艺术/手艺(摄影)", "乔装", "法律", "图书馆使用", "心理学", "侦查", "追踪", "信用评级"],
                 "formula": 4, "cr_range": (20, 50)},
    "律师": {"skills": ["会计", "法律", "图书馆使用", "说服", "心理学", "追踪", "历史", "信用评级"], "formula": 1,
             "cr_range": (30, 80)},
    "警探": {"skills": ["艺术/手艺(表演)", "火器", "法律", "聆听", "心理学", "侦查", "说服", "信用评级"], "formula": 4,
             "cr_range": (20, 50)},

    # --- 🧪 医疗 / 科学类 ---
    "医生": {"skills": ["急救", "医学", "心理学", "科学(生物学)", "外语(拉丁文)", "药剂学", "学术(任意)", "信用评级"],
             "formula": 1, "cr_range": (30, 80)},
    "心理学家": {"skills": ["会计", "图书馆使用", "聆听", "说服", "心理学", "精神分析", "科学(任意)", "信用评级"],
                 "formula": 1, "cr_range": (30, 80)},
    "科学家": {
        "skills": ["计算机使用", "电气维修", "图书馆使用", "母语", "科学(主攻)", "科学(副攻)", "侦查", "信用评级"],
        "formula": 1, "cr_range": (30, 70)},
    "护士": {"skills": ["急救", "聆听", "医学", "心理学", "科学(生物学)", "科学(化学)", "说服", "信用评级"],
             "formula": 1, "cr_range": (9, 30)},

    # --- 🛠️ 技术 / 工程 / 手工业 ---
    "工程师": {
        "skills": ["艺术/手艺(绘图)", "电气维修", "图书馆使用", "机械维修", "操作重型机械", "科学(物理)", "地质学",
                   "信用评级"], "formula": 1, "cr_range": (30, 60)},
    "机械师": {
        "skills": ["艺术/手艺(木工)", "攀爬", "驾驶(汽车)", "电气维修", "机械维修", "操作重型机械", "锁匠", "信用评级"],
        "formula": 3, "cr_range": (9, 30)},
    "电工": {
        "skills": ["艺术/手艺(技术)", "攀爬", "电气维修", "机械维修", "操作重型机械", "科学(物理)", "急救", "信用评级"],
        "formula": 3, "cr_range": (20, 40)},

    # --- 🚓 法律 / 军事 / 安全 ---
    "警察": {"skills": ["艺术/手艺(表演)", "火器", "急救", "法律", "心理学", "侦查", "驾驶(汽车)", "信用评级"],
             "formula": 4, "cr_range": (9, 30)},
    "士兵": {"skills": ["攀爬", "闪避", "格斗(斗殴)", "火器", "隐秘", "生存", "急救", "信用评级"], "formula": 2,
             "cr_range": (9, 30)},
    "联邦探员": {"skills": ["驾驶(汽车)", "火器", "法律", "说服", "隐秘", "侦查", "计算机使用", "信用评级"],
                 "formula": 4, "cr_range": (20, 40)},

    # --- 🗺️ 探险 / 户外 / 体力型 ---
    "探险家": {"skills": ["攀爬", "跳跃", "历史", "导航", "外语(任意)", "生存", "考古学", "信用评级"], "formula": 4,
               "cr_range": (50, 80)},
    "猎人": {"skills": ["攀爬", "火器", "聆听", "自然学", "导航", "隐秘", "生存", "信用评级"], "formula": 4,
             "cr_range": (20, 50)},
    "飞行员": {
        "skills": ["电气维修", "机械维修", "导航", "操作重型机械", "驾驶(飞行器)", "天文学", "物理学", "信用评级"],
        "formula": 3, "cr_range": (20, 70)},
    "水手": {"skills": ["电气维修", "格斗(斗殴)", "急救", "机械维修", "导航", "驾驶(船只)", "游泳", "信用评级"],
             "formula": 2, "cr_range": (20, 40)},

    # --- 💰 商业 / 犯罪 / 灰色地带 ---
    "商人": {"skills": ["会计", "计算机使用", "法律", "聆听", "说服", "心理学", "信用评级", "话术"], "formula": 1,
             "cr_range": (30, 90)},
    "罪犯": {"skills": ["格斗(任意)", "锁匠", "巧手", "隐秘", "侦查", "心理学", "估价", "信用评级"], "formula": 3,
             "cr_range": (5, 40)},
    "黑帮分子": {"skills": ["格斗(斗殴)", "火器", "驾驶(汽车)", "聆听", "心理学", "说服", "隐秘", "信用评级"],
                 "formula": 2, "cr_range": (9, 50)},
    "走私者": {"skills": ["火器", "聆听", "导航", "驾驶(船只或汽车)", "巧手", "隐秘", "侦查", "信用评级"], "formula": 4,
               "cr_range": (20, 60)},

    # --- 🎭 娱乐 / 非传统 ---
    "演员": {"skills": ["艺术/手艺(表演)", "乔装", "格斗(斗殴)", "历史", "心理学", "说服", "魅惑", "信用评级"],
             "formula": 5, "cr_range": (9, 40)},
    "作家": {"skills": ["艺术/手艺(写作)", "历史", "图书馆使用", "母语", "外语(任意)", "心理学", "自然学", "信用评级"],
             "formula": 1, "cr_range": (9, 30)},
    "神秘学家": {"skills": ["人类学", "艺术/手艺(任意)", "历史", "图书馆使用", "外语(任意)", "神秘学", "科学(天文学)",
                            "信用评级"], "formula": 6, "cr_range": (20, 60)},
    "宗教人士": {"skills": ["会计", "历史", "图书馆使用", "聆听", "外语(任意)", "说服", "心理学", "信用评级"],
                 "formula": 1, "cr_range": (9, 60)}
}


# ================= 2. 核心逻辑函数 =================

def calculate_osp(job_key, stats):
    """计算职业技能点 (OSP)"""
    formula = JOBS_DATA[job_key]["formula"]
    edu = stats.get("EDU", 50)
    dex = stats.get("DEX", 50)
    str_stat = stats.get("STR", 50)
    app = stats.get("APP", 50)
    pow_stat = stats.get("POW", 50)

    if formula == 1:
        return edu * 4
    elif formula == 2:
        return edu * 2 + str_stat * 2
    elif formula == 3:
        return edu * 2 + dex * 2
    elif formula == 4:
        return edu * 2 + max(dex, str_stat) * 2
    elif formula == 5:
        return edu * 2 + app * 2  # 艺术家/演员
    elif formula == 6:
        return edu * 2 + pow_stat * 2  # 神秘学家
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
    """AI 裁决：只判断是否需要检定，不生成剧情"""
    client = get_ai_client()
    if not client: return False, "", ""

    prompt = f"""
    【指令】你是 CoC 7e 的守密人。
    玩家声明了行动："{action_context}"。
    玩家当前技能列表：{list(player_skills.keys())}。

    【判断逻辑】
    1. 这个行动是否困难、有风险或对抗性？如果是，需要检定。
    2. 如果只是简单的观察、对话或日常行为，通常无需检定。
    3. 特殊规则：如果玩家尝试回忆或寻找隐藏物品，可能需要【侦查】或【图书馆使用】。

    【输出格式】
    如果需要检定，请严格输出：CHECK|技能名称|难度(常规/困难/极难)
    如果无需检定（自动成功或失败），请严格输出：NONE

    **绝对不要生成剧情故事，只输出判断代码。**
    """
    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
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
    """AI 叙事：根据行动和（可选的）检定结果生成剧情"""
    client = get_ai_client()
    if not client: return "系统提示：API未连接。"

    outcome_str = "自动成功"
    if check_info:
        outcome_str = f"技能【{check_info['skill']}】检定结果：{check_info['result_level']} (掷骰 {check_info['roll']}/目标 {check_info['target']})"

    # 获取角色特性
    traits = st.session_state.investigator.get('traits', '无') if st.session_state.investigator else '无'

    prompt = f"""
    【指令】你是《克苏鲁的呼唤》7版模组《罗德岛的黄金梦魇》的守密人(KP)。

    【玩家信息】
    玩家角色特性：{traits}
    (请在生成剧情时，根据该特性调整角色的行为描述、对话风格或心理活动。)

    【剧本背景】
    1921年12月，罗德岛。10年前“前进号”捕鲸船带回了被诅咒的金币（偷自克苏鲁祭坛）。
    船长德怀特变成了深潜者，躲在沙滩小屋。
    雕塑家麦凯恩是克苏鲁的傀儡，制造雕像想找回金币。
    玩家的叔叔史密斯（已故）曾是船员，刚死于雕像砸头意外，玩家来继承遗产。
    关键物品：史密斯遗物中残缺的金币（剩下1/3）、航海日志、老鼠啃食的日记。

    【上下文】{st.session_state.dm_text[-800:]}
    【玩家行动】{action_context}
    【判定结果】{outcome_str}

    【任务】
    请根据上述判定结果，描写接下来的剧情发展。
    - 严格遵循模组剧情，不要随意创造与模组无关的内容。
    - 如果是大成功/极难成功，给予更多奖励或细节（如发现金币上的不可名状符号、日记中的疯言疯语）。
    - 如果是失败/大失败，描述挫折或负面后果（如被老鼠群攻击、被警察怀疑）。

    【叙事风格 - 严格执行】
    1. **高效叙事（7:3比例）**：请将 **70%** 的篇幅用于陈述重点信息（事实、结果、直接反馈、NPC关键对话），仅用 **30%** 的篇幅进行环境氛围描写。
    2. 拒绝冗长：不要堆砌辞藻，直接告诉玩家发生了什么。
    3. 风格：冷峻、客观、充满悬疑感，但绝不拖沓。

    - 如果有重要线索（如：航海日志内容、金币、NPC证词），请在段落末尾以【线索：...】格式明确标注。
    - **严禁**在剧情末尾提供“推荐行动指南”或类似的下一步建议。只描述当前发生的事情和结果。
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


# --- 跑团助手 ---
def ai_get_help(current_context, investigator):
    """跑团助手：分析当前局势，给出建议"""
    client = get_ai_client()
    if not client: return "助手提示：请先配置API Key。"

    prompt = f"""
    【角色】你是一位经验丰富的《克苏鲁的呼唤》(CoC 7e) 跑团老手，正在指导一位新手玩家。
    【当前模组】《罗德岛的黄金梦魇》
    【当前剧情】{current_context[-1000:]}
    【玩家职业】{investigator['job']}
    【玩家技能】{list(investigator['skills'].keys())}

    【任务】
    玩家现在有点迷茫，不知道该做什么。请根据当前剧情，给出 3 条具体的行动建议。
    建议方向：
    1. 可以调查的地点或物品。
    2. 可以询问NPC的问题。
    3. 可以使用的技能（如侦查、聆听、心理学等）。

    【限制】
    - 不要剧透后续剧情！
    - 只提供思路，让玩家自己去执行。
    - 语气亲切、鼓励。
    - 使用 Markdown 列表格式输出。
    """
    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"助手掉线了: {e}"


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
if "rules_read" not in st.session_state: st.session_state.rules_read = False  # 新增：规则阅读状态

if "notebook" not in st.session_state: st.session_state.notebook = []
if "action_log" not in st.session_state: st.session_state.action_log = []
if "last_dice_result" not in st.session_state: st.session_state.last_dice_result = None
if "pending_check" not in st.session_state: st.session_state.pending_check = None


# ================= 5. 界面渲染 =================

# --- 新增功能：规则导读页 ---
def render_rules_guide():
    st.markdown("## 📜 CoC 7e 规则速览")
    st.markdown("在开始创建角色之前，请先了解一下《克苏鲁的呼唤》的核心规则。")

    st.markdown("""
    <div class='coc-rules-intro'>
    <h4>📖 CoC 7e 核心规则速查</h4>

    <h5>一、技能检定（Skill Check）</h5>
    <p>1️⃣ <b>基本流程</b><br>
    先确定目标（想干嘛）→ 确定难度等级 → 是否允许推骰（能否合理解释？先预告失败后果）→ 掷 D100 → 成功则可能勾技能</p>

    <p>2️⃣ <b>成功等级</b><br>
    <table>
    <tr><th>等级</th><th>判定标准</th></tr>
    <tr><td>大成功</td><td>01</td></tr>
    <tr><td>极限成功</td><td>≤ 技能/属性 × 1/5</td></tr>
    <tr><td>困难成功</td><td>≤ 技能/属性 × 1/2</td></tr>
    <tr><td>普通成功</td><td>≤ 技能/属性</td></tr>
    <tr><td>失败</td><td>> 技能</td></tr>
    <tr><td>大失败</td><td>100；或技能<50且掷96–100</td></tr>
    </table>
    ⚠️ 推骰失败 = 必须承受严重后果</p>

    <h5>二、对抗检定（Opposed Roll）</h5>
    <p>双方各自掷同意的技能/属性，比较成功等级高低。<br>
    <b>成功等级排序</b>：大成功 > 极限 > 困难 > 普通 > 失败<br>
    平手 → 技能/属性高者胜；仍平手 → 僵局或重骰<br>
    ❌ 不能推骰</p>

    <h5>三、奖励骰 / 惩罚骰（Bonus / Penalty Dice）</h5>
    <p>奖励骰：多掷一个十位骰，取<b>更低</b><br>
    惩罚骰：多掷一个十位骰，取<b>更高</b><br>
    多个可叠加（一般不超过 2）。本质：概率修正，而非直接加减数值。</p>

    <h5>四、联合技能检定</h5>
    <p>只掷一次骰，同时与多个技能对照。<br>
    Keeper 决定：是否需要<b>全部成功</b> 或 <b>任一成功即可</b></p>

    <h5>五、近身战斗（Melee）</h5>
    <p>1️⃣ <b>行动顺序</b>：按 DEX 高到低<br>
    2️⃣ <b>行动选择</b>：攻击 / 闪避 / 反击 / 战术动作 / 逃跑 / 施法<br>
    3️⃣ <b>对抗逻辑</b><br>
    - 反击：战斗技能 vs 战斗技能 → 成功等级高者造成伤害<br>
    - 闪避：战斗技能 vs 闪避 → 攻击方等级更高才命中<br>
    - 平手规则明确偏向防守方（除反击平手）<br>
    4️⃣ <b>极限成功伤害</b><br>
    - 穿刺武器：最大伤害 + 再掷伤害<br>
    - 非穿刺武器：最大伤害</p>

    <h5>六、战术动作（缴械 / 压制 / 推倒等）</h5>
    <p>比较 <b>体格（Build）</b><br>
    每差 1 点 → 攻击者 1 个惩罚骰<br>
    差 ≥3 → 战术不可行<br>
    成功 ≠ 伤害，而是 <b>实现战术目标</b></p>

    <h5>七、火器战斗（Firearms）</h5>
    <p>1️⃣ <b>核心原则</b>：不对抗，失败永不造成伤害，困难度由<b>射程决定</b><br>
    2️⃣ <b>射程 → 困难度</b><br>
    <table>
    <tr><th>射程</th><th>难度</th></tr>
    <tr><td>基本</td><td>普通</td></tr>
    <tr><td>2×</td><td>困难</td></tr>
    <tr><td>4×</td><td>极限</td></tr>
    </table>
    3️⃣ <b>常见修正</b><br>
    - 瞄准：奖励骰<br>
    - 近距离：奖励骰<br>
    - 目标闪避 / 掩护 / 快速移动：惩罚骰<br>
    - 近战射击：惩罚骰 + 失误可能误伤友军<br>
    4️⃣ <b>全自动 / 爆裂</b><br>
    技能 ÷10 = 每轮子弹数（最少3）。每轮单独掷骰，后续轮次逐渐增加惩罚骰。<br>
    极限成功 → 全中 + 部分贯穿</p>

    <h5>八、追逐规则（Chase）</h5>
    <p>1️⃣ <b>初始化</b>：决定追逐分组，进行<b>速度检定（CON 或 驾驶）</b><br>
    - 成功：MOV 不变<br>
    - 极限：MOV +1<br>
    - 失败：MOV -1<br>
    2️⃣ <b>行动</b>：普通移动 / 冲刺 / 攻击 / 协助。冲刺越猛 → 危害骰惩罚越多<br>
    3️⃣ <b>特殊情况</b><br>
    - 射击中：移动会吃惩罚骰<br>
    - 打轮胎：护甲3，仅穿刺可毁<br>
    - 司机重伤 → 立即危害检定</p>

    <h5>九、理智（SAN）与疯狂</h5>
    <p>1️⃣ <b>触发条件</b><br>
    - 单次失 SAN ≥5 → 临时疯狂<br>
    - 一天失 ≥1/5 SAN → 不定期疯狂<br>
    2️⃣ <b>疯狂类型</b><br>
    - 实时：1D10 回合<br>
    - 摘要：1D10 小时<br>
    - 可能获得：恐惧症 / 狂躁症 / 妄想<br>
    3️⃣ <b>恢复</b><br>
    - 临时疯狂：休息即可<br>
    - 不定期疯狂：月度治疗检定<br>
    - 私人治疗 > 机构治疗 成功率高</p>

    <h5>十、神话书与魔法</h5>
    <p>1️⃣ <b>阅读神话书</b>：越古老 → 难度越高。初读：SAN 损失 + 神话技能。全书学习：时间长，但收益完整。<br>
    2️⃣ <b>施法</b>：初次施法：困难 POW。可推骰（失败代价极高）。MP 可透支 HP。<br>
    3️⃣ <b>POW 成长</b>：赢得 POW 对抗 或 Luck 01。擲 1D100 > 当前 POW → POW +1D10（永久）</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("我已了解规则，开始创建角色", type="primary", use_container_width=True):
        st.session_state.rules_read = True
        st.rerun()


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

        # 角色特性
        traits_val = st.session_state.get("temp_traits", "")
        traits = st.text_area("✨ 角色特性 (性格、外貌、怪癖、背景)", value=traits_val,
                              placeholder="例如：性格急躁，右眼有伤疤，极度害怕老鼠，随身带着去世妻子的照片...",
                              height=100)

        st.info(f"职业特性：{', '.join(JOBS_DATA[job]['skills'])}")

        if st.button("下一步：属性投掷"):
            st.session_state.temp_name = name
            st.session_state.temp_job = job
            st.session_state.temp_traits = traits
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

                # 去重职业技能
                raw_job_skills = JOBS_DATA[current_job]["skills"] + ["信用评级"]
                job_specific_skills = []
                seen = set()
                for sk in raw_job_skills:
                    if sk not in seen:
                        job_specific_skills.append(sk)
                        seen.add(sk)

                # 补全基础技能表
                for skill_name in job_specific_skills:
                    if skill_name not in base_skills:
                        if "艺术" in skill_name or "手艺" in skill_name:
                            base_skills[skill_name] = 5
                        elif "格斗" in skill_name:
                            base_skills[skill_name] = 25
                        elif "科学" in skill_name:
                            base_skills[skill_name] = 1
                        elif "外语" in skill_name:
                            base_skills[skill_name] = 1
                        elif "火器" in skill_name:
                            base_skills[skill_name] = 20
                        else:
                            base_skills[skill_name] = 1

                base_skills["闪避"] = st.session_state.temp_stats["DEX"] // 2
                base_skills["母语"] = st.session_state.temp_stats["EDU"]

                # 初始值超过80的强制修正为80
                for k in base_skills:
                    if base_skills[k] > 80:
                        base_skills[k] = 80

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

        raw_js = JOBS_DATA[job_key]["skills"] + ["信用评级"]
        job_skills = []
        seen = set()
        for sk in raw_js:
            if sk not in seen:
                job_skills.append(sk)
                seen.add(sk)

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
            for sk in job_skills:
                if sk in st.session_state.base_skills_snapshot:
                    render_skill_input(sk, True)
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
        "traits": st.session_state.get("temp_traits", "无"),
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
    【指令】你是《克苏鲁的呼唤》7版模组《罗德岛的黄金梦魇》(The Golden Dream of Rhode Island) 的守密人(KP)。
    【当前场景】
    1. 时间：1921年12月20日。
    2. 地点：美国罗德岛州，普罗维登斯市中心，雷蒙德律师事务所 (Raymond Law Firm)。
    3. 环境：一间装修考究但略显压抑的办公室，窗外飘着冷雨。
    4. NPC：雷蒙德律师 (Lawyer Raymond)，政府指派的遗产管理人。态度热情但公事公办。
    5. 剧情背景：玩家的亲戚（叔叔）史密斯先生 (Mr. Smith) 于1个月前（11月20日）在家中遭遇意外（雕像砸头）身亡。

    【玩家角色】
    姓名：{st.session_state.temp_name}
    职业：{st.session_state.temp_job}
    【角色特性】：{st.session_state.get("temp_traits", "无")}
    (请在生成剧情时，根据该特性调整角色的行为描述、对话风格或心理活动。)

    【任务】
    请生成一段开场剧情。
    1. 描述调查员来到律所，见到了雷蒙德律师。
    2. 雷蒙德告知调查员，由于没有直系亲属，你是史密斯先生的唯一合法继承人。
    3. 遗产包括：罗德岛市中心的公寓、所有艺术品、以及银行账户里的1000美元。
    4. 结尾雷蒙德将带调查员前往史密斯的公寓整理遗物。

    【叙事风格 - 严格执行】
    1. **高效叙事（7:3比例）**：请将 **70%** 的篇幅用于陈述重点信息（事实、结果、直接反馈、NPC关键对话），仅用 **30%** 的篇幅进行环境氛围描写。
    2. 拒绝冗长：不要堆砌辞藻，直接告诉玩家发生了什么。
    3. 风格：冷峻、客观、充满悬疑感，但绝不拖沓。

    请注意：如果剧情中出现了重要的可调查信息，请在段落末尾添加【线索：...】标记。
    **严禁**在此次回复中生成“推荐行动指南”或类似的建议。只描述当前发生的事情和结果。
    """

    with st.spinner("守密人正在翻阅《罗德岛的黄金梦魇》剧本..."):
        raw_text = ai_narrate_outcome("游戏开始", None)
        st.session_state.dm_text = process_clues(raw_text)
        add_log("system", "模组开始：罗德岛的黄金梦魇", "导入完成")


def render_intro_page():
    st.markdown("## 📜 模组介绍：罗德岛的黄金梦魇")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class='intro-box'>
        <h3>背景故事</h3>
        <p>时间是1921年的冬天，地点位于美国罗德岛州（Rhode Island）。</p>
        <p>你收到了一封来自<b>雷蒙德律师事务所</b>的信件。信中称，你的一位远房亲戚——住在罗德岛中央大街附近的<b>史密斯先生</b>，于上个月不幸去世。</p>
        <p>史密斯先生年轻时曾是一艘捕鱼船的导航员，十年前突然退休，独自居住，据说发了一笔横财。如今他意外身亡，而你是他唯一的合法遗产继承人。</p>
        <p>为了处理后事并继承遗产，你踏上了前往罗德岛的旅程，却不知道一场源自十年前深海的梦魇正等待着你……</p>
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
        <div class='rule-box'>
        <b>3. 理智值 (SAN)</b><br>
        遭遇恐怖事物会扣除理智。SAN值归零意味着永久疯狂。请小心行事！
        </div>
        """, unsafe_allow_html=True)


def render_game_interface():
    st.sidebar.markdown("### 🕵️ 角色面板")
    inv = st.session_state.investigator
    st.sidebar.markdown(f"**{inv['name']}** ({inv['job']})")
    st.sidebar.caption(f"📝 特性：{inv.get('traits', '无')}")

    c1, c2, c3 = st.sidebar.columns(3)
    c1.metric("HP", f"{inv['derived']['HP']}/{inv['derived']['MAX_HP']}")
    c2.metric("SAN", f"{inv['derived']['SAN']}/{inv['derived']['MAX_SAN']}")
    c3.metric("MP", f"{inv['derived']['MP']}/{inv['derived']['MAX_MP']}")

    with st.sidebar.expander("技能列表"):
        sorted_skills = sorted(inv["skills"].items(), key=lambda x: x[1], reverse=True)
        for k, v in sorted_skills:
            if v > 10: st.markdown(f"{k}: **{v}%**")

    # --- 跑团助手 ---
    with st.sidebar.expander("🆘 跑团助手", expanded=False):
        # 1. 规则介绍 (置顶) - 完整版
        st.markdown("""
        <div class='coc-rules-intro'>
        <h4>📜 CoC 7e 核心规则速查 (进阶版)</h4>

        <h5>一、技能检定（Skill Check）</h5>
        <p>1️⃣ <b>基本流程</b><br>
        先确定目标（想干嘛）→ 确定难度等级 → 是否允许推骰（能否合理解释？先预告失败后果）→ 掷 D100 → 成功则可能勾技能</p>

        <p>2️⃣ <b>成功等级</b><br>
        <table>
        <tr><th>等级</th><th>判定标准</th></tr>
        <tr><td>大成功</td><td>01</td></tr>
        <tr><td>极限成功</td><td>≤ 技能/属性 × 1/5</td></tr>
        <tr><td>困难成功</td><td>≤ 技能/属性 × 1/2</td></tr>
        <tr><td>普通成功</td><td>≤ 技能/属性</td></tr>
        <tr><td>失败</td><td>> 技能</td></tr>
        <tr><td>大失败</td><td>100；或技能<50且掷96–100</td></tr>
        </table>
        ⚠️ 推骰失败 = 必须承受严重后果</p>

        <h5>二、对抗检定（Opposed Roll）</h5>
        <p>双方各自掷同意的技能/属性，比较成功等级高低。<br>
        <b>成功等级排序</b>：大成功 > 极限 > 困难 > 普通 > 失败<br>
        平手 → 技能/属性高者胜；仍平手 → 僵局或重骰<br>
        ❌ 不能推骰</p>

        <h5>三、奖励骰 / 惩罚骰（Bonus / Penalty Dice）</h5>
        <p>奖励骰：多掷一个十位骰，取<b>更低</b><br>
        惩罚骰：多掷一个十位骰，取<b>更高</b><br>
        多个可叠加（一般不超过 2）。本质：概率修正，而非直接加减数值。</p>

        <h5>四、联合技能检定</h5>
        <p>只掷一次骰，同时与多个技能对照。<br>
        Keeper 决定：是否需要<b>全部成功</b> 或 <b>任一成功即可</b></p>

        <h5>五、近身战斗（Melee）</h5>
        <p>1️⃣ <b>行动顺序</b>：按 DEX 高到低<br>
        2️⃣ <b>行动选择</b>：攻击 / 闪避 / 反击 / 战术动作 / 逃跑 / 施法<br>
        3️⃣ <b>对抗逻辑</b><br>
        - 反击：战斗技能 vs 战斗技能 → 成功等级高者造成伤害<br>
        - 闪避：战斗技能 vs 闪避 → 攻击方等级更高才命中<br>
        - 平手规则明确偏向防守方（除反击平手）<br>
        4️⃣ <b>极限成功伤害</b><br>
        - 穿刺武器：最大伤害 + 再掷伤害<br>
        - 非穿刺武器：最大伤害</p>

        <h5>六、战术动作（缴械 / 压制 / 推倒等）</h5>
        <p>比较 <b>体格（Build）</b><br>
        每差 1 点 → 攻击者 1 个惩罚骰<br>
        差 ≥3 → 战术不可行<br>
        成功 ≠ 伤害，而是 <b>实现战术目标</b></p>

        <h5>七、火器战斗（Firearms）</h5>
        <p>1️⃣ <b>核心原则</b>：不对抗，失败永不造成伤害，困难度由<b>射程决定</b><br>
        2️⃣ <b>射程 → 困难度</b><br>
        <table>
        <tr><th>射程</th><th>难度</th></tr>
        <tr><td>基本</td><td>普通</td></tr>
        <tr><td>2×</td><td>困难</td></tr>
        <tr><td>4×</td><td>极限</td></tr>
        </table>
        3️⃣ <b>常见修正</b><br>
        - 瞄准：奖励骰<br>
        - 近距离：奖励骰<br>
        - 目标闪避 / 掩护 / 快速移动：惩罚骰<br>
        - 近战射击：惩罚骰 + 失误可能误伤友军<br>
        4️⃣ <b>全自动 / 爆裂</b><br>
        技能 ÷10 = 每轮子弹数（最少3）。每轮单独掷骰，后续轮次逐渐增加惩罚骰。<br>
        极限成功 → 全中 + 部分贯穿</p>

        <h5>八、追逐规则（Chase）</h5>
        <p>1️⃣ <b>初始化</b>：决定追逐分组，进行<b>速度检定（CON 或 驾驶）</b><br>
        - 成功：MOV 不变<br>
        - 极限：MOV +1<br>
        - 失败：MOV -1<br>
        2️⃣ <b>行动</b>：普通移动 / 冲刺 / 攻击 / 协助。冲刺越猛 → 危害骰惩罚越多<br>
        3️⃣ <b>特殊情况</b><br>
        - 射击中：移动会吃惩罚骰<br>
        - 打轮胎：护甲3，仅穿刺可毁<br>
        - 司机重伤 → 立即危害检定</p>

        <h5>九、理智（SAN）与疯狂</h5>
        <p>1️⃣ <b>触发条件</b><br>
        - 单次失 SAN ≥5 → 临时疯狂<br>
        - 一天失 ≥1/5 SAN → 不定期疯狂<br>
        2️⃣ <b>疯狂类型</b><br>
        - 实时：1D10 回合<br>
        - 摘要：1D10 小时<br>
        - 可能获得：恐惧症 / 狂躁症 / 妄想<br>
        3️⃣ <b>恢复</b><br>
        - 临时疯狂：休息即可<br>
        - 不定期疯狂：月度治疗检定<br>
        - 私人治疗 > 机构治疗 成功率高</p>

        <h5>十、神话书与魔法</h5>
        <p>1️⃣ <b>阅读神话书</b>：越古老 → 难度越高。初读：SAN 损失 + 神话技能。全书学习：时间长，但收益完整。<br>
        2️⃣ <b>施法</b>：初次施法：困难 POW。可推骰（失败代价极高）。MP 可透支 HP。<br>
        3️⃣ <b>POW 成长</b>：赢得 POW 对抗 或 Luck 01。擲 1D100 > 当前 POW → POW +1D10（永久）</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.caption("不知道该做什么？助手可以提供一些思路。")
        if st.button("🤔 获取行动建议"):
            with st.spinner("助手正在分析局势..."):
                help_text = ai_get_help(st.session_state.dm_text, inv)
                st.session_state.helper_msg = help_text

        if "helper_msg" in st.session_state:
            st.markdown(f"<div class='helper-box'>{st.session_state.helper_msg}</div>", unsafe_allow_html=True)
    # --------------------------

    tab1, tab2, tab3 = st.tabs(["📖 剧情互动", "📝 行动记录", "📓 调查笔记本"])

    with tab1:
        st.info(st.session_state.dm_text)

        if st.session_state.get("last_dice_result"):
            res_data = st.session_state.last_dice_result
            st.markdown(
                f"<div class='{res_data['css']}'>🎲 {res_data['skill']} 检定：{res_data['val']} / {res_data['target']} → {res_data['level']}</div>",
                unsafe_allow_html=True)

        st.divider()

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
                    ph = st.empty()
                    for _ in range(10):
                        ph.markdown(f"<div class='dice-anim'>{random.randint(1, 100)}</div>", unsafe_allow_html=True)
                        time.sleep(0.05)

                    final_roll = random.randint(1, 100)
                    skill_val = inv['skills'].get(check['skill'], inv['stats'].get(check['skill'], 15))
                    if check['skill'] == '幸运': skill_val = inv['stats']['幸运']

                    level, css = check_coc7_success(final_roll, skill_val)
                    ph.markdown(f"<div class='dice-anim {css}'>{final_roll}</div>", unsafe_allow_html=True)

                    st.session_state.last_dice_result = {
                        "skill": check['skill'], "val": final_roll, "target": skill_val, "level": level, "css": css
                    }
                    add_log("dice", f"{check['skill']} 检定", f"{final_roll} ({level})")

                    with st.spinner("守密人正在判定后果..."):
                        check_info = {"skill": check['skill'], "roll": final_roll, "target": skill_val,
                                      "result_level": level}
                        narrative = ai_narrate_outcome(check['action'], check_info)
                        st.session_state.dm_text = process_clues(narrative)

                    st.session_state.pending_check = None
                    st.rerun()

            with col_skip:
                st.markdown("<div style='text-align:center; color:#666;'>⚠️ 命运无法逃避，你必须掷骰。</div>",
                            unsafe_allow_html=True)

        else:
            st.markdown("#### 🗣️ 采取行动")
            action = st.text_input("你的行动...", placeholder="例如：我向雷蒙德律师询问史密斯先生的死因")

            if st.button("执行行动", type="primary"):
                if action:
                    add_log("action", action)

                    with st.spinner("守密人正在判断是否需要检定..."):
                        need_roll, skill, diff = ai_judge_check(action, inv['skills'])

                        if need_roll:
                            st.session_state.pending_check = {
                                "action": action,
                                "skill": skill,
                                "difficulty": diff
                            }
                            st.rerun()
                        else:
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

    st.title("🕯️ CoC 7e: 罗德岛的黄金梦魇")

    # 逻辑流：没角色 -> 规则导读 -> 车卡; 有角色但没确认介绍 -> 介绍页; 否则 -> 游戏界面
    if not st.session_state.rules_read:
        render_rules_guide()
    elif not st.session_state.investigator:
        render_character_creation()
    elif not st.session_state.intro_acknowledged:
        render_intro_page()
    else:
        render_game_interface()


if __name__ == "__main__":
    main()
