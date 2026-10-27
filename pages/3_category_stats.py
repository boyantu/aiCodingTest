"""分类统计页：分类金额统计表 + 柱状图。"""

import pandas as pd
import streamlit as st

import database

st.set_page_config(page_title="分类统计", page_icon="📊", layout="wide")
database.init_db()

# ---- 侧边栏月份筛选（与列表页共用 month_filter，跨页联动） ----
months = [database.ALL_MONTHS] + database.list_months()
# 防线：选中月份的记录被删光后旧值不在 options 中，selectbox 会抛异常
if st.session_state.get("month_filter") not in months:
    st.session_state["month_filter"] = database.ALL_MONTHS
month = st.sidebar.selectbox("月份", months, key="month_filter")

st.title("📊 分类统计")

# stats_by_category 已补齐 6 个固定分类并按金额降序
stats = database.stats_by_category(month)
total_fen = sum(s["total_fen"] for s in stats)
total_count = sum(s["count"] for s in stats)

col1, col2 = st.columns(2)
col1.metric("总支出", f"¥{total_fen / 100:,.2f}")
col2.metric("记录笔数", f"{total_count} 笔")

df = pd.DataFrame(
    {
        "分类": [s["category"] for s in stats],
        "笔数": [s["count"] for s in stats],
        "金额(元)": [s["total_fen"] / 100 for s in stats],
        # 除零保护：无记录时占比全 0
        "占比(%)": [
            round(s["total_fen"] / total_fen * 100, 1) if total_fen else 0.0
            for s in stats
        ],
    }
)

st.dataframe(
    df,
    width="stretch",
    hide_index=True,
    column_config={
        "金额(元)": st.column_config.NumberColumn(format="¥%.2f"),
        "占比(%)": st.column_config.NumberColumn(format="%.1f%%"),
    },
)

# 单序列柱状图：分类身份由 x 轴标签承载，无需图例；降序排列便于比较
if total_count == 0:
    st.info("当前筛选范围内暂无记录")
else:
    st.bar_chart(df, x="分类", y="金额(元)", height=320)
