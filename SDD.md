# Cloud-Native Attack Path Analysis Platform – SDD

## Phase 1. Problem Definition & Goals
- **背景**：Kubernetes 资产高度动态，攻击往往跨越 Pod/节点/RBAC/Secrets/控制面；缺少统一图谱导致安全分析师难以回答“攻击如何发生”。  
- **挑战**：采集链路与图谱割裂、缺乏自动路径分析、自定义查询能力弱、部署体验复杂。  
- **目标**：  
  1. 通过上传 kubeconfig 的方式连接真实集群并采集 Node/Pod/Container/Volume/ServiceAccount/Secret/Master/Credential。  
  2. 将资产+权限+攻击关系标准化后写入 Neo4j，提供全量/增量同步。  
  3. 提供自动攻击路径（标准/高价值/最短）与自定义 Cypher 查询，返回有向、层级化且可解释的路径。  
  4. 前端以 Wiz 风格 DAG 呈现路径，并提供资产检索、采集任务跟踪与 Cypher 控制台。  
  5. 支持 Docker/docker-compose & Windows 本地运行，具备演进空间。

## Phase 2. Functional Specification
- **核心旅程**  
  - *资产采集*：上传 kubeconfig → 选择配置 → 运行全量/增量任务 → 监控状态 → Neo4j 更新。  
  - *路径探索*：设置起点/目标类型/模式（标准、高价值、最短）→ 计算路径 → 图谱展示 → 节点详情/导出。  
  - *自定义查询*：在 Cypher 控制台输入语句（只读白名单）→ 同时展示表格+图谱 → 支持模板快捷键。  
- **模块能力**  
  1. **K8s Collector**：基于 Kubernetes Python Client 分模块收集 Node/Pod/.../Secret，自动推导 Container、Volume、Credential 节点与攻击关系。  
  2. **Graph Writer**：Bolt 批写 Neo4j，提供 full-sync (清理 cluster 节点) 与 incremental。  
  3. **Attack Path 服务**：标准搜索、面向 Master/Credential 的高价值搜索、指定起止点的最短路径，若搜索为空可自动 fallback 到高价值路径。  
  4. **Cypher API**：`/api/cypher/execute` 支持只读查询，自动阻止 CREATE/MERGE/LOAD/DELETE 等语句，并将结果用于 Wiz 风格 DAG 渲染。  
  5. **前端子系统**：Tab 布局（攻击路径 / 资产采集 / Cypher 控制台）、资产统计卡片、路径卡片、Cytoscape DAG、资产检索、任务表格。  
- **验收标准**  
  - 上传 kubeconfig 后可在 2 分钟内完成 1k Pods 的全量写入；任务状态与日志实时更新。  
  - 攻击路径查询 ≤2s，并按模式返回对应路径集合。  
  - Cytoscape 图谱仅展示相关子图、方向清晰、节点颜色区分类型。  
  - Cypher 控制台禁止写操作且返回图+表。

## Phase 3. Non-Functional Requirements
- **性能**：Collector 吞吐≥500 nodes/s；Neo4j 查询 ≤2s；前端 DAG 200 nodes 60fps。  
- **可用性**：采集失败给出原因并可重试；健康检查 30s 调度；Cypher 错误提示友好。  
- **安全**：kubeconfig 仅存储本地 volume；API Key（可选）；Cypher API 仅读；日志不落 token。  
- **可靠性**：采集任务具备日志与状态机，Neo4j 断连自动重试；job store 支持欧性保留。  
- **可维护性**：FastAPI 分层（routers/services/repositories/ingestion），Collector 插件化；前端 Zustand 管状态。  
- **可观测性**：采集/写入日志、Neo4j 查询耗时、任务进度；Docker stdout。  
- **部署**：Docker + docker-compose（neo4j/backend/frontend + storage volume）；文档化 Windows 本地运行。

