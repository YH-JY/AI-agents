# Cloud-Native Attack Path Analysis Platform

This repository contains a Wiz-style cloud-native security graph prototype that
collects Kubernetes assets via kubeconfig, models relationships in Neo4j,
exposes attack-path search/Cypher APIs via FastAPI, and renders directed attack
graphs in React + Cytoscape.

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
# Wait for Neo4j, backend (8000), frontend (5173)
python scripts/import_sample_data.py --uri bolt://localhost:7687 --user neo4j --password neo4jpassword
```

Then open http://localhost:5173 to explore attack paths.

## Features

- **Kubernetes 资产采集**：在“资产采集”页上传 kubeconfig，选择全量/增量模式后即可触发 Collector。采集任务状态（队列/运行/成功/失败）及日志都会展示在页面上。
- **Neo4j 图谱写入**：Collector 将 Node/Pod/Container/ServiceAccount/Secret/Master/Credential/Volume 映射为 `Asset` 节点，并依据攻击技术枚举写入 `ATTACK_REL`。
- **攻击路径分析**：前端支持标准搜索、高价值目标（默认 Master/Credential）以及最短路径三种模式，路径图采用左→右 DAG 布局并可点击查看节点详情。
- **Cypher 控制台**：安全人员可直接执行只读 Cypher 查询（自动拦截包含 CREATE/MERGE 等写操作的语句），结果以图谱 + 表格双视图展示。
- **自定义查询**：资产列表可快速定位节点并触发路径计算；API 暴露 `/api/cypher/execute`、`/api/ingestion/*` 等接口供自动化集成。

## Kubernetes 采集步骤

1. 登录前端，切换到“资产采集”Tab。
2. 拖拽/选择 kubeconfig 文件上传（文件保存在 `storage/kubeconfigs`）。
3. 选择刚上传的配置，切换为全量或增量模式后点击“运行采集”。
4. 等待任务状态变为 `succeeded`，即可在“攻击路径”页依据实际资产计算路径。

## Windows 本地开发

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

确保 Neo4j 通过 Docker 启动或连接至远端实例；默认配置使用 `bolt://localhost:7687`。
