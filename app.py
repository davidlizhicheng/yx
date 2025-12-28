import streamlit as st
import random
from openai import OpenAI
from datetime import datetime
import time
import re
import json
import heapq

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

    /* 优化后的日志样式 */
    .log-entry {
        border-bottom: 1px solid #e0e0e0; padding: 12px; font-size: 0.95em;
        margin-bottom: 8px; background-color: #ffffff; border-radius: 6px;
        border-left: 5px solid #ccc; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .log-type-action { border-left-color: #007bff; } /* 蓝色-行动 */
    .log-type-dice { border-left-color: #dc3545; }   /* 红色-检定 */
    .log-type-system { border-left-color: #28a745; } /* 绿色-系统 */
    .log-type-madness { border-left-color: #6f42c1; background-color: #f3e5f5; } /* 紫色-疯狂 */
    .log-type-correction { border-left-color: #fd7e14; background-color: #fff3cd; } /* 橙色-修正 */

    .log-header { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.8em; color: #666; }
    .log-content { font-weight: bold; color: #333; margin-bottom: 4px; }
    .log-result { font-size: 0.9em; color: #555; background: #f8f9fa; padding: 2px 6px; border-radius: 4px; display: inline-block; }

    /* 记忆摘要样式 */
    .memory-summary {
        background-color: #f0f4f8; border-left: 3px solid #3c8dbc;
        padding: 6px 10px; margin-top: 8px; font-size: 0.85em; color: #444;
        font-family: "Courier New", monospace; border-radius: 0 4px 4px 0;
    }
    .memory-tags {
        font-size: 0.75em; color: #888; margin-top: 4px;
    }
    .memory-tag {
        background: #e1e1e1; padding: 2px 6px; border-radius: 10px; margin-right: 4px; display: inline-block;
    }

    /* 增强的线索样式 */
    .clue-item {
        background-color: #fff; border: 1px solid #ddd; padding: 12px; margin-bottom: 10px; border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .clue-header { display: flex; justify-content: space-between; margin-bottom: 6px; align-items: center;}
    .clue-meta { font-size: 0.8em; color: #666; }
    .clue-content { font-size: 1em; color: #222; line-height: 1.5; }

    .badge { padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; margin-right: 5px; color: #fff;}
    .badge-core { background-color: #d39e00; } /* 金色-核心 */
    .badge-side { background-color: #17a2b8; } /* 蓝色-支线 */
    .badge-mislead { background-color: #dc3545; } /* 红色-误导 */

    .badge-high { background-color: #28a745; } /* 绿色-高信 */
    .badge-mid { background-color: #ffc107; color: #333; } /* 黄色-中信 */
    .badge-low { background-color: #6c757d; } /* 灰色-低信 */

    .check-request-box {
        background-color: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 10px; text-align: center;
        margin: 20px 0;
    }

    /* 疯狂状态特效 */
    .madness-alert {
        background-color: #4a148c; color: white; padding: 10px; border-radius: 5px; 
        text-align: center; font-weight: bold; border: 2px solid #880e4f;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(136, 14, 79, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(136, 14, 79, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(136, 14, 79, 0); }
    }

    /* 状态栏样式 */
    .world-state-box {
        font-size: 0.85em; background: #e0e0e0; padding: 8px; border-radius: 4px; margin-bottom: 10px; border-left: 4px solid #555;
    }
    .mental-state-box {
        font-size: 0.85em; background: #e8eaf6; padding: 8px; border-radius: 4px; margin-bottom: 10px; border-left: 4px solid #3f51b5;
    }

    /* 剧情存档样式 */
    .history-box {
        background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 5px; padding: 15px; margin-bottom: 10px;
        max-height: 300px; overflow-y: auto;
    }
    .history-entry {
        margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #ccc;
    }
    .history-header { font-weight: bold; color: #8b0000; font-size: 0.9em; margin-bottom: 4px;}
    .history-content { font-size: 0.9em; color: #333; white-space: pre-wrap; }
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

# 疯狂症状库
MADNESS_TABLE = {
    "phobias": [
        "恐水症", "恐高症", "幽闭恐惧症", "黑暗恐惧症", "尸体恐惧症",
        "鲜血恐惧症", "老鼠恐惧症", "异类恐惧症(害怕奇怪形状)", "噪音恐惧症", "人群恐惧症"
    ],
    "manias": [
        "洗手癖(试图洗掉污秽)", "欺诈癖(无法说真话)", "暴食癖", "强迫性多疑",
        "收藏癖(收集无用之物)", "纵火癖", "自言自语", "书写狂(记录一切)", "偏执狂(认为被监视)"
    ],
    "sources": [
        "普通恐怖(尸体/惊吓)", "暴力(目睹酷刑/杀戮)", "宇宙真相(时空/维度)", "神话存在(不可名状怪物)"
    ]
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
    """旧的正则提取，保留用于视觉高亮，真正的数据更新移交给 parse_ai_state_update"""
    clue_pattern = r"【线索：(.*?)】"
    # 纯视觉高亮替换
    return text.replace("【线索：", "**【线索：").replace("】", "】**")


def save_plot_history(action, content):
    """将新的剧情保存到历史存档中"""
    if "plot_history" not in st.session_state:
        st.session_state.plot_history = []

    st.session_state.plot_history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "content": content
    })


def add_log(action_type, content, result=None, memory_summary=None, memory_tags=None):
    st.session_state.action_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "type": action_type,
        "content": content,
        "result": result,
        "memory_summary": memory_summary,
        "memory_tags": memory_tags
    })


def check_coc7_success(roll_val, skill_val):
    # 1. 大成功：01
    if roll_val == 1:
        return "大成功", "dice-result-critical"

    # 2. 大失败：100 (若技能>=50) 或 96-100 (若技能<50)
    if skill_val < 50 and roll_val >= 96:
        return "大失败", "dice-result-fumble"
    if skill_val >= 50 and roll_val == 100:
        return "大失败", "dice-result-fumble"

    # 3. 成功等级
    if roll_val <= skill_val // 5:
        return "极限成功", "dice-result-critical"
    if roll_val <= skill_val // 2:
        return "困难成功", "dice-result-success"
    if roll_val <= skill_val:
        return "普通成功", "dice-result-success"

    # 4. 失败
    return "失败", "dice-result-fail"


def roll_madness_symptom():
    """随机生成疯狂症状"""
    symptom_type = random.choice(["phobias", "manias"])
    return random.choice(MADNESS_TABLE[symptom_type])


# ================= 3. AI 接口 (Authoritative State + Memory Retrieval) =================
def get_ai_client():
    if "api_key" not in st.session_state or not st.session_state.api_key:
        return None
    return OpenAI(api_key=st.session_state.api_key, base_url=st.session_state.base_url)


def retrieve_relevant_memories(action_context, limit=8):
    """检索相关记忆：基于当前地点和行动关键词"""
    if "memory_archive" not in st.session_state or not st.session_state.memory_archive:
        return "（暂无历史记忆）"

    current_location = st.session_state.game_state['world']['location']

    # 简单的关键词提取（按空格分词）
    query_tokens = set(action_context.split())
    query_tokens.add(current_location)

    scored_memories = []

    for idx, mem in enumerate(st.session_state.memory_archive):
        score = 0
        # 标签匹配
        if "tags" in mem:
            for tag in mem["tags"]:
                # 如果标签包含当前地点，加分
                if current_location in tag:
                    score += 3
                # 如果标签包含动作中的关键词，加分
                for token in query_tokens:
                    if token in tag:
                        score += 2

        # 倒序加权（越近的记忆越可能相关）
        recency_bonus = idx / len(st.session_state.memory_archive)
        score += recency_bonus

        if score > 0.1:  # 只有相关性才加入
            heapq.heappush(scored_memories, (-score, idx, mem))

    # 取 Top K
    top_memories = []
    count = 0
    while scored_memories and count < limit:
        score, _, mem = heapq.heappop(scored_memories)
        summary = mem.get("summary", "无内容")
        time_str = mem.get("fields", {}).get("when", "未知时间")
        top_memories.append(f"[{time_str}] {summary}")
        count += 1

    return "\n".join(top_memories) if top_memories else "（未检索到高度相关的历史事件）"


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


def ai_get_help(context, inv):
    """
    新手助手：分析当前局势，给出建议
    """
    client = get_ai_client()
    if not client: return "⚠️ API 未连接，无法获取建议。"

    prompt = f"""
    【指令】你是《克苏鲁的呼唤》(CoC 7e) 的新手辅助助手。

    【当前剧情摘要】
    {context[-2000:]}

    【调查员状态】
    职业：{inv['job']}
    技能高值：{', '.join([k for k, v in inv['skills'].items() if v > 40])}
    HP: {inv['derived']['HP']} | SAN: {inv['derived']['SAN']}

    【任务】
    根据当前局势，为迷茫的玩家提供 3 个可行的行动建议。
    建议应当符合 CoC 的调查风格，或应对眼前的危机。
    请保持简短（每条建议不超过 30 字）。

    【格式】
    1. [行动建议1]
    2. [行动建议2]
    3. [行动建议3]
    """

    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"助手掉线了... ({e})"


def apply_state_updates(updates):
    """将 AI 返回的结构化更新应用到 session_state，包含 SAN/疯狂/线索/NPC 系统"""
    if not updates: return

    memory_data = None  # 用于回传给UI显示

    # 1. 更新调查员状态
    if "investigator" in updates:
        inv_update = updates["investigator"]
        inv = st.session_state.investigator
        gs = st.session_state.game_state

        # HP 更新
        if "hp_change" in inv_update and inv_update["hp_change"] != 0:
            inv['derived']['HP'] += inv_update["hp_change"]
            inv['derived']['HP'] = max(0, min(inv['derived']['HP'], inv['derived']['MAX_HP']))
            add_log("system", f"HP 变化: {inv_update['hp_change']}", f"当前 {inv['derived']['HP']}")

        # SAN 更新与疯狂检定
        if "san_change" in inv_update and inv_update["san_change"] < 0:
            loss = abs(inv_update["san_change"])
            inv['derived']['SAN'] += inv_update["san_change"]
            current_san = inv['derived']['SAN']

            # 更新当日累计损失
            gs['sanity_data']['daily_loss'] += loss

            add_log("system", f"理智损失: -{loss}", f"当前 SAN: {current_san}")

            # 永久疯狂检查
            if current_san <= 0:
                gs['sanity_data']['status'] = "permanent"
                inv['derived']['SAN'] = 0
                add_log("madness", "⚠️ 永久疯狂！", "调查员心智彻底崩溃，游戏结束。")

            # 临时疯狂检查：单次损失 >= 5
            elif loss >= 5 and gs['sanity_data']['status'] == "sane":
                int_val = inv['stats']['INT']
                roll = random.randint(1, 100)
                if roll <= int_val:
                    symptom = roll_madness_symptom()
                    gs['sanity_data']['status'] = "temporary"
                    gs['sanity_data']['symptom'] = symptom
                    add_log("madness", f"智力检定成功({roll}≤{int_val}) -> 💡理解了恐怖", f"陷入【临时疯狂】")
                    add_log("madness", f"获得症状: {symptom}", "持续 1d10 小时")
                else:
                    add_log("system", f"智力检定失败({roll}>{int_val}) -> 🧠 大脑自我保护", "未陷入疯狂")

            # 不定性疯狂检查：单日累计 >= 起始值/5
            elif gs['sanity_data']['daily_loss'] >= (gs['sanity_data']['start_of_day'] // 5) and gs['sanity_data'][
                'status'] in ["sane", "temporary"]:
                symptom = roll_madness_symptom()
                gs['sanity_data']['status'] = "indefinite"
                gs['sanity_data']['symptom'] = symptom
                add_log("madness", "⚠️ 单日丧失过多理智", "陷入【不定性疯狂】")
                add_log("madness", f"获得症状: {symptom}", "直到病情好转")

        # MP 更新
        if "mp_change" in inv_update and inv_update["mp_change"] != 0:
            inv['derived']['MP'] += inv_update["mp_change"]
            inv['derived']['MP'] = max(0, min(inv['derived']['MP'], inv['derived']['MAX_MP']))

    # 2. 更新权威游戏状态 (game_state)
    if "game_state" in updates:
        gs_update = updates["game_state"]
        current_gs = st.session_state.game_state

        # 更新世界信息
        if "world" in gs_update:
            for k, v in gs_update["world"].items():
                current_gs["world"][k] = v

        # 更新 NPC 状态 (支持嵌套更新)
        if "npcs" in gs_update:
            for npc_name, npc_data in gs_update["npcs"].items():
                if npc_name not in current_gs["npcs"]:
                    current_gs["npcs"][npc_name] = {}
                for k, v in npc_data.items():
                    current_gs["npcs"][npc_name][k] = v

        # 更新案件线索 (线索系统升级)
        if "new_clues" in gs_update:
            for clue in gs_update["new_clues"]:
                # 检查重复 (基于内容前10个字简单去重)
                is_duplicate = any(c['content'][:10] == clue['content'][:10] for c in st.session_state.notebook)

                if not is_duplicate:
                    # 补全默认字段，防止 AI 漏填
                    new_clue_entry = {
                        "time": current_gs["world"]["time"],
                        "content": clue.get('content', '未知内容'),
                        "type": clue.get('type', '支线'),
                        "source": clue.get('source', '未知来源'),
                        "reliability": clue.get('reliability', '中')
                    }
                    st.session_state.notebook.append(new_clue_entry)
                    add_log("system", f"发现新线索 [{new_clue_entry['type']}]", "已记录到笔记本")

        # 更新规则状态
        if "rules" in gs_update:
            for k, v in gs_update["rules"].items():
                current_gs["rules"][k] = v

    # 3. 存储记忆档案 (Memory Archive)
    if "memory" in updates and updates["memory"]:
        mem = updates["memory"]
        # 确保基本字段存在
        if "summary" in mem and mem["summary"]:
            new_entry = {
                "id": len(st.session_state.memory_archive) + 1,
                "summary": mem["summary"],
                "tags": mem.get("tags", []),
                "fields": mem.get("fields", {})
            }
            st.session_state.memory_archive.append(new_entry)
            memory_data = new_entry  # 返回给调用层以便UI展示

    return memory_data


def ai_narrate_outcome(action_context, check_info=None):
    """AI 叙事：根据行动和（可选的）检定结果生成剧情，并维护权威状态表 + 记忆档案 + 审查器"""
    client = get_ai_client()
    if not client: return "系统提示：API未连接。", None

    outcome_str = "自动成功"
    fumble_instruction = ""

    if check_info:
        outcome_str = f"技能【{check_info['skill']}】检定结果：{check_info['result_level']} (掷骰 {check_info['roll']}/目标 {check_info['target']})"
        if check_info['result_level'] == "大失败":
            fumble_instruction = "【特别指令】玩家遭遇了【大失败】。请务必在剧情中描述严重的负面后果（如：受伤、损坏物品、被敌人发现、陷入绝境等），这不仅仅是失败，而是灾难性的失误。"

    # 1. 序列化当前权威状态
    current_state_json = json.dumps({
        "investigator_derived": st.session_state.investigator['derived'],
        "world": st.session_state.game_state['world'],
        "rules": st.session_state.game_state['rules'],
        "sanity_data": st.session_state.game_state['sanity_data'],
        "npcs": st.session_state.game_state['npcs'],  # 注入 NPC 状态
        "known_clues_count": len(st.session_state.notebook)
    }, ensure_ascii=False)

    # 2. 检索相关记忆 (RAG)
    relevant_memories = retrieve_relevant_memories(action_context)

    # 2.1 构建完整的剧情历史上下文 (Context Window)
    # 将 plot_history 转换为 AI 可读的文本块，确保连贯性
    history_context = ""
    if "plot_history" in st.session_state and st.session_state.plot_history:
        # 为了防止Token溢出，我们可能需要限制长度，但尽量包含所有
        entries = []
        for i, entry in enumerate(st.session_state.plot_history):
            entries.append(
                f"【第{i + 1}幕 ({entry['timestamp']})】\n玩家行动：{entry['action']}\n剧情进展：{entry['content']}")

        full_hist = "\n\n".join(entries)
        # 简单的截断保护 (保留最后 12000 字符，约为 3000-4000 token，留给 generation)
        history_context = full_hist[-12000:] if len(full_hist) > 12000 else full_hist
    else:
        history_context = "（游戏刚开始，暂无剧情历史）"

    traits = st.session_state.investigator.get('traits', '无') if st.session_state.investigator else '无'

    # 疯狂状态注入
    madness_status = st.session_state.game_state['sanity_data']
    madness_prompt = ""
    if madness_status['status'] != "sane":
        madness_prompt = f"【警告：调查员处于疯狂状态！】类型：{madness_status['status']}。当前症状：{madness_status['symptom']}。请在剧情中体现出调查员的感知被扭曲、强迫行为或极度恐惧。如果玩家的行动与症状冲突（例如恐高症却想爬楼），请描述其生理上的抗拒甚至行动失败。"

    # DM 风格注入
    dm_style_prompt = ""
    if "dm_style" in st.session_state:
        style = st.session_state.dm_style
        dm_style_prompt = f"""
        【DM 叙事风格调教（必须执行）】
        1. 恐怖倾向[{style['horror']}]：请根据此倾向描写环境和心理。
        2. 致命度[{style['lethality']}]：判定失败后果的严重程度以此为准。
        3. 信息密度[{style['density']}]：决定单次回复包含的信息量。
        4. 模组偏向[{style['focus']}]：剧情发展重点。
        """

    base_prompt = f"""
    【指令】你是《克苏鲁的呼唤》7版模组《罗德岛的黄金梦魇》的守密人(KP)。
    {dm_style_prompt}

    【权威状态表 (Authoritative State)】
    当前数值状态：{current_state_json}

    【相关前情回顾 (Retrieval Augmented Generation - 摘要版)】
    {relevant_memories}

    【完整剧情回溯 (Full History Context - 避免前后矛盾)】
    {history_context}

    【玩家信息】
    玩家角色特性：{traits}
    {madness_prompt}

    【剧本背景】
    1921年12月，罗德岛。10年前“前进号”捕鲸船带回了被诅咒的金币。
    船长德怀特变成了深潜者。雕塑家麦凯恩是傀儡。
    玩家继承了刚死于意外的叔叔史密斯的遗产。

    【玩家本次行动】{action_context}
    【本次判定结果】{outcome_str}
    {fumble_instruction}

    【思维流程与一致性守则（重要）】
    1. **承接上下文**：剧情必须严格承接在【完整剧情回溯】的最后一段之后。
    2. **一致性检查（反穿帮）**：
       - **禁止瞬移**：时间/地点必须符合权威状态。
       - **禁止全知NPC**：NPC 绝不能透露不在 `knowledge` 列表中的信息。
       - **禁止虚空造物**：物品/伤势/金钱不能凭空变化。
       - **禁止诈尸**：已死亡角色不能说话。
       - **绝对遵守检定结果**：如果失败，绝不能让玩家达成目标；如果大失败，必须发生灾难。

    【NPC 行为控制】
    请查阅 `npcs` 状态。
    1. **知情范围**：NPC 绝不能透露不在 `knowledge` 列表中的信息。
    2. **态度演变**：如果玩家冒犯 NPC，请在 JSON 中将 `attitude` 更新为 '警惕' 或 '敌对'。
    3. **谎言判定**：如果 `is_lying` 为 true，NPC 表面说一套，但若玩家【心理学】成功，请在剧情中暗示其神情异常。
    4. **性格驱动**：根据 `weakness` (恐惧/欲望) 决定 NPC 的行动动机。

    【线索生成规则（严肃调查）】
    1. **分级**：
       - [核心]：推进剧情必须的。如果检定失败，必须以“带代价的方式”获得，或获得“模糊版”。
       - [支线]：补充背景，非必须。
       - [误导]：检定失败/大失败时生成。看似有用但错误的信息。
    2. **可信度与状态**：
       - 检定成功：可信度[高]。
       - 检定失败/勉强成功：可信度[中/低]。
       - 大失败：生成[误导]线索，且标记为可信度[高]（玩家会误以为是真的）。

    【任务】
    1. 生成剧情发展。遵循高效叙事（70%信息，30%氛围）。
    2. 如果涉及恐怖场景，请根据来源（普通/暴力/真相/神话）判定 SAN 损失，填入 JSON。
    3. **自我审查**：在输出 JSON 前，检查是否违反了“一致性守则”。如果有严重逻辑冲突，将 `consistency_check.passed` 设为 false。
    4. **关键步骤**：在回复末尾，用 JSON 代码块输出状态变更 AND 本回合记忆摘要。

    【输出格式要求 (JSON Schema)】
    [剧情文本...]

    ```json
    {{
        "consistency_check": {{
            "passed": true, // 如果发现严重穿帮（瞬移、死人说话等）填 false
            "reason": "如果 false，请说明原因"
        }},
        "investigator": {{
            "hp_change": 0,
            "san_change": 0, // 负数表示损失
            "san_loss_source": "无/普通恐怖/暴力/宇宙真相/神话存在", 
            "mp_change": 0
        }},
        "game_state": {{
            "world": {{
                "time": "更新后的时间(如流逝)",
                "location": "更新后的地点(如未变则不填)"
            }},
            "npcs": {{
                "NPC名称": {{ "attitude": "新态度", "is_lying": false }} 
            }},
            "new_clues": [
                {{
                    "content": "线索具体内容",
                    "type": "核心/支线/误导",
                    "source": "来源",
                    "reliability": "高/中/低"
                }}
            ],
            "rules": {{
                "temp_madness": false
            }}
        }},
        "memory": {{
            "summary": "50~120字的回合摘要。包含地点时间、行动、检定结果、线索、状态变化、下一步意图。",
            "tags": ["NPC:某人", "地点:某地", "线索:某物", "检定:技能-结果"],
            "fields": {{
                "what_happened": "事件简述",
                "who": "涉及NPC",
                "where": "地点",
                "when": "时间",
                "checks": "{outcome_str}",
                "consequences": "结果影响"
            }}
        }}
    }}
    ```
    """

    # 引入重试机制
    max_retries = 1
    current_prompt = base_prompt

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=st.session_state.model_name,
                messages=[{"role": "user", "content": current_prompt}],
                temperature=0.8
            )
            full_content = response.choices[0].message.content

            # 分离剧情文本和 JSON
            narrative = full_content
            json_match = re.search(r"```json(.*?)```", full_content, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                narrative = full_content.replace(json_match.group(0), "").strip()
                try:
                    updates = json.loads(json_str)

                    # 检查一致性
                    consistency = updates.get("consistency_check", {"passed": True})
                    if not consistency.get("passed", True):
                        if attempt < max_retries:
                            # 触发重写
                            error_reason = consistency.get("reason", "未知一致性错误")
                            add_log("correction", f"🛑 触发剧情修正", f"检测到：{error_reason}")
                            current_prompt = base_prompt + f"\n\n【系统警告】上一次生成被检测为不一致：{error_reason}。请重新生成，务必修正此逻辑错误！"
                            continue
                        else:
                            # 超过重试次数，强制通过但记录
                            add_log("system", "⚠️ 一致性检查失败但已达重试上限", consistency.get("reason"))

                    # 应用状态更新
                    memory_result = apply_state_updates(updates)
                    return narrative, memory_result

                except json.JSONDecodeError:
                    add_log("system", "状态解析失败", "AI返回了无效的JSON")
                    return narrative, None

            # 如果没有 JSON，直接返回文本（极为罕见）
            return narrative, None

        except Exception as e:
            return f"AI 错误: {e}", None

    return "系统错误：重试循环溢出。", None


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
if "rules_read" not in st.session_state: st.session_state.rules_read = False

if "notebook" not in st.session_state: st.session_state.notebook = []
if "action_log" not in st.session_state: st.session_state.action_log = []
if "last_dice_result" not in st.session_state: st.session_state.last_dice_result = None
if "pending_check" not in st.session_state: st.session_state.pending_check = None

# 新增：剧情存档初始化
if "plot_history" not in st.session_state: st.session_state.plot_history = []

# 新增：DM 风格默认值
if "dm_style" not in st.session_state:
    st.session_state.dm_style = {
        "horror": "心理",
        "lethality": "写实",
        "density": "适中",
        "focus": "调查"
    }

# 新增：权威状态表初始化
if "game_state" not in st.session_state:
    # 定义初始 NPC 数据
    INITIAL_NPCS = {
        "雷蒙德律师": {
            "desc": "史密斯的遗产律师，戴着金丝眼镜，精明算计。",
            "knowledge": ["遗嘱内容", "史密斯的财务状况(取了巨款)", "公寓钥匙"],
            "attitude": "友好",
            "secret": "私吞了一部分现金遗产",
            "is_lying": True,
            "weakness": "贪财"
        },
        "麦凯恩": {
            "desc": "住在隔壁的疯癫艺术家，雕塑家。",
            "knowledge": ["金币的魔力", "深潜者的存在", "史密斯的死因真相"],
            "attitude": "警惕",
            "secret": "他是克苏鲁的傀儡，想要金币",
            "is_lying": False,
            "weakness": "对旧日支配者的恐惧"
        },
        "德怀特船长": {
            "desc": "已变成深潜者的前船长，潜伏在暗处。",
            "knowledge": ["金币的来源", "深潜者契约"],
            "attitude": "敌对",
            "secret": "非人生物",
            "is_lying": False,
            "weakness": "对黄金的渴望"
        }
    }

    st.session_state.game_state = {
        "world": {
            "time": "1921-12-20 10:00",
            "location": "雷蒙德律师事务所",
            "weather": "冷雨"
        },
        "npcs": INITIAL_NPCS,
        "case": {
            "unsolved": ["史密斯的真正死因", "金币的下落"]
        },
        "rules": {
            "temp_madness": False,
            "bonus_dice": 0
        },
        "sanity_data": {
            "start_of_day": 50,  # 修复点：将 san 改为默认值 50
            "daily_loss": 0,
            "status": "sane",
            "symptom": "无"
        }
    }

# 新增：记忆档案初始化
if "memory_archive" not in st.session_state:
    st.session_state.memory_archive = []


# ================= 5. 界面渲染 =================

# --- 规则导读页 ---
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
    <strong style='color:red;'>⚠️ 推骰失败 = 必须承受严重后果！必须承受严重后果！必须承受严重后果！必须承受严重后果！</strong></p>

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

    # 初始化权威状态表 (如果尚未初始化)
    if "game_state" not in st.session_state or not st.session_state.game_state:
        # 定义初始 NPC 数据
        INITIAL_NPCS = {
            "雷蒙德律师": {
                "desc": "史密斯的遗产律师，戴着金丝眼镜，精明算计。",
                "knowledge": ["遗嘱内容", "史密斯的财务状况(取了巨款)", "公寓钥匙"],
                "attitude": "友好",
                "secret": "私吞了一部分现金遗产",
                "is_lying": True,
                "weakness": "贪财"
            },
            "麦凯恩": {
                "desc": "住在隔壁的疯癫艺术家，雕塑家。",
                "knowledge": ["金币的魔力", "深潜者的存在", "史密斯的死因真相"],
                "attitude": "警惕",
                "secret": "他是克苏鲁的傀儡，想要金币",
                "is_lying": False,
                "weakness": "对旧日支配者的恐惧"
            },
            "德怀特船长": {
                "desc": "已变成深潜者的前船长，潜伏在暗处。",
                "knowledge": ["金币的来源", "深潜者契约"],
                "attitude": "敌对",
                "secret": "非人生物",
                "is_lying": False,
                "weakness": "对黄金的渴望"
            }
        }

        st.session_state.game_state = {
            "world": {
                "time": "1921-12-20 10:00",
                "location": "雷蒙德律师事务所",
                "weather": "冷雨"
            },
            "npcs": INITIAL_NPCS,
            "case": {
                "unsolved": ["史密斯的真正死因", "金币的下落"]
            },
            "rules": {
                "temp_madness": False,
                "bonus_dice": 0
            },
            "sanity_data": {
                "start_of_day": san,
                "daily_loss": 0,
                "status": "sane",
                "symptom": "无"
            }
        }

    # 初始化记忆档案
    if "memory_archive" not in st.session_state:
        st.session_state.memory_archive = []

    with st.spinner("守密人正在翻阅《罗德岛的黄金梦魇》剧本..."):
        raw_text, mem_res = ai_narrate_outcome("游戏开始", None)
        st.session_state.dm_text = process_clues(raw_text)
        # 保存到历史存档
        save_plot_history("游戏开始", raw_text)
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

        # 新增：DM 风格参数设置
        with st.expander("⚙️ 守密人(DM) 风格设置", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state.dm_style["horror"] = c1.selectbox("恐怖倾向", ["心理 (压抑/暗示)", "猎奇 (血腥/肉体)",
                                                                            "宇宙 (宏大/虚无)"])
            st.session_state.dm_style["lethality"] = c2.selectbox("致命度",
                                                                  ["写实 (标准)", "宽容 (剧情为主)", "残酷 (容易死亡)"])
            st.session_state.dm_style["density"] = c1.selectbox("信息密度",
                                                                ["适中", "克制 (需多追问)", "密集 (大量细节)"])
            st.session_state.dm_style["focus"] = c2.selectbox("模组偏向",
                                                              ["调查 (解谜)", "生存 (战斗/逃生)", "阴谋 (NPC博弈)"])

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
        普通(≤技能) / 困难(≤1/2) / 极限(≤1/5) / 大成功(1) / 大失败(96-100)
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

    # 显示世界状态 (Authoritative State)
    if "game_state" in st.session_state:
        gs = st.session_state.game_state
        st.sidebar.markdown(f"""
        <div class='world-state-box'>
        📅 <b>{gs['world']['time']}</b><br>
        📍 {gs['world']['location']}<br>
        ☁️ {gs['world'].get('weather', '')}
        </div>
        """, unsafe_allow_html=True)

        # 显示精神状态 (Sanity State)
        san_status = gs['sanity_data']['status']
        san_status_label = {
            "sane": "🟢 神志清醒",
            "temporary": "🟡 临时疯狂",
            "indefinite": "🔴 不定性疯狂",
            "permanent": "💀 永久疯狂"
        }.get(san_status, "未知")

        st.sidebar.markdown(f"""
        <div class='mental-state-box'>
        <b>🧠 {san_status_label}</b><br>
        当前症状: {gs['sanity_data']['symptom']}<br>
        当日丧失: {gs['sanity_data']['daily_loss']} SAN
        </div>
        """, unsafe_allow_html=True)

        # 如果疯狂，弹出警示
        if san_status != "sane":
            st.sidebar.markdown(f"<div class='madness-alert'>⚠️ 你正处于疯狂状态！</div>", unsafe_allow_html=True)

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
        <strong style='color:red;'>⚠️ 推骰失败 = 必须承受严重后果！必须承受严重后果！必须承受严重后果！必须承受严重后果！</strong></p>

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

    # 新增：剧情进度与存档区
    if "plot_history" in st.session_state and st.session_state.plot_history:
        with st.expander("📚 剧情回溯与存档 (Story Archive)", expanded=False):
            turn_count = len(st.session_state.plot_history)
            st.progress(min(turn_count, 100) / 100, text=f"当前进度：第 {turn_count} 幕")

            # 使用滑块或列表来查看旧剧情
            if turn_count > 0:
                # 修复逻辑：只有当大于1幕时才显示滑块，否则直接设为1
                if turn_count > 1:
                    selected_turn = st.slider("回溯过往剧情 (拖动查看)", 1, turn_count, turn_count)
                else:
                    selected_turn = 1

                # 显示选中的剧情
                entry = st.session_state.plot_history[selected_turn - 1]
                st.markdown(f"""
                <div class='history-box'>
                    <div class='history-header'>
                        🎬 第 {selected_turn} 幕 | {entry['timestamp']} | 行动: {entry['action']}
                    </div>
                    <div class='history-content'>{process_clues(entry['content'])}</div>
                </div>
                """, unsafe_allow_html=True)

                # 显示所有历史记录的开关
                if st.checkbox("显示所有历史记录列表"):
                    for idx, h_entry in enumerate(reversed(st.session_state.plot_history)):
                        st.markdown(f"""
                        <div class='history-entry'>
                            <div class='history-header'>第 {turn_count - idx} 幕 - {h_entry['action']}</div>
                            <div class='history-content'>{process_clues(h_entry['content'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("暂无历史剧情。")

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
                        narrative, mem_res = ai_narrate_outcome(check['action'], check_info)
                        st.session_state.dm_text = process_clues(narrative)

                        # 保存到历史存档
                        save_plot_history(check['action'], narrative)

                        # 单独记录一个系统日志来存储记忆（如果是检定后触发的剧情）
                        if mem_res:
                            add_log("system", "剧情推进", None, mem_res['summary'], mem_res['tags'])

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

                    with st.spinner("守密人正在判断是否需要检定..."):
                        need_roll, skill, diff = ai_judge_check(action, inv['skills'])

                        if need_roll:
                            add_log("action", action)
                            st.session_state.pending_check = {
                                "action": action,
                                "skill": skill,
                                "difficulty": diff
                            }
                            st.rerun()
                        else:
                            narrative, mem_res = ai_narrate_outcome(action)
                            st.session_state.dm_text = process_clues(narrative)

                            # 保存到历史存档
                            save_plot_history(action, narrative)

                            # 在记录行动的同时，附加上这一轮产生的记忆
                            add_log("action", action, None,
                                    mem_res['summary'] if mem_res else None,
                                    mem_res['tags'] if mem_res else None)
                            st.rerun()

    with tab2:
        st.markdown("### 📝 行动日志")

        # 搜索和筛选栏
        c1, c2 = st.columns([3, 1])
        with c1:
            search_txt = st.text_input("🔍 搜索", placeholder="输入关键词搜索日志...", label_visibility="collapsed")
        with c2:
            filter_opt = st.selectbox("类型", ["全部", "行动", "检定", "系统", "疯狂", "修正"],
                                      label_visibility="collapsed")

        # 筛选逻辑
        display_logs = []
        if st.session_state.action_log:
            for log in reversed(st.session_state.action_log):
                # 1. 类型筛选
                if filter_opt != "全部":
                    if filter_opt == "行动" and log['type'] != 'action': continue
                    if filter_opt == "检定" and log['type'] != 'dice': continue
                    if filter_opt == "系统" and log['type'] != 'system': continue
                    if filter_opt == "疯狂" and log['type'] != 'madness': continue
                    if filter_opt == "修正" and log['type'] != 'correction': continue

                # 2. 文本搜索
                if search_txt:
                    term = search_txt.lower()
                    content_match = term in log['content'].lower()
                    result_match = log['result'] and term in log['result'].lower()
                    summary_match = log.get('memory_summary') and term in log['memory_summary'].lower()
                    tags_match = log.get('memory_tags') and any(term in t.lower() for t in log['memory_tags'])

                    if not (content_match or result_match or summary_match or tags_match):
                        continue

                display_logs.append(log)

        # 渲染
        if display_logs:
            for log in display_logs:
                # 映射 CSS 类
                css_class = "log-type-system"
                icon = "🤖"
                if log['type'] == 'action':
                    css_class = "log-type-action"
                    icon = "👤"
                elif log['type'] == 'dice':
                    css_class = "log-type-dice"
                    icon = "🎲"
                elif log['type'] == 'madness':
                    css_class = "log-type-madness"
                    icon = "🧠"
                elif log['type'] == 'correction':
                    css_class = "log-type-correction"
                    icon = "🔧"

                # 构建 HTML
                memory_html = ""
                if log.get('memory_summary'):
                    tags_html = "".join([f"<span class='memory-tag'>{t}</span>" for t in log['memory_tags']])
                    memory_html = f"""
                    <div class='memory-summary'>
                        <div><b>📜 回合摘要：</b>{log['memory_summary']}</div>
                        <div class='memory-tags'>{tags_html}</div>
                    </div>
                    """

                result_html = f"<div class='log-result'>结果: {log['result']}</div>" if log['result'] else ""

                st.markdown(f"""
                <div class='log-entry {css_class}'>
                    <div class='log-header'>
                        <span>{icon} {log['type'].upper()}</span>
                        <span>{log['time']}</span>
                    </div>
                    <div class='log-content'>{log['content']}</div>
                    {result_html}
                    {memory_html}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("没有找到匹配的记录。")

    with tab3:
        st.markdown("### 📓 调查笔记本")
        if st.session_state.notebook:
            for note in st.session_state.notebook:

                # 确定标签样式
                type_badge = "badge-side"
                if note.get('type') == '核心':
                    type_badge = "badge-core"
                elif note.get('type') == '误导':
                    type_badge = "badge-mislead"

                rel_badge = "badge-mid"
                if note.get('reliability') == '高':
                    rel_badge = "badge-high"
                elif note.get('reliability') == '低':
                    rel_badge = "badge-low"

                st.markdown(f"""
                <div class='clue-item'>
                    <div class='clue-header'>
                        <div>
                            <span class='badge {type_badge}'>{note.get('type', '一般')}</span>
                            <span class='badge {rel_badge}'>可信度: {note.get('reliability', '中')}</span>
                        </div>
                        <span class='clue-meta'>{note['time']}</span>
                    </div>
                    <div class='clue-content'>{note['content']}</div>
                    <div class='clue-meta' style='margin-top:5px;'>来源: {note.get('source', '未知')}</div>
                </div>
                """, unsafe_allow_html=True)
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
