import streamlit as st
import pandas as pd
import itertools
from io import StringIO

# ==========================================
# 1. 核心配置与样式
# ==========================================

st.set_page_config(page_title="PTCG 战队 BP 助手 (4人备战版)", page_icon="🛡️", layout="wide")

# 颜色样式：根据 1-6 的数值上色
def get_color_style(val):
    if not isinstance(val, (int, float)): 
        return ""
    if val <= 1.5: 
        return "background-color: #22c55e; color: white"  # 1: 深绿 (大优)
    if val <= 2.5: 
        return "background-color: #86efac; color: #14532d"  # 2: 浅绿 (小优)
    if val <= 3.5: 
        return "background-color: #dbeafe; color: #1e3a8a"  # 3: 蓝 (均势)
    if val <= 4.5: 
        return "background-color: #fef08a; color: #713f12"  # 4: 黄 (小劣)
    if val <= 5.5: 
        return "background-color: #fca5a5; color: #7f1d1d"  # 5: 橙红 (劣)
    return "background-color: #ef4444; color: white; font-weight: bold"  # 6: 深红 (不想打)

# ==========================================
# 2. 默认数据 (备用)
# ==========================================

DEFAULT_DATA = [
    { "player": "老李", "deck": "放逐鬼龙", "matchups": { "恶喷": 1, "沙奈朵": 3, "鬼龙": 3, "密勒顿": 3, "轰鸣月": 3, "赛富豪": 1, "双窝梦幻": 4, "古剑豹": 3, "洛奇亚": 4, "卡比兽": 1, "连击熊": 4, "炎帝": 3, "汇流梦幻": 4, "宙斯": 2, "团结之翼": 3 } },
    { "player": "CRAZY", "deck": "密勒顿", "matchups": { "恶喷": 6, "沙奈朵": 3, "鬼龙": 3, "密勒顿": 3, "轰鸣月": 3, "赛富豪": 4, "双窝梦幻": 5, "古剑豹": 2, "洛奇亚": 1, "卡比兽": 6, "连击熊": 5, "炎帝": 3, "汇流梦幻": 3, "宙斯": 3, "团结之翼": 1 } },
    { "player": "橙子", "deck": "恶喷", "matchups": { "恶喷": 3, "沙奈朵": 4, "鬼龙": 5, "密勒顿": 2, "轰鸣月": 3, "赛富豪": 4, "双窝梦幻": 2, "古剑豹": 3, "洛奇亚": 3, "卡比兽": 6, "连击熊": 5, "炎帝": 2, "汇流梦幻": 1, "宙斯": 5, "团结之翼": 2 } },
    { "player": "苡瞳", "deck": "沙奈朵", "matchups": { "恶喷": 3, "沙奈朵": 3, "鬼龙": 4, "密勒顿": 5, "轰鸣月": 1, "赛富豪": 2, "双窝梦幻": 4, "古剑豹": 3, "洛奇亚": 2, "卡比兽": 6, "连击熊": 6, "炎帝": 6, "汇流梦幻": 3, "宙斯": 5, "团结之翼": 1 } },
    { "player": "PK", "deck": "轰鸣月", "matchups": { "恶喷": 3, "沙奈朵": 6, "鬼龙": 3, "密勒顿": 3, "轰鸣月": 3, "赛富豪": 3, "双窝梦幻": 3, "古剑豹": 2, "洛奇亚": 2, "卡比兽": 3, "连击熊": 1, "炎帝": 4, "汇流梦幻": 3, "宙斯": 1, "团结之翼": 1 } },
    { "player": "龙嫂", "deck": "梦幻", "matchups": { "恶喷": 6, "沙奈朵": 3, "鬼龙": 3, "密勒顿": 2, "轰鸣月": 6, "赛富豪": 2, "双窝梦幻": 3, "古剑豹": 1, "洛奇亚": 3, "卡比兽": 3, "连击熊": 1, "炎帝": 1, "汇流梦幻": 3, "宙斯": 3, "团结之翼": 4 } }
]
# ==========================================
# 3. CSV 解析函数 (增强版)
# ==========================================

