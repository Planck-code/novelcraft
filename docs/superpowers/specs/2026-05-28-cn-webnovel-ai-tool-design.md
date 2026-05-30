# 中文网络小说作者 AI 辅助分析工具设计文档

## 1. 概述

本文档定义一个面向中文网络小说作者的 AI 辅助分析工具的一期设计方案。一期目标聚焦于 `分析优先` 的本地单机 MVP，采用 `Python + FastAPI + Web 前端` 的技术路线，重点交付以下能力：

- 支持 `txt` 文件上传、清洗、自动切章与章节标题识别
- 对单章生成结构化分析结果与修改建议
- 建立可持续更新的长期记忆中心
- 提供后续可视化、RAG、向量数据库、多 Agent 扩展所需的稳定架构边界

非目标：

- 一期不做多用户 SaaS
- 一期不做复杂微服务拆分
- 一期不以重型自治式 Agent 框架为核心
- 一期不强依赖向量数据库

## 2. 产品范围

### 2.1 一期范围

- 本地单机运行
- 单用户通过网页创建小说项目并上传 `txt`
- 自动识别章节标题并按章节切分
- 对章节执行结构化分析
- 生成写作修改建议
- 保存人物、世界观、势力、境界体系、重要事件等长期记忆
- 提供后续可视化所需的结构化数据接口
- 接入统一 LLM Provider 层，兼容 OpenAI、DeepSeek、Gemini

### 2.2 二期方向

- 人物关系图、时间线、情绪曲线等完整可视化页面增强
- RAG 与向量数据库接入
- 更灵活的多 Agent 编排
- PostgreSQL 和云端部署支持
- 多用户与账号隔离

## 3. 总体架构

### 3.1 架构风格

系统采用 `模块化单体 + 异步任务队列`。

原因如下：

- 比纯同步单体更适合长文本分析
- 比微服务更适合本地单机 MVP
- 能在不推翻代码结构的前提下接入 RAG、向量库和多 Agent

### 3.2 分层结构

- `Presentation Layer`
  - 网页路由、API、文件上传、任务状态查询、结果展示
- `Application Layer`
  - 编排导入、分析、记忆更新、可视化聚合等用例
- `Domain Layer`
  - 定义小说、章节、人物、事件、关系、设定等核心业务对象和规则
- `Infrastructure Layer`
  - 数据库、文件存储、LLM provider、任务执行器、向量库适配器、日志
- `Agent/Workflow Layer`
  - 定义轻量 Agent 和工作流编排逻辑

### 3.3 核心原则

- `结构化优先`：模型结果优先转成结构化数据
- `上下文收敛`：按任务选择最小必要上下文，不直接喂整本历史
- `任务可重跑`：导入、分析、记忆更新都支持重试
- `模型可替换`：上层只依赖统一 provider 接口
- `扩展点前置`：为向量库、RAG、多 Agent 预留接口，但一期实现保持克制

## 4. 模块划分

### 4.1 业务模块

- `novel_import`
  - 负责 txt 上传、编码识别、文本清洗、标题识别、章节切分
- `chapter_analysis`
  - 负责本章剧情总结、关键事件、人物出场、关系变化、情绪变化、冲突分析、世界观新增、伏笔识别
- `revision_advice`
  - 负责节奏、水文、逻辑、爽点、情绪铺垫、战力崩坏、设定冲突等修改建议
- `memory_center`
  - 负责人物档案、世界观、势力关系、境界体系、重大事件等长期记忆的更新与检索
- `visualization`
  - 负责聚合人物关系图、章节情绪曲线、时间线、出场频率等图表数据
- `project_management`
  - 负责小说项目管理

### 4.2 技术模块

- `llm_gateway`
  - 统一适配 OpenAI、DeepSeek、Gemini
- `workflow_engine`
  - 编排导入、章节分析、记忆更新、批量分析流程
