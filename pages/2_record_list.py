"""账目列表页：月份/分类筛选 + 明细表格 + 按 ID 删除。"""

import pandas as pd
import streamlit as st

import database

st.set_page_config(page_title="账目列表", page_icon="📋", layout="wide")
database.init_db()

# ---- 侧边栏筛选（month_filter 与统计页共用，跨页联动） ----
months = [database.ALL_MONTHS] + database.list_months()
# 防线：选中月份的记录被删光后旧值不在 options 中，selectbox 会抛异常
if st.session_state.get("month_filter") not in months:
    st.session_state["month_filter"] = database.ALL_MONTHS
month = st.sidebar.selectbox("月份", months, key="month_filter")
category = st.sidebar.selectbox(
    "分类", [database.ALL_CATEGORIES, *database.CATEGORIES], key="cat_filter"
)

st.title("📋 账目列表")

# ---- 删除（放在表格上方：同一次 run 内先删后查，表格即时刷新） ----
with st.form("delete_form"):
    rec_id = st.number_input("要删除的记录 ID", min_value=1, step=1)
    if st.form_submit_button("🗑 删除"):
        if database.delete_record(int(rec_id)) == 0:
            st.error(f"ID {int(rec_id)} 不存在，未删除任何记录")
        else:
            st.success(f"已删除 ID {int(rec_id)}")

# ---- 明细表格 ----
rows = database.list_records(month, category)
if not rows:
    st.info("暂无符合条件的记录")
else:
    df = pd.DataFrame(
        {
            "ID": [r["id"] for r in rows],
            "日期": [r["date"] for r in rows],
            "分类": [r["category"] for r in rows],
            "金额(元)": [r["amount"] / 100 for r in rows],
            "备注": [r["note"] for r in rows],
        }
    )
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "金额(元)": st.column_config.NumberColumn(format="¥%.2f"),
        },
    )
    total_fen = sum(r["amount"] for r in rows)
    st.caption(f"共 {len(rows)} 笔 · 合计 ¥{total_fen / 100:,.2f}")