def parse_uploaded_csv(file):
    try:
        # 尝试用不同编码读取
        try:
            content = file.read().decode('utf-8')
        except:
            content = file.read().decode('gbk')
        
        # 读取CSV，尝试不同的分隔符
        for sep in [',', '\t', ';']:
            try:
                df_raw = pd.read_csv(StringIO(content), sep=sep, header=None, engine='python')
                if df_raw.shape[1] >= 3:  # 至少3列（选手、卡组、一个对手）
                    break
            except:
                continue
        
        if df_raw is None or df_raw.shape[1] < 3:
            st.error("CSV 格式无法识别：列数不足")
            return None
        
        # 寻找表头行
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = ' '.join(str(x) for x in row.astype(str).values if str(x).strip())
            if any(keyword in row_str for keyword in ['沙奈朵', '比雕恶喷', '鬼龙', '密勒顿']):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            # 如果没有找到明显的表头行，使用第0行作为表头
            header_row_idx = 0
        
        # 重新读取，指定header行
        df = pd.read_csv(StringIO(content), header=header_row_idx, sep=sep, engine='python')
        
        # 清理列名
        df.columns = [str(col).strip() for col in df.columns]
        
        # 尝试识别选手和卡组列
        player_col = None
        deck_col = None
        
        # 常见的列名关键词
        player_keywords = ['选手', '队员', 'player', 'name', '名称']
        deck_keywords = ['卡组', 'deck', '卡组名称', '使用卡组']
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in player_keywords):
                player_col = col
            elif any(keyword in col_lower for keyword in deck_keywords):
                deck_col = col
        
        # 如果无法自动识别，使用前两列
        if player_col is None and len(df.columns) >= 1:
            player_col = df.columns[0]
        if deck_col is None and len(df.columns) >= 2:
            deck_col = df.columns[1]
        
        if player_col is None or deck_col is None:
            st.error("无法识别选手或卡组列")
            return None
        
        # 处理数据
        team_data = []
        
        for _, row in df.iterrows():
            if pd.isna(row[player_col]) or pd.isna(row[deck_col]):
                continue
            
            player_name = str(row[player_col]).strip()
            deck_name = str(row[deck_col]).strip()
            
            # 提取对阵数据
            matchups = {}
            for col in df.columns:
                if col == player_col or col == deck_col:
                    continue
                
                # 跳过空列名
                if pd.isna(col) or 'unnamed' in str(col).lower() or str(col).strip() == '':
                    continue
                
                deck_opponent = str(col).strip()
                score = row[col]
                
                # 处理分数
                if pd.isna(score):
                    score = 3.0
                else:
                    try:
                        score = float(score)
                        # 确保分数在1-6之间
                        if score < 1 or score > 6:
                            score = 3.0
                    except:
                        score = 3.0
                
                matchups[deck_opponent] = score
            
            # 添加到数据列表
            team_data.append({
                "player": player_name,
                "deck": deck_name,
                "matchups": matchups
            })
        
        return team_data
        
    except Exception as e:
        st.error(f"解析CSV时出错: {str(e)}")
        return None

# ==========================================
# 4. 核心算法 (推荐 4 人)
# ==========================================