- `vector_adapter`
  - 一期提供抽象接口，后续可接向量数据库
- `storage`
  - 负责原始文件、正文快照、模型原始响应等文件存储
- `queue`
  - 负责异步任务执行

## 5. 推荐文件结构

推荐目录结构如下：

```text
novelcraft/
├─ app/
│  ├─ main.py
│  ├─ config/
│  ├─ api/
│  ├─ schemas/
│  ├─ domain/
│  ├─ modules/
│  ├─ workflows/
│  ├─ agents/
│  ├─ llm/
│  ├─ infra/
│  ├─ web/
│  └─ common/
├─ data/
│  ├─ uploads/
│  ├─ novels/
│  ├─ analysis_cache/
│  ├─ exports/
│  └─ logs/
├─ prompts/
│  ├─ system/
│  ├─ chapter_analysis/
│  ├─ revision_advice/
│  ├─ memory_update/
│  └─ consistency_check/
├─ scripts/
├─ tests/
├─ docs/
├─ requirements.txt
├─ .env.example
└─ README.md
```

目录设计原则：

- `api` 只处理请求和响应，不承载业务逻辑
- `modules` 以业务能力为边界
- `domain` 放纯业务规则和实体
- `workflows` 专注流程编排
- `agents` 作为能力单元，与工作流解耦
- `llm` 独立管理模型接入与输出解析
- `infra` 隔离数据库、文件、队列等技术细节
- `prompts` 独立存储，便于版本化与调优

## 6. 关键数据流

### 6.1 小说导入流

1. 用户创建小说项目并上传 `txt`
2. 系统保存原始文件到 `data/uploads/`
3. `novel_import` 执行编码识别、文本清洗、标题识别和自动切章
4. 将小说信息写入 `novels`
5. 将章节索引写入 `chapters`
6. 将清洗结果和切章缓存落到 `data/novels/{novel_id}/`

### 6.2 章节分析流

1. 用户对单章或多章发起分析
2. API 创建一条分析任务记录到 `tasks`
3. 后台队列执行 `chapter_analysis_workflow`
4. 工作流读取章节正文和相关长期记忆
5. 工作流调用多个 Agent 或分析子任务
6. 将主分析结果写入 `chapter_analyses`
7. 将事件、人物出场、情绪变化等拆分结果写入对应明细表
8. 触发记忆更新流程

### 6.3 修改建议流

1. 读取章节正文
2. 读取本章结构化分析结果
3. 读取相关长期记忆与前文摘要
4. 调用修改建议 Prompt
5. 将分类建议写入 `revision_suggestions`

### 6.4 长期记忆流

1. 从本章分析结果中抽取新增事实
2. 更新人物档案、人物状态、关系变化
3. 更新世界观、势力关系、境界体系
4. 追加全书级重大事件时间线
5. 将来源章节写入追溯字段
6. 若发现冲突，写入 `consistency_issues`

### 6.5 可视化聚合流

1. 从结构化分析结果与长期记忆中读取数据
2. 聚合出关系图、情绪曲线、出场频率、势力变化、时间线数据
3. 按需缓存到 `visualization_cache`
4. 前端读取聚合结果并渲染图表

## 7. 数据库存储设计

### 7.1 技术选型

- 数据库：`SQLite`
- ORM：`SQLAlchemy`
- 迁移工具：后续建议引入 `Alembic`

### 7.2 主表

- `novels`
  - 小说项目主表
- `chapters`
  - 切章后的章节索引
- `tasks`
  - 导入、分析、记忆更新、批量分析任务表
- `chapter_analyses`
  - 章节主分析结果表
- `revision_suggestions`
  - 分类修改建议表

### 7.3 分析明细表

- `chapter_events`
  - 本章关键事件
- `chapter_character_mentions`
  - 本章出场人物、角色定位、行为与情绪
- `chapter_emotion_arcs`
  - 章节情绪分段变化
