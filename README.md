# 🍽️ Restaurant Ordering & Operational Analytics System
### 餐厅点餐管理系统与经营数据分析平台

> **项目定位 / Project Positioning**
> 这不仅仅是一个 POS（收银）原型，而是一个**从底层数据流转到上层商业决策的完整闭环**。项目源于真实的传统餐饮业务痛点，展示了从业务需求拆解、关系型数据库建模、交易一致性保障，到最终 BI 经营分析的全链路能力。
> 
> *This is not just a POS prototype, but a complete closed-loop from underlying data flow to top-level business decision-making. Originated from real pain points of traditional restaurants, it demonstrates the full-chain capability from requirement analysis, relational database modeling, and transaction consistency, to the final BI operational analytics.*

---

## 💡 项目背景与产品初衷 (Business Value & Product Origin)

*   **源于真实痛点**：本项目的契机始于课程作业，但我将其延伸为一次完整的商业产品落地尝试。我有一位朋友家中经营传统餐厅，在交流中发现传统门店在数字化点餐、经营数据沉淀上存在明显的痛点。结合当前主流餐饮品牌的线上服务模式，我决定从零搭建一个涵盖“点单交易闭环 + 经营数据分析”的餐厅系统，以此探索技术如何真正赋能传统餐饮业务。
*   **产品落地与成本取舍（MVP策略）**：系统不仅实现了前端的点餐、结账、退款等核心交易逻辑，还涵盖了后端的菜品管理、桌台状态流转。考虑到云服务器成本，核心交易系统目前在本地完成全链路验证，并提供三种展示方式
*   **数据产品化**：为了进一步挖掘餐饮数据价值，针对系统底层数据，我独立使用 Streamlit 搭建了经营分析看板。将枯燥的数据库表转化为涵盖营收趋势、复购率、产品排行等维度的可视化界面，完整打通了“交易—数据—决策”的闭环。

---

## 🛠️ 工程严谨性与技术架构 (Engineering Rigor & Architecture)

为了支撑上述复杂的业务分析，底层需要一个极其稳固的数据库底座：

*   **规范化数据建模**：基于 3NF 设计 MySQL 关系型数据库，包含外键、CHECK 约束与唯一约束。引入主数据（Dimensions）与订单事实表（Facts）分离，历史订单明细保留购买时的单价快照，确保财务历史数据不被未来的菜单调价所污染。
*   **事务与并发控制（核心亮点）**：针对餐饮业常见的“多服务员同时结账”场景，实现了事务级安全结账，并加入了**桌台状态保护机制**，防止并发脏数据与重复扣款，确保财务报表 100% 准确。
*   **全栈与展示层**：后端采用 FastAPI + SQLAlchemy 2，前端提供轻量级 Web UI。为打破技术壁垒，方便业务方理解，独立开发了基于 Streamlit 的交互式经营分析看板（内置 1000 笔模拟订单快照）。
*   **性能与真实数据验证**：使用 1,000 笔模拟数据及 UCI 真实零售数据集（100万+条）进行链路验证；通过 EXPLAIN 执行计划分析与索引优化，支撑 1K/10K/50K 不同数据规模下的秒级业务查询。

---

## 🚀 交互与演示 (Demo & Showcases)

考虑到为了更直观地展示项目成果，我准备了以下三种体验方式：

*   📊 **[1. 数据分析交互式看板复现 (Streamlit Live)](https://restaurant-ordering-and-operational-analytics-dcvtzkhr4wjycvp2.streamlit.app/)** 
    *无需本地部署，直接在线预览经营指标与 BI 报表。*
    *看板托管在 Streamlit 免费社区版，若显示休眠，点击‘Yes, get this app back up!’即可唤醒，约30秒加载*
*   🎬 **[2. 核心交易系统本地演示视频 (Watch Demo)](https://github.com/user-attachments/assets/e6e81f14-7902-4da3-9e34-9a920ceba7d4)** 
    *包含从开台、点餐到结账完整业务流，以及底层并发保护的交互演示。*
*   🌐 **[3. 项目完整图文展示页 (Portfolio Page)](https://yuehaomin-svg.github.io/Restaurant-Ordering-and-Operational-Analytics/)** 
    *包含更详细的架构图、指标口径说明与业务洞察报告。*

---
---

## 📁 仓库结构 (Repository Structure)

```text
app/
  models.py             relational schema
  schemas.py            API input and output contracts
  services/             transactional order operations
  routers/              menu, order, and analytics APIs
frontend/               full-stack web interface
scripts/                database initialization, seeding, and evaluation
tests/                  transaction and API tests
docs/                   design, metrics, plan, report outline, and chart SVGs
sql/schema.sql          generated MySQL DDL
streamlit_app.py        Streamlit demo entry point
data/restaurant_demo.sqlite3   1,000-order SQLite snapshot for the Streamlit demo
```

Analytical outputs for the BI exercise are generated under `data/processed/bi`. Raw and processed datasets are excluded from Git and can be recreated using the scripts above; the only committed data file is `data/restaurant_demo.sqlite3`, the 1,000-order snapshot used by the Streamlit demo.


## Architecture

```text
Browser UI
   |
   v
FastAPI application
   |-- order and menu services
   |-- analytical queries
   v
MySQL 9
   |-- normalized operational tables
   |-- order facts and master dimensions
```

The operational schema follows 3NF. Analytical endpoints aggregate the same normalized data using meaningful SQL queries. Historical order items retain the unit price at purchase time so later menu price changes do not corrupt revenue history.

## Technology Stack

- Python 3.12
- FastAPI and Pydantic
- SQLAlchemy 2
- MySQL 9
- HTML, CSS, and vanilla JavaScript
- Streamlit for the browser demo (`streamlit_app.py`)
- Pytest and SQLite for isolated transaction-flow tests

## Run Locally

Start the project database:

```powershell
docker compose up -d
```

Create and activate the Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Initialize and seed the database:

```powershell
python -m scripts.initialize_db
python -m scripts.seed_data --orders 1000 --reset
```

`sql/schema.sql` already holds the generated MySQL DDL, so the application runs without re-exporting the schema.

Start the application:

```powershell
python -m uvicorn app.main:app --reload --port 8010
```

Open:

- Application: `http://127.0.0.1:8010`
- API documentation: `http://127.0.0.1:8010/docs`

The database container uses host port `3308` to avoid conflicting with other local MySQL instances.

## Streamlit Demo

`streamlit_app.py` is a browser-ready analytics demo backed by the committed `data/restaurant_demo.sqlite3` snapshot of 1,000 simulated orders and 3,032 order lines. It is a read-only presentation layer for product, customer, timing, refund and order exploration.

```powershell
python -m venv .venv-streamlit
.\.venv-streamlit\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit Community Cloud should use `streamlit_app.py` as the main file and install `requirements.txt`. The application dependencies for the FastAPI system are kept separately in `requirements-app.txt`.

## Static Portfolio Summary

`index.html` is a self-contained one-page portfolio summary. It can be opened directly in a browser or hosted through GitHub Pages from the repository root.



