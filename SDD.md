# Cloud-Native Attack Path Analysis Platform – Specification Driven Development

## Phase 1. Problem Definition & Goals
- **Context**: Kubernetes / 云原生资产数量与权限组合爆炸，传统面板无法回答“攻击如何逐跳推进”。
- **Pain Points**: 跨容器/Secret/ServiceAccount/云凭证之间的攻击链难以识别，缺乏统一图谱与可解释路径。
- **Users**: 安全分析师、平台安全负责人、SOC 团队。
- **Goals**:
  1. 将云原生资产、权限与攻击关系建模到 Neo4j 图谱。
  2. 自动计算可解释、有向的攻击路径并量化风险。
  3. 以前端可视化呈现“左→右、层级化”的攻击推进过程。
  4. 可在本地 Windows + Docker 环境一键部署演示。

## Phase 2. Functional Specification
- **User Journeys**
  - *攻击路径探索*: 输入起点或类型→后端 Cypher→前端渲染层级路径、点击节点查看属性。
  - *资产检索*: 按名称/类型/namespace 检索节点→查看关联→发起子图可视化。
  - *威胁优先级*: 路径评分排序，列表展示 Top Paths 并可跳转图谱。
- **Modules**
  1. 资产/关系入图 (JSON 导入 + 去重标准化)。
  2. 攻击路径计算 API `/api/attack-paths/search`（filters: startNodeId/startType/targetType/namespace/maxDepth/limit）。
  3. 图谱可视化：React + Cytoscape `breadthfirst` 左→右布局，节点颜色区分类型，边显示技术。
  4. 洞察面板：风险分、关键节点摘要、导出 JSON。
  5. 健康监测：`/api/system/health` 周期调用。
- **Acceptance**
  - 3s 内返回存在路径；每条边展示攻击技术；Neo4j 异常时前端告警；非法过滤条件 400。

## Phase 3. Non-Functional Requirements
- **Performance**: 单路径查询 ≤2s (≤5万节点)；前端渲染≤200 nodes/400 edges ≥40fps。
- **Availability**: 健康接口 30s 轮询；错误提示友好。
- **Security**: 只读 Neo4j 账号、配置走环境变量、日志脱敏凭证。
- **Maintainability**: FastAPI 分层 (routers/services/repositories)，前端 Zustand store；代码有轻量注释。
- **Observability**: 记录请求耗时和 Cypher 执行时间；Docker stdout 日志。
- **Deployment**: docker-compose 一键启动；`.env` 管理配置。

## Phase 4. Architecture Design
- **Components**
  - React 前端：FilterPanel、AssetList、AttackGraph、HealthIndicator、PathSummaryDrawer。
  - FastAPI 后端：routers → services → repositories → Neo4j 驱动。
  - Neo4j 数据库：资产节点 + ATTACK_REL。
  - Import 脚本：JSON → Neo4j MERGE。
  - docker-compose：neo4j + backend + frontend。
- **Data Flow**: 前端提交过滤→FastAPI service 调用 repository→Neo4j 返回路径→服务层转 AttackStep→前端 Cytoscape 显示。
- **Rationale**: 清晰分层便于扩展；Cytoscape breadthfirst 满足定向布局；docker-compose 满足本地演示。

## Phase 5. Data Model & Graph Schema
- **Node Base Properties**: `id`, `type`, `name`, `namespace`, `criticality (LOW/MEDIUM/HIGH)`, `labels[]`, `lastSeen`, `metadata{}`。
- **Type-specific Metadata**: Container(image,nodeName), Pod(workloadType,cluster), ServiceAccount(roles[]), Secret(secretType), Credential(provider,scope), Node(os,kubeletVersion), Master(apiServerVersion), Volume(storageClass)。
- **Relations**: label `ATTACK_REL` with properties `technique` (属于/挂载发现/根目录/横向移动/权限发现/RBAC权限利用/集群凭证获取/污点横向), `evidence`, `confidence`, `sequence`。
- **Constraints & Indexes**: `CREATE CONSTRAINT asset_id IF NOT EXISTS ON (n:Asset) ASSERT n.id IS UNIQUE`; composite index `(Asset {type,name,namespace})`; optional `technique` index on relationships。