## Phase 4. Architecture Design
- **组件**  
  - *Backend FastAPI*：`ingestion` (registry/job store/collector/writer)、`graph` (attack path repo/service)、`cypher` 模块、资产 & 健康路由。  
  - *Kubernetes Collectors*：基于 kubeconfig 连接 CoreV1 API 收集资源→标准化 Asset/Edge。  
  - *Neo4j*：单实例 5.x，通过 Bolt 读写；节点 `Asset` + 子标签、边 `ATTACK_REL`。  
  - *Frontend SPA*：Ant Design + Cytoscape + Zustand + Axios。  
  - *Storage*：`storage/kubeconfigs`（映射为 docker volume）。  
- **数据流**  
  1. 上传 kubeconfig→写入本地→解析 metadata。  
  2. 运行任务→Collector 调 K8s API→生成 `IngestionResult`。  
  3. GraphWriter 批量 MERGE Neo4j 节点/关系（full/incremental）。  
  4. AttackPath / Cypher API 读取 Neo4j→返回 DTO→前端渲染 DAG。  
  5. 进度/日志通过内存 JobStore 暴露 REST。  
- **设计理由**：上传 kubeconfig 避免长连接；Collector & Writer 解耦；JobStore 轻量；前端 Tab 模式提升导航；Cypher API 做只读校验。

## Phase 5. Data Model & Graph Schema
- **节点**：`Asset` + `type`（Container/Pod/Volume/Node/ServiceAccount/Secret/Credential/Master），属性：`id`, `name`, `namespace`, `cluster`, `criticality`, `labels[]`, `lastSeen`, `meta_*`。  
- **关系**：`ATTACK_REL`，属性：`technique`（属于/挂载发现/根目录/横向移动/权限发现/RBAC权限利用/集群凭证获取/污点横向）、`evidence`, `confidence`, `sequence`, `discoveredAt`.  
- **约束**：`CREATE CONSTRAINT asset_id IF NOT EXISTS ON (n:Asset) ASSERT n.id IS UNIQUE`; 索引 `Asset(cluster, namespace, type)`、`REL(technique)`。  
- **映射规则**：  
  - Container→Pod = 属于；Pod→Volume(hostPath) = 挂载发现；Node→Pod = 根目录；Pod→ServiceAccount = 权限发现；ServiceAccount→Secret token = 集群凭证获取；Secret→Credential = 集群凭证获取；Credential→Master = 集群凭证获取。  
  - 补充 metadata：`cluster`, `k8sUid`, `image`, `hostPath` 等。

## Phase 6. API Specification
| Method | Path | 描述 |
| --- | --- | --- |
| POST | `/api/ingestion/kubeconfig` | 上传 kubeconfig，返回 `KubeConfigInfo` |
| GET | `/api/ingestion/configs` | 查询已上传配置 |
| POST | `/api/ingestion/run` | 启动采集 `{configId, mode(full/incremental)}` |
| GET | `/api/ingestion/jobs`/`/{id}` | 查看任务列表/详情 |
| POST | `/api/attack-paths/search` | 标准路径查询 |
| POST | `/api/attack-paths/high-value` | 针对目标类型列表（默认 Master/Credential） |
| POST | `/api/attack-paths/shortest` | 指定起止节点最短路径 |
| POST | `/api/cypher/execute` | 执行只读 Cypher，返回 nodes/edges |
| GET | `/api/assets`, `/api/assets/{id}` | 资产检索与详情 |
| GET | `/api/system/health` | Neo4j + 版本信息 |
- **安全**：全部接口可配置 `X-API-Key`；Cypher 请求在服务端阻断 CREATE/DELETE/MERGE/LOAD/CALL。  
- **错误**：采集/查询异常返回 4xx/5xx + 详细消息；Cypher 非法语句返回 400。

