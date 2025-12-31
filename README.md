# Cloud-Native Attack Path Analysis Platform

This repository contains a Wiz-style cloud-native security graph prototype that
models Kubernetes assets in Neo4j, exposes attack-path search APIs via FastAPI,
and renders directed attack graphs in React + Cytoscape.

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
# Wait for Neo4j, backend (8000), frontend (5173)
python scripts/import_sample_data.py --uri bolt://localhost:7687 --user neo4j --password neo4jpassword
```

Then open http://localhost:5173 to explore attack paths.
