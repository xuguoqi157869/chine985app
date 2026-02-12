import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta

# ====================== 页面基础配置 ======================
st.set_page_config(
    page_title="985高校研究生院信息抓取平台",
    page_icon="🎓",
    layout="wide"  # 宽屏布局，适配多列展示
)

# 自定义样式（美化页面）
st.markdown("""
<style>
/* 美化卡片 */
.stMetric {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 8px;
}
/* 详情卡片 */
.detail-card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #2188ff;
}
/* 新内容标签 */
.new-tag {
    color: #e74c3c;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ====================== 模拟后端数据（你只需替换成真实爬虫数据） ======================
# 说明：后端爬虫需输出类似格式的DataFrame，字段如下：
# - 高校名称：985高校名
# - 网页标题：抓取的网页题目
# - 发布时间：网页的发布时间（datetime格式）
# - 网页URL：研究生院原始网址
# - 本地存储路径：网页存本地的路径
# - 标签：自定义标签（用逗号分隔）
# - 是否新内容：判重结果（True=新网页，False=重复）
# - 抓取时间：本次抓取的时间
def get_mock_data():
    # 985高校列表（示例）
    universities = ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学"]
    # 模拟标签
    tags = ["招生通知", "复试安排", "导师招聘", "学术讲座", "政策公告"]
    # 生成模拟数据
    data = []
    for i in range(50):  # 模拟50条抓取记录
        uni = universities[i % len(universities)]
        tag = tags[i % len(tags)] + "," + tags[(i+1) % len(tags)]  # 多标签
        publish_time = datetime.date.today() - timedelta(days=i % 30)
        crawl_time = datetime.date.today() - timedelta(days=i % 7)  # 模拟每周抓取
        is_new = True if i % 5 == 0 else False  # 每5条1条新内容
        data.append({
            "高校名称": uni,
            "网页标题": f"{uni}研究生院{tag.split(',')[0]}-{i}",
            "发布时间": publish_time,
            "网页URL": f"https://gs.{uni.lower().replace(' ', '')}.edu.cn/{i}.html",
            "本地存储路径": f"./data/{uni}/{publish_time}_{i}.html",
            "标签": tag,
            "是否新内容": is_new,
            "抓取时间": crawl_time
        })
    df = pd.DataFrame(data)
    # 格式转换（确保时间是日期格式）
    df["发布时间"] = pd.to_datetime(df["发布时间"]).dt.date
    df["抓取时间"] = pd.to_datetime(df["抓取时间"]).dt.date
    return df

# 加载数据（替换成：df = pd.read_csv("后端爬虫输出的csv文件")）
df = get_mock_data()

# ====================== 页面标题 & 核心指标概览 ======================
st.title("🎓 985高校研究生院信息抓取平台")
st.divider()

# 核心指标（4列展示）
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总抓取网页数", len(df))
with col2:
    st.metric("涉及985高校数", df["高校名称"].nunique())
with col3:
    st.metric("本次新抓取内容", len(df[df["是否新内容"] == True]))
with col4:
    # 计算下次抓取时间（每周一次，假设本周抓取日是周五）
    next_crawl = datetime.date.today() + timedelta(days=(4 - datetime.date.today().weekday()) % 7)
    st.metric("下次抓取时间", next_crawl.strftime("%Y-%m-%d"))

st.divider()

# ====================== 筛选栏（侧边栏） ======================
st.sidebar.title("🔍 数据筛选")
# 1. 高校筛选
selected_uni = st.sidebar.multiselect(
    "选择高校",
    options=df["高校名称"].unique(),
    default=df["高校名称"].unique()
)
# 2. 标签筛选
all_tags = list(set([tag for tags in df["标签"].str.split(',') for tag in tags]))  # 拆分所有标签
selected_tag = st.sidebar.multiselect(
    "选择标签",
    options=all_tags,
    default=all_tags
)
# 3. 时间筛选
min_date = df["发布时间"].min()
max_date = df["发布时间"].max()
date_range = st.sidebar.date_input(
    "发布时间范围",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
# 4. 新内容筛选
only_new = st.sidebar.checkbox("仅查看新抓取内容")

# ====================== 应用筛选条件 ======================
filtered_df = df.copy()
# 高校筛选
filtered_df = filtered_df[filtered_df["高校名称"].isin(selected_uni)]
# 标签筛选（包含任一选中标签即可）
filtered_df = filtered_df[filtered_df["标签"].apply(lambda x: any(tag in x for tag in selected_tag))]
# 时间筛选
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["发布时间"] >= date_range[0]) &
        (filtered_df["发布时间"] <= date_range[1])
    ]
# 新内容筛选
if only_new:
    filtered_df = filtered_df[filtered_df["是否新内容"] == True]

# ====================== 数据展示 ======================
st.subheader("📋 抓取数据列表")
# 导出按钮
col_export, col_empty = st.columns([1, 9])
with col_export:
    # 导出筛选后的结果
    csv_data = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 导出筛选结果",
        data=csv_data,
        file_name=f"985研究生院数据_{datetime.date.today()}.csv",
        mime="text/csv"
    )

# 展示筛选后的数据表格（隐藏部分列，简化视图）
show_columns = ["高校名称", "网页标题", "发布时间", "标签", "是否新内容"]
st.dataframe(
    filtered_df[show_columns].rename(columns={"是否新内容": "是否新抓取"}),
    use_container_width=True,
    column_config={
        "发布时间": st.column_config.DateColumn("发布时间"),
        "是否新抓取": st.column_config.CheckboxColumn("是否新抓取", disabled=True)
    }
)

# ====================== 详情展示（选中某条数据） ======================
st.divider()
st.subheader("🔍 内容详情")
# 选择要查看的记录
selected_title = st.selectbox(
    "选择要查看的网页标题",
    options=filtered_df["网页标题"].tolist(),
    index=0 if len(filtered_df) > 0 else None
)

if selected_title and len(filtered_df) > 0:
    # 获取选中记录的详情
    detail = filtered_df[filtered_df["网页标题"] == selected_title].iloc[0]
    # 详情卡片
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    # 标题 + 新内容标签
    title_html = f"<h4>{detail['网页标题']}</h4>"
    if detail["是否新内容"]:
        title_html += '<span class="new-tag">【新抓取内容】</span>'
    st.markdown(title_html, unsafe_allow_html=True)
    
    # 详情信息（分2列展示）
    col_left, col_right = st.columns(2)
    with col_left:
        st.write(f"**所属高校**：{detail['高校名称']}")
        st.write(f"**发布时间**：{detail['发布时间']}")
        st.write(f"**抓取时间**：{detail['抓取时间']}")
        st.write(f"**标签**：{detail['标签']}")
    with col_right:
        st.write(f"**原始URL**：")
        st.markdown(f'<a href="{detail["网页URL"]}" target="_blank">{detail["网页URL"]}</a>', unsafe_allow_html=True)
        st.write(f"**本地存储路径**：{detail['本地存储路径']}")
    
    # 网页内容预览（模拟，实际可读取本地HTML文件）
    st.write("---")
    st.write("**网页内容预览**（本地文件）：")
    st.info("提示：实际部署时，可读取本地HTML文件并展示内容，此处为模拟预览")
    st.text_area(
        "",
        value=f"【模拟内容】{detail['网页标题']} 的本地网页内容...",
        height=200,
        disabled=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== 底部提示 ======================
st.divider()
st.caption(f"📢 数据更新至：{datetime.date.today()} | 下次自动抓取时间：{next_crawl.strftime('%Y-%m-%d')}")