"""首页：工具简介与本月概览。"""

from datetime import date

import streamlit as st

import database

st.set_page_config(page_title="记账工具", page_icon="💰")
database.init_db()

st.title("💰 网页记账工具")
st.caption("记录日常支出 · 6 个固定分类 · 数据存储于本地 SQLite")

this_month = date.today().strftime("%Y-%m")
total_fen, count = database.month_summary(this_month)

col1, col2 = st.columns(2)
col1.metric(f"本月支出（{this_month}）", f"¥{total_fen / 100:,.2f}")
col2.metric("本月笔数", f"{count} 笔")

st.divider()
st.markdown(
    "使用左侧导航：\n\n"
    "- **添加账目** —— 录入金额、分类、日期、备注\n"
    "- **账目列表** —— 按月份/分类筛选查看明细，按 ID 删除\n"
    "- **分类统计** —— 分类金额统计表与柱状图"
)