def calculate_ban_pick(team_data, selected_opponents):
    if not team_data or not selected_opponents:
        return {
            'ban_target': None,
            'ban_score': 0,
            'pick_combo': None,
            'remaining_opponents': [],
            'risk_analysis': None
        }
    
    results = {}
    
    # --- 1. Ban 计算 ---
    unique_opponents = list(set(selected_opponents))
    opponent_scores = {}
    
    for opp_deck in unique_opponents:
        total_score = 0
        count = 0
        for member in team_data:
            # 获取评分，如果没有则使用默认值3
            rating = member['matchups'].get(opp_deck, 3)
            total_score += rating
            count += 1
        opponent_scores[opp_deck] = total_score / count if count > 0 else 0
    
    if opponent_scores:
        ban_target = max(opponent_scores.items(), key=lambda x: x[1])[0]
        ban_reason_score = opponent_scores[ban_target]
    else:
        ban_target = None
        ban_reason_score = 0

    results['ban_target'] = ban_target
    results['ban_score'] = ban_reason_score

    # --- 2. Pick 计算 (选4个) ---
    remaining_opponents = selected_opponents.copy()
    if ban_target and ban_target in remaining_opponents:
        remaining_opponents = [opp for opp in remaining_opponents if opp != ban_target]

    if not remaining_opponents or len(team_data) < 4:
        results['pick_combo'] = None
        results['remaining_opponents'] = remaining_opponents
        return results

    all_members = [m['player'] for m in team_data]
    # 生成所有4人组合
    combos_4 = list(itertools.combinations(all_members, min(4, len(all_members))))
    
    best_combo_4 = None
    best_score_4 = float('inf')
    best_combo_details = {}

    # 寻找总分最低的 4 人组
    for combo in combos_4:
        current_combo_score = 0
        player_scores = {}
        
        for player_name in combo:
            player_data = next((p for p in team_data if p['player'] == player_name), None)
            if not player_data:
                continue
                
            player_score = 0
            for opp_deck in remaining_opponents:
                rating = player_data['matchups'].get(opp_deck, 3)
                player_score += rating
            
            player_scores[player_name] = player_score
            current_combo_score += player_score
        
        # 检查是否是最佳组合
        if current_combo_score < best_score_4:
            best_score_4 = current_combo_score
            best_combo_4 = combo
            best_combo_details = player_scores

    results['pick_combo'] = best_combo_4
    results['pick_score'] = best_score_4
    results['player_scores'] = best_combo_details
    results['remaining_opponents'] = remaining_opponents
    
    # --- 3. 风险评估 ---
    if best_combo_4:
        worst_case_score = float('-inf')
        worst_case_banned = None
        worst_case_details = {}
        
        # 遍历这4个人，假设每人都可能被Ban
        for banned_player in best_combo_4:
            remaining_3 = [p for p in best_combo_4 if p != banned_player]
            
            # 计算这剩下的3人总分
            score_3 = 0
            player_scores_3 = {}
            for player_name in remaining_3:
                player_data = next((p for p in team_data if p['player'] == player_name), None)
                if not player_data:
                    continue
                    
                player_score = 0
                for opp_deck in remaining_opponents:
                    rating = player_data['matchups'].get(opp_deck, 3)
                    player_score += rating
                
                player_scores_3[player_name] = player_score
                score_3 += player_score
            
            # 如果分数变高（变差），说明这个被Ban的人很重要
            if score_3 > worst_case_score:
                worst_case_score = score_3
                worst_case_banned = banned_player
                worst_case_details = player_scores_3
        
        results['risk_analysis'] = {
            'if_ban': worst_case_banned,
            'remaining_score': worst_case_score,
            'remaining_players_scores': worst_case_details
        }

    return results

# ==========================================
# 5. 界面渲染
# ==========================================

st.title("🛡️ PTCG 战队 BP 助手 (4人备战版)")
st.caption("策略：推荐 4 名队友，防止对方 Ban 人导致阵容崩盘")

# 侧边栏：文件上传
with st.sidebar:
    st.header("📂 数据源")
    
    # CSV示例下载
    st.markdown("**CSV格式示例:**")
    example_data = """选手,卡组,沙奈朵,鬼龙,密勒顿,赛富豪
三毛九鬼龙,鬼龙,3,5,4,3
土豆,鬼龙,2,4,3,1
语申,尾狸恶喷,4,6,1,5
ZZ,沙奈朵,1,3,5,2
乐子人,lostK喷,6,2,6,4
龟龟,涡轮梦幻,5,1,2,6"""
    
    st.download_button(
        label="下载示例CSV",
        data=example_data,
        file_name="ptcg_matchups_example.csv",
        mime="text/csv"
    )
    
    uploaded_file = st.file_uploader("上传最新优劣势表格 (CSV)", type="csv", 
                                     help="请确保CSV包含：选手列、卡组列、以及各对手卡组的优劣势评分(1-6)")
    
    current_team_data = DEFAULT_DATA
    if uploaded_file is not None:
        parsed_data = parse_uploaded_csv(uploaded_file)
        if parsed_data:
            current_team_data = parsed_data
            st.success(f"✅ 成功加载 {len(current_team_data)} 名队员数据！")
            
            # 显示加载的选手信息
            with st.expander("已加载的选手"):
                for member in current_team_data:
                    st.write(f"**{member['player']}** - {member['deck']}")
        else:
            st.warning("⚠️ CSV解析失败，使用默认数据")
            current_team_data = DEFAULT_DATA
    else:
        st.info("💡 请上传最新表格，或使用默认数据进行演示")
    
    st.markdown("---")
    st.header("⚙️ 对局设置")
    
    # 提取所有对手卡组
    all_possible_opponents = set()
    for member in current_team_data:
        all_possible_opponents.update(member['matchups'].keys())
    sorted_opponents = sorted([x for x in all_possible_opponents if x])
    
    selected_opponents = []
    default_values = ["沙奈朵", "鬼龙", "密勒顿", "赛富豪", "(无)", "(无)"]
    
    st.markdown("**选择对手卡组 (最多6套):**")
    for i in range(6):
        col1, col2 = st.columns([3, 1])
        with col1:
            options = ["(无)"] + sorted_opponents
            def_index = 0
            if i < len(default_values) and default_values[i] in options:
                def_index = options.index(default_values[i])
            
            deck = st.selectbox(
                f"对手卡组 #{i+1}", 
                options=options, 
                index=def_index, 
                key=f"deck_select_{i}",
                label_visibility="collapsed"
            )
        
        with col2:
            if deck != "(无)":
                # 显示该卡组的平均威胁值
                avg_score = 0
                count = 0
                for member in current_team_data:
                    score = member['matchups'].get(deck, 3)
                    avg_score += score
                    count += 1
                if count > 0:
                    avg_score = avg_score / count
                    color = "#ef4444" if avg_score >= 4.5 else "#fca5a5" if avg_score >= 3.5 else "#86efac"
                    st.markdown(f"<span style='color:{color}; font-weight:bold'>{avg_score:.1f}</span>", unsafe_allow_html=True)
        
        if deck != "(无)":
            selected_opponents.append(deck)
    
    st.markdown("---")
    st.write(f"**当前已选:** {len(selected_opponents)} 套")
    if selected_opponents:
        st.write("，".join(selected_opponents))

