import argparse
import json
from pathlib import Path

from neo4j import GraphDatabase, basic_auth


def normalize_properties(node: dict) -> dict:
    metadata = node.get("metadata", {})
    flattened = {f"meta_{key}": value for key, value in metadata.items()}
    return {
        "id": node["id"],
        "name": node.get("name"),
        "namespace": node.get("namespace"),
        "criticality": node.get("criticality", "MEDIUM"),
        "labels": node.get("labels", []),
        "type": node["type"],
        **flattened,
    }


def load_data(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def import_data(uri: str, user: str, password: str, payload: dict):
    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    with driver.session() as session:
        for node in payload["nodes"]:
            labels = ":".join(["Asset", node["type"]])
            props = normalize_properties(node)
            session.run(
                f"""
                MERGE (n:{labels} {{id: $id}})
                SET n += $props
                """,
                {"props": props, "id": node["id"]},
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
