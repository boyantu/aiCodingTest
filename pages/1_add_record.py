"""添加账目页：表单录入金额、分类、日期、备注。"""

from datetime import date

import streamlit as st

import database

st.set_page_config(page_title="添加账目", page_icon="➕")
database.init_db()

st.title("➕ 添加账目")

with st.form("add_form"):
    amount = st.number_input(
        "金额（元）",
        min_value=0.01,
        max_value=1_000_000.0,
        step=0.01,
        format="%.2f",
    )
    category = st.selectbox("分类", database.CATEGORIES)
    day = st.date_input("日期", value=date.today())
    note = st.text_input("备注（可选）")
    submitted = st.form_submit_button("💾 保存", width="stretch")

# 写操作只在点击提交的那一次 run 执行，避免切换筛选时重复插入
if submitted:
    # 元 → 分必须用 round：int() 截断会少 1 分（19.99 * 100 == 1998.99…）
    record_id = database.add_record(
        round(amount * 100), category, day.isoformat(), note.strip()
    )
    st.success(
        f"已记账（ID {record_id}）：{category}　¥{amount:.2f}　{day.isoformat()}"
    )
