import argparse
import json
from pathlib import Path

from neo4j import GraphDatabase, basic_auth


def load_data(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def import_data(uri: str, user: str, password: str, payload: dict):
    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    with driver.session() as session:
        for node in payload["nodes"]:
            labels = ":".join(["Asset", node["type"]])
            props = {k: v for k, v in node.items() if k not in {"type"}}
            session.run(
                f"""
                MERGE (n:{labels} {{id: $id}})
                SET n.name = $name,
                    n.namespace = $namespace,
                    n.criticality = $criticality,
                    n.labels = $labels,
                    n.metadata = $metadata,
                    n.type = $type
                """,
                {
                    "id": node["id"],
                    "name": node["name"],
                    "namespace": node.get("namespace"),
                    "criticality": node.get("criticality", "MEDIUM"),
                    "labels": node.get("labels", []),
                    "metadata": node.get("metadata", {}),
                    "type": node["type"],
                },
            )
        for rel in payload["relationships"]:
            session.run(
                """
                MATCH (src:Asset {id: $source}), (dst:Asset {id: $target})
                MERGE (src)-[r:ATTACK_REL]->(dst)
                SET r.technique = $technique,
                    r.evidence = $evidence,
                    r.confidence = $confidence,
                    r.sequence = $sequence
                """,
                rel,
            )
    driver.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import sample attack graph data into Neo4j"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/sample_attack_graph.json"),
        help="Path to data file",
    )
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", default="neo4jpassword")
    args = parser.parse_args()

    payload = load_data(args.file)
    import_data(args.uri, args.user, args.password, payload)
    print("Import completed")


if __name__ == "__main__":
    main()
