# CLAUDE.md

网页版个人记账工具（纯支出），技术栈：Python 3.13 + Streamlit（多页应用）+ sqlite3（标准库）。

## 运行

```bash
pip install -r requirements.txt
python -m streamlit run app.py    # http://localhost:8501
```

> 本机 `streamlit` 命令不在 PATH（包装在用户 site-packages），一律用 `python -m streamlit` 代替；首次运行的邮箱询问已通过 `~/.streamlit/credentials.toml`（空 email）跳过。

## 项目结构

```
finance_cli/
├── app.py                    # 入口首页：简介 + 本月概览（st.metric）
├── database.py               # 数据访问层：DDL + CRUD + 统计 SQL（唯一含 SQL 的文件）
├── pages/
│   ├── 1_add_record.py       # 录入表单
│   ├── 2_record_list.py      # 月份/分类筛选 + 明细表格 + 按 ID 删除
│   └── 3_category_stats.py   # 分类统计表 + 柱状图（st.bar_chart）
├── requirements.txt          # streamlit>=1.41；pandas/altair 随 streamlit 带入，勿单独列出
└── data/finance.db           # 首次运行自动创建，已 gitignore
```

## 架构约定（修改代码前必读）

### 耦合边界
- 文件名一律纯英文（禁止中文）；侧边栏导航的中文标题由各页 `st.set_page_config(page_title=...)` 提供（Streamlit ≥1.31 侧边栏直接显示 page_title），勿靠改文件名实现
- 页面文件只 `import database`，页面之间零依赖
- 所有 SQL 只出现在 `database.py`；页面不拼 SQL
- 跨页共享状态只有 `st.session_state` 的 `month_filter`、`cat_filter` 两个 key（列表页与统计页月份筛选联动）

### 数据约定
- 金额以**分**为单位存 INTEGER（`amount > 0` 有 CHECK 约束），展示层统一 `fen / 100`
- 元 → 分必须用 `round(x * 100)`，禁止 `int()`（浮点截断会少 1 分）
- 日期存 TEXT `'YYYY-MM-DD'`；月份筛选用 `substr(date, 1, 7) = ?`
- 分类唯一真源是 `database.CATEGORIES`（6 个固定分类：餐饮、交通、购物、娱乐、居住、其他），不建分类表，UI 不硬编码第二份
- 筛选 WHERE 动态拼装但一律参数化占位符，禁止字符串拼接 SQL

### Streamlit × sqlite3 关键决策（勿"优化"回去）
- **每次操作新建短连接**（`database.get_conn()` contextmanager，手动 close）——不用 `st.cache_resource` 缓存连接，规避 Streamlit 多线程 `check_same_thread` 问题
- **不用 `st.cache_data` 缓存查询**——无缓存保证写后读永远最新
- **全 app 不用 `st.rerun()`**——靠「先写后读」的布局顺序在同一次 run 内刷新（如删除表单必须在表格查询代码上方）
- 写操作必须包在 `if submitted:` / `if st.form_submit_button():` 内，否则改筛选会重复写库
- 月份下拉从 DB `DISTINCT` 生成，且必须带防线：`st.session_state` 中旧值不在 options 时回退"全部月份"（选中月份的记录被删光会触发）
- `DB_PATH` 锚定 `__file__` 而非 cwd，换目录启动读同一个库

### UI 约定
- 录入/删除用 `st.form` 包裹（避免每次击键触发 rerun）
- 删除返回 `rowcount == 0` 时用 `st.error` 提示 ID 不存在，禁止静默成功
- 空结果用 `st.info` 提示，不渲染空表/空图
- 统计表按 `CATEGORIES` 补齐 6 行（无发生的分类计 0），占比列需除零保护

## 测试

无自动化测试框架。改动后按手动清单验证：空态无 traceback、19.99 录入后精确显示、0.07+0.03 合计为 0.10、删除不存在 ID 报错、删光选中月份后下拉回退、重启后数据仍在。

## Git

- 不自动 commit / push
- `data/`（SQLite 库文件）不进 git