## Phase 6. API Specification
| Method | Path | Description | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/system/health` | Neo4j 状态 | – | `{ neo4j, version, timestamp }` |
| POST | `/api/attack-paths/search` | 计算攻击路径 | `{ startNodeId?, startType?, targetType?, namespace?, maxDepth≤8, limit≤20 }` (至少提供起点) | `{ paths:[{id,score,summary,steps[{depth,nodes[],edges[]}]}] }` |
| GET | `/api/assets` | 分页资产列表 | `type?, namespace?, search?, page, pageSize` | `{ items[], total, page, pageSize }` |
| GET | `/api/assets/{id}` | 节点详情 | – | `{ node, inbound_edges[], outbound_edges[] }` |
| POST | `/api/attack-paths/export` | (前端离线导出实现) | 同 search | JSON 下载 |
- **Auth**: 可选 `X-API-Key` header (`ENABLE_API_KEY` true 时强制)。
- **Errors**: 400/422 输入错误，500 包含 trace id。

## Phase 7. Frontend Interaction & Visualization
- **Layout**: 左侧过滤与资产检索、右上健康灯、右侧资产列表、主画布 Cytoscape `breadthfirst orientation=LR`、底部抽屉显示路径详情。
- **States**: Zustand store 管理 `filters/paths/loading/selectedPathId/selectedNodeId/health`。
- **Node Styles**: 颜色映射 (Pod 蓝、Container 青、Secret 紫、Credential 黄、Master 红等)；圆角方/菱形通过 Cytoscape 数据 hook 预留扩展。
- **Edges**: 箭头指向下一 hop，label 为攻击技术，hover tooltip 显示 evidence。
- **Interactions**: 过滤提交→API→loading；卡片切换路径→graph refit；node tap→侧 panel；资产列表点击→以该资产为起点重新算路径；健康灯可手动刷新。

## Phase 8. Implementation Summary
- **Backend (FastAPI)**
  - `app/config.py` 统一环境配置；`core/logger.py` 输出结构化日志。
  - `models/domain.py` 定义 NodeType/AttackTechnique/DTOs（含 root validator 强制 start filter）。
  - `repositories/neo4j_client.py` 封装 Neo4j 驱动；`attack_path_repository.py` 生成 Cypher + Score 逻辑；`asset_repository.py` 提供分页和详情。
  - `services/*` 组织业务；`routers/*` 暴露 REST；`dependencies.py` 预留 API Key 验证。
  - Dockerfile + `requirements.txt` 提供可部署镜像。
- **Frontend (React + TS + Cytoscape + AntD)**
  - Vite 工程 (`package.json`, `tsconfig*`, `vite.config.ts`)；`useAttackStore.ts` 管理全局状态。
  - 组件：FilterPanel（表单→调用 onSearch）、AssetList（检索资产）、HealthIndicator（Badge+刷新）、AttackGraph（Cytoscape directed layout）、PathSummaryDrawer（评分+导出按钮）。
  - `App.tsx` 组合流程、卡片化路径列表与空态/加载处理。
  - `services/api.ts` 基于 Axios 调用 FastAPI；`.env` 中可设置 `VITE_API_URL`。
- **Data & Tooling**
  - `data/sample_attack_graph.json` 示例多跳路径。
  - `scripts/import_sample_data.py` 可指定文件/连接导入 Neo4j。

## Phase 9. Deployment & Runbook
1. `cp .env.example .env` 并根据需要调整 Neo4j/Bolt/ApiKey 配置。
2. 启动：`docker-compose up --build`（包含 Neo4j:5.19, FastAPI, React dev server）。
3. 数据导入：`python scripts/import_sample_data.py --uri bolt://localhost:7687 --user neo4j --password neo4jpassword`。
4. 访问 `http://localhost:5173` 使用前端；`http://localhost:8000/docs` 查看 API。
5. 健康排障：若前端健康灯红色→检查 Neo4j 容器日志或 `.env` 凭据；可运行 `docker logs attack-backend` 查看服务日志。
6. Windows 开发机直接运行：安装 Node 20、Python 3.11，`cd backend && uvicorn app.main:app --reload`、`cd frontend && npm install && npm run dev`，Neo4j Docker 保持启动即可。

