from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

from kubernetes import client, config
from kubernetes.client import ApiException

from app.core.logger import logger
from app.ingestion.models import IngestionResult
from app.models.domain import (
    AssetNode,
    AttackEdge,
    AttackTechnique,
    NodeType,
)


class KubernetesCollector:
    def __init__(self, kubeconfig_path: Path, cluster_name: str):
        self.kubeconfig_path = kubeconfig_path
        self.cluster_name = cluster_name
        self.assets: Dict[str, AssetNode] = {}
        self.edges: list[AttackEdge] = []
        self.edge_keys: set[tuple[str, str, str]] = set()
        self.core_v1 = None

    def collect(self) -> IngestionResult:
        logger.info("Loading kubeconfig from %s", self.kubeconfig_path)
        config.load_kube_config(config_file=str(self.kubeconfig_path))
        self.core_v1 = client.CoreV1Api()

        self._collect_master()
        self._collect_nodes()
        self._collect_service_accounts()
        self._collect_secrets()
        self._collect_pods()

        return IngestionResult(
            assets=list(self.assets.values()),
            relationships=self.edges,
        )

    def _collect_master(self):
        master_id = self._build_id("master", None, "api-server")
        self._add_asset(
            AssetNode(
                id=master_id,
                type=NodeType.MASTER,
                name=f"{self.cluster_name}-master",
                namespace=None,
                criticality="HIGH",
                labels=[],
                metadata={"cluster": self.cluster_name},
                last_seen=datetime.utcnow(),
            )
        )

    def _collect_nodes(self):
        try:
            nodes = self.core_v1.list_node().items
        except ApiException as exc:
            logger.error("Failed to list nodes: %s", exc)
            return
        for node in nodes:
            metadata = node.metadata
            if not metadata:
                continue
            node_id = self._build_id("node", None, metadata.name)
            labels = _labels_to_list(metadata.labels)
            self._add_asset(
                AssetNode(
                    id=node_id,
                    type=NodeType.NODE,
                    name=metadata.name,
                    namespace=None,
                    criticality="MEDIUM",
                    labels=labels,
                    metadata={
                        "cluster": self.cluster_name,
                        "k8sUid": metadata.uid,
                        "kubeletVersion": node.status.node_info.kubelet_version
                        if node.status and node.status.node_info
                        else None,
                        "osImage": node.status.node_info.os_image
                        if node.status and node.status.node_info
                        else None,
                    },
                    last_seen=datetime.utcnow(),
                )
            )

    def _collect_service_accounts(self):
        try:
            sas = self.core_v1.list_service_account_for_all_namespaces().items
        except ApiException as exc:
            logger.error("Failed to list service accounts: %s", exc)
            return
        for sa in sas:
            metadata = sa.metadata
            if not metadata:
                continue
            sa_id = self._build_id("serviceaccount", metadata.namespace, metadata.name)
            labels = _labels_to_list(metadata.labels)
            self._add_asset(
                AssetNode(
                    id=sa_id,
                    type=NodeType.SERVICE_ACCOUNT,
                    name=metadata.name,
                    namespace=metadata.namespace,
                    criticality="MEDIUM",
                    labels=labels,
                    metadata={
                        "cluster": self.cluster_name,
                        "k8sUid": metadata.uid,
                        "secrets": [secret.name for secret in sa.secrets or []],
                    },
                    last_seen=datetime.utcnow(),
                )
            )

    def _collect_secrets(self):
        try:
            secrets = self.core_v1.list_secret_for_all_namespaces().items
        except ApiException as exc:
            logger.error("Failed to list secrets: %s", exc)
            return
        for secret in secrets:
            metadata = secret.metadata
            if not metadata:
                continue
            secret_id = self._build_id("secret", metadata.namespace, metadata.name)
            labels = _labels_to_list(metadata.labels)
            criticality = "HIGH" if secret.type == "kubernetes.io/service-account-token" else "MEDIUM"
            self._add_asset(
                AssetNode(
                    id=secret_id,
                    type=NodeType.SECRET,
                    name=metadata.name,
                    namespace=metadata.namespace,
                    criticality=criticality,
                    labels=labels,
                    metadata={
                        "cluster": self.cluster_name,
                        "k8sUid": metadata.uid,
                        "secretType": secret.type,
                    },
                    last_seen=datetime.utcnow(),
                )
            )
            if secret.type == "kubernetes.io/service-account-token":
                cred_id = f"{secret_id}:credential"
                self._add_asset(
                    AssetNode(
                        id=cred_id,
                        type=NodeType.CREDENTIAL,
                        name=f"{metadata.name}-credential",
                        namespace=metadata.namespace,
                        criticality="HIGH",
                        labels=[],
                        metadata={
                            "cluster": self.cluster_name,
                            "secret": metadata.name,
                        },
                        last_seen=datetime.utcnow(),
                    )
                )
                self._add_edge(
                    AttackEdge(
                        source=secret_id,
                        target=cred_id,
                        technique=AttackTechnique.CLUSTER_CREDS.value,
                        evidence="Service account token",
                        confidence=0.7,
                    )
                )
                master_id = self._build_id("master", None, "api-server")
                self._add_edge(
                    AttackEdge(
                        source=cred_id,
                        target=master_id,
                        technique=AttackTechnique.CLUSTER_CREDS.value,
                        evidence="Token to master access",
                        confidence=0.8,
                    )
                )

    def _collect_pods(self):
        try:
            pods = self.core_v1.list_pod_for_all_namespaces().items
        except ApiException as exc:
            logger.error("Failed to list pods: %s", exc)
            return
        for pod in pods:
            metadata = pod.metadata
            if not metadata:
                continue
            pod_id = self._build_id("pod", metadata.namespace, metadata.name)
            labels = _labels_to_list(metadata.labels)

            self._add_asset(
                AssetNode(
                    id=pod_id,
                    type=NodeType.POD,
                    name=metadata.name,
                    namespace=metadata.namespace,
                    criticality="MEDIUM",
                    labels=labels,
                    metadata={
                        "cluster": self.cluster_name,
                        "k8sUid": metadata.uid,
                        "nodeName": pod.spec.node_name if pod.spec else None,
                    },
                    last_seen=datetime.utcnow(),
                )
            )
            if pod.spec and pod.spec.node_name:
                node_id = self._build_id("node", None, pod.spec.node_name)
                self._add_edge(
                    AttackEdge(
                        source=node_id,
                        target=pod_id,
                        technique=AttackTechnique.ROOT_ACCESS.value,
                        evidence="Pod scheduled on node",
                        confidence=0.5,
                    )
                )
            if pod.spec and pod.spec.service_account_name:
                sa_id = self._build_id(
                    "serviceaccount", metadata.namespace, pod.spec.service_account_name
                )
                self._add_edge(
                    AttackEdge(
                        source=pod_id,
                        target=sa_id,
                        technique=AttackTechnique.PRIV_DISCOVERY.value,
                        evidence="ServiceAccount mounted",
                        confidence=0.6,
                    )
                )
            if pod.spec:
                for volume in pod.spec.volumes or []:
                    if volume.host_path:
                        volume_id = self._build_id(
                            "volume", metadata.namespace, f"{metadata.name}-{volume.name}"
                        )
                        self._add_asset(
                            AssetNode(
                                id=volume_id,
                                type=NodeType.VOLUME,
                                name=volume.name,
                                namespace=metadata.namespace,
                                criticality="MEDIUM",
                                labels=[],
                                metadata={
                                    "cluster": self.cluster_name,
                                    "hostPath": volume.host_path.path,
                                },
                                last_seen=datetime.utcnow(),
                            )
                        )
                        self._add_edge(
                            AttackEdge(
                                source=pod_id,
                                target=volume_id,
                                technique=AttackTechnique.MOUNT_DISCOVERY.value,
                                evidence=volume.host_path.path,
                                confidence=0.6,
                            )
                        )
                for container in (pod.spec.containers or []) + (pod.spec.init_containers or []):
                    container_id = self._build_id(
                        "container", metadata.namespace, f"{metadata.name}-{container.name}"
                    )
                    self._add_asset(
                        AssetNode(
                            id=container_id,
                            type=NodeType.CONTAINER,
                            name=container.name,
                            namespace=metadata.namespace,
                            criticality="MEDIUM",
                            labels=[],
                            metadata={
                                "cluster": self.cluster_name,
                                "image": container.image,
                            },
                            last_seen=datetime.utcnow(),
                        )
                    )
                    self._add_edge(
                        AttackEdge(
                            source=container_id,
                            target=pod_id,
                            technique=AttackTechnique.BELONGS_TO.value,
                            evidence="Container part of Pod",
                            confidence=0.9,
                        )
                    )

            if pod.spec and pod.spec.service_account_name and pod.metadata.namespace:
                sa_id = self._build_id(
                    "serviceaccount", pod.metadata.namespace, pod.spec.service_account_name
                )
                sa = self.assets.get(sa_id)
                if sa:
                    secrets = sa.metadata.get("secrets", [])
                    for secret_name in secrets:
                        secret_id = self._build_id("secret", pod.metadata.namespace, secret_name)
                        if secret_id in self.assets:
                            self._add_edge(
                                AttackEdge(
                                    source=sa_id,
                                    target=secret_id,
                                    technique=AttackTechnique.CLUSTER_CREDS.value,
                                    evidence="SA token secret",
                                    confidence=0.7,
                                )
                            )

    def _add_asset(self, asset: AssetNode):
        self.assets[asset.id] = asset

    def _add_edge(self, edge: AttackEdge):
        key = (edge.source, edge.target, str(edge.technique))
        if key in self.edge_keys:
            return
        self.edge_keys.add(key)
        self.edges.append(edge)

    def _build_id(self, resource: str, namespace: str | None, name: str) -> str:
        ns = namespace or "global"
        return f"{self.cluster_name}:{resource}:{ns}:{name}"


def _labels_to_list(labels: dict | None) -> list[str]:
    if not labels:
        return []
    return [f"{key}={value}" for key, value in labels.items()]