# 主区域
if not selected_opponents:
    st.info("👈 请先在左侧选择至少1个对手卡组")
    st.markdown("### 默认队员数据预览")
    df_default = pd.DataFrame([
        {"队员": f"{m['player']} ({m['deck']})", "卡组类型": m['deck']}
        for m in DEFAULT_DATA
    ])
    st.dataframe(df_default, use_container_width=True)
else:
    # 显示优劣势表格
    st.subheader("📊 优劣势速览 (颜色越绿越优势)")
    
    # 创建表格数据
    table_rows = []
    for member in current_team_data:
        row = {"队员": f"{member['player']}", "卡组": member['deck']}
        total_score = 0
        
        for opp in selected_opponents:
            rating = member['matchups'].get(opp, 3)
            row[opp] = rating
            total_score += rating
        
        # 计算平均分
        row["平均分"] = total_score / len(selected_opponents) if selected_opponents else 0
        table_rows.append(row)
    
    df = pd.DataFrame(table_rows)
    df.set_index("队员", inplace=False)
    
    # 应用样式
    styled_df = df.style.applymap(
        lambda x: get_color_style(x) if isinstance(x, (int, float)) and str(x).replace('.', '').isdigit() else "",
        subset=[col for col in df.columns if col not in ['队员', '卡组']]
    )
    
    # 高亮平均分列
    def highlight_avg(val):
        if isinstance(val, (int, float)):
            if val <= 2.5: return "background-color: #dcfce7; color: #14532d; font-weight: bold"
            if val >= 4.5: return "background-color: #fee2e2; color: #7f1d1d; font-weight: bold"
            return "background-color: #fef9c3; color: #713f12"
        return ""
    
    styled_df = styled_df.applymap(highlight_avg, subset=['平均分'])
    
    st.dataframe(styled_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🧠 AI 战术建议")
    
    # 计算建议
    analysis = calculate_ban_pick(current_team_data, selected_opponents)
    
    # 使用列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔴 建议 Ban 目标")
        if analysis['ban_target']:
            # 创建威胁度指示器
            threat_level = analysis['ban_score']
            threat_color = "#ef4444" if threat_level >= 4.5 else "#fca5a5" if threat_level >= 3.5 else "#fef08a"
            
            st.markdown(f"""
            <div style="border-left: 5px solid {threat_color}; padding: 10px; background-color: #f9fafb; border-radius: 5px;">
                <h3 style="color: {threat_color}; margin-top: 0;">{analysis['ban_target']}</h3>
                <p><strong>威胁指数:</strong> {threat_level:.2f}</p>
                <p><strong>理由:</strong> 这是对方卡组中，对我方全体平均威胁最大的卡组。</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("没有足够的对手数据来建议Ban目标")
    
    with col2:
        st.markdown("### 🟢 建议 4 人名单")
        if analysis.get('pick_combo'):
            combo = analysis['pick_combo']
            combo_score = analysis.get('pick_score', 0)
            
            # 显示组合信息
            st.markdown(f"""
            <div style="padding: 15px; background-color: #dcfce7; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="color: #14532d; margin: 0;">{" + ".join(combo)}</h4>
                <p style="color: #166534; margin: 5px 0 0 0;">总评分: <strong>{combo_score:.1f}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # 显示每个队员的详细评分
            with st.expander("查看详细评分"):
                if analysis.get('player_scores'):
                    for player, score in analysis['player_scores'].items():
                        # 查找队员卡组
                        deck = next((m['deck'] for m in current_team_data if m['player'] == player), "未知")
                        st.write(f"**{player}** ({deck}): {score:.1f}分")
            
            # 风险分析
            st.markdown("#### 🛡️ 抗压分析")
            risk = analysis.get('risk_analysis')
            if risk:
                # 风险等级评估
                risk_score = risk['remaining_score']
                if risk_score > combo_score * 0.9:  # 如果风险评分接近原始评分
                    risk_level = "高"
                    risk_color = "#ef4444"
                elif risk_score > combo_score * 0.8:
                    risk_level = "中"
                    risk_color = "#f59e0b"
                else:
                    risk_level = "低"
                    risk_color = "#22c55e"
                
                st.markdown(f"""
                <div style="padding: 12px; background-color: #fef3c7; border-radius: 6px; border-left: 4px solid {risk_color};">
                    <p><strong>最坏情况:</strong> 如果对方 Ban 掉 <strong>{risk['if_ban']}</strong></p>
                    <p><strong>剩余3人风险值:</strong> {risk['remaining_score']:.1f}</p>
                    <p><strong>风险等级:</strong> <span style="color:{risk_color}; font-weight:bold">{risk_level}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("查看风险详情"):
                    st.write("剩余3人评分:")
                    for player, score in risk['remaining_players_scores'].items():
                        st.write(f"- {player}: {score:.1f}分")
                
                st.caption(f"💡 推荐这4人是因为即使被Ban掉{risk['if_ban']}，剩余的阵容依然是所有组合中最稳定的。")
                
            if analysis['remaining_opponents']:
                st.markdown("---")
                st.caption(f"📋 需要应对的剩余对手: {', '.join(analysis['remaining_opponents'])}")
        else:
            st.warning("无法生成4人组合，请检查数据或对手选择")
    
    # 添加操作建议
    st.markdown("---")
    st.subheader("📝 操作建议")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 🎯 优先策略")
        st.markdown("""
        1. **执行Ban选**: 优先Ban掉建议的卡组
        2. **关注核心**: 保护建议名单中的关键队员
        3. **灵活调整**: 根据对方实际选择微调
        """)
    
    with col4:
        st.markdown("### ⚠️ 注意事项")
        st.markdown("""
        1. 评分仅供参考，实际对局还需考虑选手状态
        2. 关注对方的Ban人策略
        3. 准备备用方案应对意外情况
        """)
    
    # 添加数据导出功能
    st.markdown("---")
    with st.expander("📤 导出当前分析"):
        export_data = {
            "对手卡组": selected_opponents,
            "建议Ban": analysis['ban_target'],
            "Ban威胁指数": analysis['ban_score'],
            "建议4人名单": list(analysis['pick_combo']) if analysis['pick_combo'] else [],
            "名单总评分": analysis.get('pick_score', 0),
            "风险分析": analysis.get('risk_analysis', {})
        }
        
        st.json(export_data)
        
        # 创建可下载的文本报告
        report_text = f"""PTCG BP分析报告
====================
分析时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

对手卡组: {', '.join(selected_opponents)}

建议Ban目标: {analysis['ban_target']}
威胁指数: {analysis['ban_score']:.2f}

建议4人名单: {', '.join(analysis['pick_combo']) if analysis['pick_combo'] else '无'}
名单总评分: {analysis.get('pick_score', 0):.1f}

风险分析:
  最坏情况: 被Ban {analysis.get('risk_analysis', {}).get('if_ban', '未知')}
  剩余评分: {analysis.get('risk_analysis', {}).get('remaining_score', 0):.1f}
"""
        
        st.download_button(
            label="下载分析报告",
            data=report_text,
            file_name=f"ptcg_bp_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
