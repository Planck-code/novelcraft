# 网文 AI 分析助手

中文网络小说作者 AI 辅助分析工具 — 本地单机 MVP。

- FastAPI Web 页面 + REST API 接口
- SQLite 数据库持久化
- 自动识别章节标题并切分 txt 小说文件
- 对接 OpenAI / DeepSeek / Gemini 进行 AI 分析
- 长期记忆中心（角色、势力、世界观、境界体系、时间线）
- 修改建议生成与可视化数据接口

## 快速开始

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key（至少选一个）:
#   OPENAI_API_KEY=sk-...
#   DEEPSEEK_API_KEY=sk-...
#   GEMINI_API_KEY=...

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动服务
uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000` 开始使用。

## 项目结构

```
novelcraft/
├── app/
│   ├── main.py                  # FastAPI 应用入口
│   ├── config/settings.py       # 配置管理
│   ├── api/                     # API 路由层
│   │   ├── router.py            # 路由汇总
│   │   └── v1/                  # v1 API 端点
│   ├── schemas/                 # Pydantic 请求/响应模型
│   ├── domain/                  # 领域实体（纯数据类）
│   ├── modules/                 # 业务模块
│   │   ├── novel_import/        # TXT 导入与章节切分
│   │   ├── project_management/  # 小说项目管理
│   │   ├── memory_center/       # 长期记忆中心
│   │   ├── revision_advice/     # 修改建议生成
│   │   └── visualization/       # 可视化数据聚合
│   ├── services/                # 应用服务层
│   │   └── chapter_analysis.py  # 章节分析编排
│   ├── workflows/               # 工作流编排
│   ├── llm/                     # LLM 统一网关
│   │   ├── gateway.py           # 统一调用接口
│   │   └── providers/           # 各 provider 适配器
│   ├── common/                  # 通用工具
│   │   ├── encoding.py          # 编码检测
│   │   ├── json_repair.py       # JSON 解析与修复
│   │   ├── prompt_loader.py     # Prompt 文件加载
│   │   ├── prompt_builder.py    # 5层 Prompt 构建
│   │   ├── retry.py             # 重试装饰器
│   │   └── schemas.py           # LLM 输出 JSON Schema
│   ├── infra/                   # 基础设施层
│   │   ├── db/                  # 数据库 (SQLAlchemy)
│   │   ├── storage/             # 文件存储适配器
│   │   ├── queue/               # 异步任务队列
│   │   └── vector_adapter/      # 向量库适配器接口
│   └── web/                     # Web 前端
│       ├── templates/           # Jinja2 模板
│       └── static/              # 静态资源
├── prompts/                     # Prompt 模板文件
│   ├── system/                  # 系统角色提示词
│   ├── chapter_analysis/        # 章节分析任务提示词
│   ├── revision_advice/         # 修改建议提示词
│   ├── memory_update/           # 记忆更新提示词
│   └── consistency_check/       # 一致性检查提示词
├── scripts/                     # 工具脚本
├── tests/                       # 测试
│   ├── unit/                    # 单元测试
│   └── integration/             # 集成测试
├── data/                        # 运行时数据（自动生成）
│   ├── uploads/                 # 上传的原始文件
│   ├── novels/                  # 切章后的小说文件
│   └── analysis_results/        # 分析原始响应
├── requirements.txt
├── .env.example
└── README.md
```

## 功能说明

### 1. 小说导入
- 创建小说项目 → 上传 `.txt` 文件 → 自动编码检测 → 章节标题识别 → 自动切章
- 支持的章节标题格式：`第X章`、`第XX章`（中文/阿拉伯数字）、`楔子`、`序章`、`尾声`、`番外` 等

### 2. 章节分析
- 调用 LLM 对单章进行多维度分析：
  - 剧情摘要、关键事件、情绪评估
  - 冲突分析、世界观变化、伏笔识别
  - 出场角色识别与状态追踪
- 分析结果结构化存储，支持重新分析

### 3. 修改建议
- 从网文读者预期出发，评估以下维度：
  - 节奏控制、水文检测、逻辑问题
  - 爽点机会、情绪铺垫、战力崩坏
  - 设定冲突、角色一致性、对话/描写质量
- 每条建议含严重程度、问题描述、修改方向

### 4. 长期记忆
- 角色档案：名称、别名、角色定位、性格、势力归属
- 角色状态追踪：情绪、身体、战力、位置的时间线变化
- 势力关系：宗门/家族/帝国等势力的兴衰与互动
- 世界观与境界体系：修炼等级、世界规则
- 重大事件时间线
- 设定一致性检查：自动检测与已有设定的潜在冲突

### 5. 可视化数据接口
提供 REST API 获取 - 关系图数据、情绪曲线、角色出场频率、势力演变、时间线等结构化数据。

## 运行测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 全部测试
pytest -v
```

## 技术栈

- **后端**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- **数据库**: SQLite (可升级到 PostgreSQL)
- **前端**: Jinja2 模板 + 原生 JavaScript
- **AI 接入**: OpenAI SDK + Google Generative AI SDK
- **队列**: In-process (可升级到 Celery/Redis)

## 设计文档

详细设计请参阅 [docs/superpowers/specs/2026-05-28-cn-webnovel-ai-tool-design.md](docs/superpowers/specs/2026-05-28-cn-webnovel-ai-tool-design.md)