- `chapter_world_deltas`
  - 本章新增世界观信息
- `chapter_foreshadowings`
  - 伏笔与回收记录

### 7.4 长期记忆表

- `characters`
- `character_states`
- `character_relations`
- `factions`
- `faction_relations`
- `world_settings`
- `realm_systems`
- `timeline_events`

### 7.5 追溯与一致性

- `memory_claims`
  - 保存模型提取出的原子事实，便于追溯和未来检索增强
- `consistency_issues`
  - 保存设定冲突、战力冲突、行为冲突等问题

### 7.6 缓存表

- `visualization_cache`

### 7.7 结构化与 JSON 的边界

应结构化存储的内容：

- 高频筛选、统计、关联查询字段
- 人物关系、章节索引、事件时间线、势力关系、任务状态

适合 JSON 存储的内容：

- 模型复杂嵌套输出
- 调试快照
- 任务参数与结果快照
- 别名列表和弱结构化配置

判断标准：

- 需要 `where / join / group by` 的字段优先结构化
- 主要用于保留原貌与调试的复杂结构用 JSON

## 8. Prompt 工程方案

### 8.1 五层设计

- `System Prompt`
  - 固定角色、原则和禁止事项
- `Task Prompt`
  - 定义当前任务目标和输出要求
- `Context Prompt`
  - 注入章节文本、角色摘要、世界观摘要、前文摘要
- `Output Contract`
  - 使用 JSON Schema 风格约束输出结构
- `Post Check Prompt`
  - 在输出不合法或关键字段缺失时执行修复

### 8.2 Prompt 拆分

- `chapter_analysis_v1`
  - 负责章节整体理解
- `character_relation_extract_v1`
  - 负责人物状态与关系抽取
- `revision_advice_v1`
  - 负责写作质量建议
- `memory_update_v1`
  - 负责长期记忆更新
- `consistency_check_v1`
  - 负责历史一致性检查

### 8.3 上下文注入策略

每次只注入最小必要上下文：

- `chapter_meta`
- `current_text`
- `recent_context`
- `character_context`
- `world_context`
- `memory_focus`

一期先采用规则召回和 SQL 聚合。未来接入 RAG 时，只替换上下文构建器，不改上层 Prompt 接口。

### 8.4 中文网文专用约束

- 不把修辞夸张自动当成客观事实
- 不把角色猜测自动当成设定
- 不把一时情绪自动当成稳定性格
- 不把对话吹嘘自动当成战力结论
- 判断爽点、水文、节奏时以中文网文阅读预期为准

### 8.5 版本管理

每次分析结果都记录：

- `prompt_name`
- `prompt_version`
- `provider_name`
- `model_name`
- `schema_version`

## 9. Agent 分工设计

### 9.1 设计原则

一期采用 `可编排的轻量 Agent`，而不是重型自治式多 Agent。

原则如下：

- `Agent` 只做单一分析目标
- `Workflow` 决定调用顺序和重试策略
- `Memory Center` 提供共享长期记忆
- `LLM Gateway` 提供统一模型调用

### 9.2 推荐 Agent

- `Chapter Summary Agent`
  - 负责剧情总结和关键事件抽取
- `Character State Agent`
  - 负责人物出场、行为轨迹、情绪状态、状态变化
- `Relationship Agent`
  - 负责人物关系和势力互动变化
- `Worldbuilding Agent`
  - 负责世界观设定与境界体系变化
- `Foreshadowing Agent`
  - 负责伏笔与回收识别
- `Revision Advice Agent`
  - 负责写作问题与修改建议
- `Consistency Review Agent`
  - 负责对照长期记忆检查冲突
- `Memory Update Agent`
  - 负责把本章新增事实合并进长期记忆

### 9.3 一期最小 Agent 集合

- `Chapter Summary Agent`
- `Character State Agent`
- `Worldbuilding Agent`
- `Revision Advice Agent`
- `Memory Update Agent`

