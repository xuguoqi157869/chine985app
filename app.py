import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from elasticsearch import Elasticsearch
import jieba
from datetime import datetime, timedelta
import warnings

# 忽略无关警告
warnings.filterwarnings('ignore')
# 适配云端的字体配置（解决中文乱码）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# -------------------------- 全局初始化与工具函数 --------------------------
# 页面基础配置
st.set_page_config(
    page_title="985高校研究生院信息智能系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 手动配置基础参数
os.environ["ES_HOST"] = "localhost"
os.environ["ES_PORT"] = "9200"
os.environ["ES_INDEX"] = "graduate_school_news"
os.environ["TOTAL_SCHOOLS"] = "39"
os.environ["CRAWL_CYCLE"] = "7"

# 初始化Elasticsearch连接
@st.cache_resource
def init_es():
    try:
        es = Elasticsearch(hosts=[f"http://{os.getenv('ES_HOST')}:{os.getenv('ES_PORT')}"])
        if es.ping():
            st.toast("✅ 成功连接Elasticsearch数据库", icon="✅")
            return es
        else:
            st.warning("⚠️ Elasticsearch连接失败，展示模拟数据", icon="⚠️")
            return None
    except Exception as e:
        st.warning(f"⚠️ 数据库连接异常：{str(e)}，展示模拟数据", icon="⚠️")
        return None

# 数据查询函数（无ES时返回模拟数据）
def query_es(es, condition=None):
    # 模拟数据
    mock_data = {
        "高校名称": ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学"],
        "标题": [
            "2025年硕士研究生招生复试工作安排",
            "2025年推免生接收政策调整通知",
            "研究生培养方案修订及实施细则",
            "2025年博士招生申请考核制公告",
            "研究生院关于学位授予工作的补充通知"
        ],
        "发布时间": [
            "2025-02-20 10:00:00",
            "2025-02-18 09:30:00",
            "2025-02-15 14:20:00",
            "2025-02-12 16:10:00",
            "2025-02-10 09:00:00"
        ],
        "关键词": ["复试,招生,安排", "推免,政策,调整", "培养方案,修订", "博士招生,申请考核", "学位授予,补充通知"],
        "原文链接": [
            "https://yz.tsinghua.edu.cn",
            "https://yz.pku.edu.cn",
            "https://gs.fudan.edu.cn",
            "https://yzb.sjtu.edu.cn",
            "https://yzdzb.zju.edu.cn"
        ],
        "抓取时间": [
            "2025-02-28 08:00:00",
            "2025-02-28 08:05:00",
            "2025-02-28 08:10:00",
            "2025-02-28 08:15:00",
            "2025-02-28 08:20:00"
        ]
    }
    mock_df = pd.DataFrame(mock_data)
    
    if not es:
        return mock_df
    
    try:
        query_body = {"match_all": {}} if not condition else condition
        res = es.search(index=os.getenv('ES_INDEX'), query=query_body, size=1000)
        data_list = []
        for hit in res['hits']['hits']:
            source = hit['_source']
            data_list.append({
                "高校名称": source.get("school_name", ""),
                "标题": source.get("page_title", ""),
                "发布时间": source.get("publish_time", ""),
                "关键词": ",".join(source.get("keywords", [])),
                "原文链接": source.get("url", ""),
                "抓取时间": source.get("crawl_time", "")
            })
        df = pd.DataFrame(data_list)
        # 时间格式化
        if "发布时间" in df.columns:
            df["发布时间"] = pd.to_datetime(df["发布时间"], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S').fillna("未知")
        if "抓取时间" in df.columns:
            df["抓取时间"] = pd.to_datetime(df["抓取时间"], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S').fillna("未知")
        return df if not df.empty else mock_df
    except Exception as e:
        st.error(f"❌ 数据查询失败：{str(e)}", icon="❌")
        return mock_df

# 生成知识图谱
def generate_knowledge_graph(df):
    if df.empty:
        st.warning("⚠️ 无数据，无法生成知识图谱", icon="⚠️")
        return
    try:
        G = nx.Graph()
        # 添加节点和边
        for _, row in df.iterrows():
            school = row["高校名称"]
            keywords = row["关键词"].split(",") if row["关键词"] else []
            G.add_node(school, node_type="高校", size=1000)
            for kw in keywords:
                if kw and kw != "未知":
                    G.add_node(kw, node_type="关键词", size=300)
                    G.add_edge(school, kw, weight=1)
        # 绘制图谱
        fig, ax = plt.subplots(figsize=(12, 8))
        pos = nx.spring_layout(G, k=0.8, iterations=20)
        node_colors = ["#1f77b4" if G.nodes[n]["node_type"] == "高校" else "#ff7f0e" for n in G.nodes]
        node_sizes = [G.nodes[n]["size"] for n in G.nodes]
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, alpha=0.8)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#cccccc", alpha=0.5)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
        ax.set_title("985高校研究生院信息知识图谱（高校-关键词关联）", fontsize=16, pad=20)
        ax.axis("off")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ 知识图谱生成失败：{str(e)}", icon="❌")

# 初始化ES
es = init_es()

# -------------------------- 页面主体布局 --------------------------
st.title("📚 985高校研究生院信息智能系统", anchor=False)
st.divider()

# 顶部导航栏
col1, col2, col3 = st.columns(3)
with col1:
    tab_selected = st.radio(
        "功能选择",
        ["数据总览", "关键词搜索", "知识图谱"],
        horizontal=True,
        label_visibility="collapsed"
    )

# -------------------------- 功能1：数据总览 --------------------------
if tab_selected == "数据总览":
    st.subheader("📊 高校研究生院数据总览", anchor=False)
    col_data, col_stats = st.columns([3, 1])
    
    # 侧边筛选
    with st.sidebar:
        st.header("🔍 数据筛选")
        school_list = ["全部"] + list(query_es(es)["高校名称"].unique())
        selected_school = st.selectbox("选择高校", school_list, index=0)
        time_range = st.slider("发布时间范围（近N天）", 7, 90, 30)
        selected_kw = st.text_input("输入关键词筛选", placeholder="如：招生、复试、调剂")
    
    # 构建筛选条件
    must_conditions = []
    if selected_school != "全部":
        must_conditions.append({"match": {"school_name": selected_school}})
    if selected_kw:
        must_conditions.append({"match": {"keywords": selected_kw}})
    time_ago = (datetime.now() - timedelta(days=time_range)).strftime('%Y-%m-%d')
    must_conditions.append({"range": {"publish_time": {"gte": time_ago, "format": "yyyy-MM-dd"}}})
    query_condition = {"bool": {"must": must_conditions}} if must_conditions else None
    
    # 展示数据和统计
    df_data = query_es(es, query_condition)
    with col_data:
        st.dataframe(
            df_data,
            column_config={"原文链接": st.column_config.LinkColumn("原文链接", display_text="查看原文")},
            hide_index=True,
            use_container_width=True
        )
    with col_stats:
        st.metric("📈 总数据条数", len(df_data))
        st.metric("🏫 涉及高校数", df_data["高校名称"].nunique())
        st.metric("🔑 关键词数", len(set(','.join(df_data["关键词"].tolist()).split(','))))
        st.metric("📅 爬取周期", f"{os.getenv('CRAWL_CYCLE')}天/次")

# -------------------------- 功能2：关键词搜索 --------------------------
if tab_selected == "关键词搜索":
    st.subheader("🔍 关键词精准搜索", anchor=False)
    search_kw = st.text_input("输入搜索关键词（支持多关键词空格分隔）", placeholder="招生 复试 保研 分数线")
    search_btn = st.button("开始搜索", type="primary")
    
    if search_btn and search_kw:
        kw_list = search_kw.split()
        must_conditions = [{"match": {"keywords": kw}} for kw in kw_list]
        query_condition = {"bool": {"must": must_conditions}}
        df_search = query_es(es, query_condition)
        st.dataframe(
            df_search,
            column_config={"原文链接": st.column_config.LinkColumn("原文链接", display_text="查看原文")},
            hide_index=True,
            use_container_width=True
        )
        st.caption(f"共找到 {len(df_search)} 条相关数据")
    elif search_btn and not search_kw:
        st.warning("⚠️ 请输入搜索关键词", icon="⚠️")

# -------------------------- 功能3：知识图谱 --------------------------
if tab_selected == "知识图谱":
    st.subheader("🗺️ 知识图谱（高校-关键词关联）", anchor=False)
    st.caption("💡 图谱中蓝色节点为高校，橙色节点为关键词，节点大小代表关联度")
    df_kg = query_es(es)
    generate_knowledge_graph(df_kg)

# -------------------------- 页面底部 --------------------------
st.divider()
with st.footer():
    st.markdown("### 📌 项目说明")
    st.markdown(f"本系统为985高校研究生院信息智能分析平台，覆盖{os.getenv('TOTAL_SCHOOLS')}所985高校，爬虫抓取周期{os.getenv('CRAWL_CYCLE')}天/次 | 技术栈：Streamlit + Elasticsearch + NetworkX + Matplotlib")
    st.markdown("© 2025 985高校研究生院信息智能系统项目组")