## Phase 7. Frontend Interaction & Visualization
- **结构**：Tabs（攻击路径 / 资产采集 / Cypher 控制台）。  
  - *攻击路径 Tab*: 左侧 FilterPanel（模式/起点/目标/namespace/maxDepth/limit），顶部资产统计卡片，右侧路径卡片 + Cytoscape DAG + AssetList + Path drawer。  
  - *资产采集 Tab*: Upload.Dragger + kubeconfig 列表（可选择并运行全量/增量模式）+ Job Table。  
  - *Cypher 控制台*: TextArea + 模板按钮 + 只读 Wiz 风格图谱（无表格）。  
- **可视化**：`breadthfirst` orientation=LR，节点颜色（Pod 蓝、Container 青、Secret 紫、Credential 黄、Master 红、Node 绿、ServiceAccount 橙、Volume 深紫），边 label=攻击技术；禁用力导向。  
- **交互**：  
  - 路径卡片点击高亮；节点点击打开详情抽屉。  
  - AssetList 点击将 asset.id 作为 startNodeId 重新查询。  
  - Cypher 结果 Graph 展示，与 Neo4j Browser 一致并提示节点/边数量。  
  - Job 列表 10s 轮询。  
- **状态**：Zustand 管理 filters/paths/loading/health；消息提示依托 Ant `message`。

## Phase 8. Implementation Summary
- **后端**  
  - `ingestion` 模块（`collectors.py`, `manager.py`, `writer.py`, `ingestion_service.py`）实现 kubeconfig 存储、任务状态机、Kubernetes Collector 与 Neo4j Writer。  
  - `attack_path_repository` 支持标准搜索、高价值筛选、最短路径；`attack_path_service` 暴露三类查询。  
  - `cypher_repository/service` 提供只读 Cypher 执行与节点/关系聚合；`/api/cypher/execute` 返回 Graph + table。  
  - `requirements.txt` 新增 kubernetes / PyYAML / python-multipart；`docker-compose` 为 backend 挂载 storage volume。  
- **前端**  
  - `App.tsx` 改为 Tab 布局；路径 Tab 含 FilterPanel、资产统计卡片、AttackGraph 与 AssetList；资产采集 Tab (`IngestionPanel`) 管理上传/任务；Cypher Tab (`CypherConsole` + `CypherGraph`) 仅返回 DAG。  
  - Filter 支持查询模式 (standard/highValue/shortest)、目标节点 ID、目标类型列表。  
  - 新服务函数：采集 API、Custom Cypher、Shortest/High-Value path 查询。  
  - 样式更新：`.app-shell-vertical`, `.path-layout`, `.path-card` 等保障布局。  
- **工具**：`scripts/import_sample_data.py` 扁平化 metadata 并写入 cluster 属性；`.gitignore` 忽略 storage/venv。

## Phase 9. Deployment & Runbook
1. `cp .env.example .env`，如需自定义 `STORAGE_DIR/KUBECONFIG_DIR`、Neo4j 凭据或 API Key 请同步编辑。  
2. `docker-compose up --build`：启动 Neo4j、FastAPI（含 storage 卷）、React dev server。  
3. 访问 `http://localhost:5173`：在“资产采集”Tab 上传 kubeconfig → 运行采集 → 查看任务状态。  
4. 返回“攻击路径”Tab，根据查询模式计算路径；若尚未有真实数据，可运行 `python scripts/import_sample_data.py` 导入示例。  
5. “Cypher 控制台”Tab 输入只读查询（如 `MATCH path=(s:Asset)-[:ATTACK_REL*1..4]->(t:Asset {type:'Master'}) RETURN path LIMIT 3`）。  
6. Windows 本地调试：`cd backend && python -m venv .venv && .\.venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload`；`cd frontend && npm install && npm run dev`。确保 Neo4j Docker 在本机运行或更新 `.env` 指向远端。  
7. 故障排除：  
   - 后端日志：`docker logs attack-backend` 或本地终端。  
   - 采集失败：`/api/ingestion/jobs/{id}` 查看 `logs`。  
   - Neo4j 连通性：`/api/system/health` 或访问 Neo4j Browser `http://localhost:7474`。  
   - Cypher API 拒绝：检查语句是否含 CREATE/MERGE/LOAD/CALL/DELETE。