简化策略：

- `Relationship Agent` 一期可并入人物状态抽取或以规则补充
- `Consistency Review Agent` 一期可采用规则和 Prompt 混合
- `Foreshadowing Agent` 一期可先并入章节分析输出

### 9.4 一期执行顺序

1. `Chapter Summary Agent`
2. `Character State Agent`
3. `Worldbuilding Agent`
4. 关系与伏笔的补充提取
5. 聚合形成统一分析结果
6. `Revision Advice Agent`
7. `Memory Update Agent`
8. 必要时执行一致性检查

## 10. 错误处理与重试

### 10.1 导入阶段

- 编码识别失败时保留原始文件和错误日志
- 切章异常时允许重新切章

### 10.2 分析阶段

- 模型调用失败时标记任务失败并允许重试
- JSON 解析失败时保留原始响应并进入结构修复流程
- 关键字段缺失时进入内容补全流程

### 10.3 记忆更新阶段

- 若长期记忆更新失败，不回滚章节分析主结果
- 将章节标记为 `memory_sync_pending`

### 10.4 可视化阶段

- 图表聚合失败不影响分析主结果
- 可单独重建缓存

### 10.5 任务状态

- `pending`
- `running`
- `success`
- `failed`
- `partial_success`
- `needs_review`

## 11. 测试策略

### 11.1 单元测试

- 章节标题识别与切章规则
- 输出解析器和 JSON 校验器
- 长期记忆合并与冲突检测规则
- Prompt 上下文构建器

### 11.2 集成测试

- 文件上传到入库的导入链路
- 单章分析工作流
- 修改建议写回链路
- 记忆更新链路

### 11.3 手工验证

- 使用真实中文网文章节样本验证切章准确性
- 分别验证日常章、战斗章、情绪章、设定章的分析质量
- 比较不同 provider 的输出稳定性

## 12. 技术选型建议

- 后端：`FastAPI`
- 数据库：`SQLite`
- ORM：`SQLAlchemy`
- 前端：一期优先 `FastAPI Web 页面 + API`
- 队列：一期可先用 `in-process queue`，后续升级
- 向量库：一期预留接口，后续可接 `Qdrant` 或同类方案

## 13. 实施顺序建议

### Phase 1

- 初始化 FastAPI 项目骨架
- 建立配置、数据库连接、基础页面
- 完成 `novels / chapters / tasks / chapter_analyses` 主链路

### Phase 2

- 完成 txt 导入、清洗、自动切章
- 接入统一 LLM Provider
- 打通单章分析流程

### Phase 3

- 完成修改建议模块
- 建立人物、关系、世界观、时间线等长期记忆表
- 打通记忆更新工作流

### Phase 4

- 补充基础可视化数据接口
- 增加批量分析、重试与缓存
- 为 RAG 和向量检索预留实现位

## 14. 已确认结论

- 一期范围：`分析优先`
- 运行方式：`本地单机`
- 存储方案：`SQLite + 文件目录`
- 模型接入：`统一适配层`
- 架构路线：`模块化单体 + 异步任务队列`

## 15. 风险与后续关注点

- 中文网文章节标题格式多样，切章规则需要真实语料反复校正
- 不同模型在 JSON 输出稳定性上差异较大，需要输出修复链路
- 长期记忆合并存在“别名、多称呼、误判事实”的风险，需要追溯字段
- 一期先不要过度追求复杂 Agent 自治，先保证链路稳定

## 16. 结论

本方案适合作为中文网络小说作者 AI 辅助分析工具的一期基础架构。它优先保证：

- 快速形成可运行 MVP
- 长文本分析过程可控
- 长期记忆可持续积累
- 对后续 RAG、向量检索、多 Agent 协作和云端部署具备兼容性

后续实现阶段应严格按模块边界推进，先完成导入、分析、记忆三条主链，再逐步增强可视化和高级编排能力。
