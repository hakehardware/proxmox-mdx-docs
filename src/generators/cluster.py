"""Cluster overview documentation generator."""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .base import BaseDocumentGenerator
from src.models import ClusterInfo

logger = logging.getLogger(__name__)


class ClusterOverviewGenerator(BaseDocumentGenerator):
    """Generator for cluster overview documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect cluster-wide data from API.

        Returns:
            Dictionary containing cluster information
        """
        try:
            # Get cluster status
            cluster_status = self.api.get_cluster_status()
            if not cluster_status:
                logger.error("Failed to fetch cluster status")
                return None

            # Get all resources
            resources = self.api.get_cluster_resources()
            if resources is None:
                logger.error("Failed to fetch cluster resources")
                return None

            # Get version info
            version_info = self.api.get_version()

            # Parse cluster status
            cluster_name = "Proxmox Cluster"
            quorum = False
            for item in cluster_status:
                if item.get('type') == 'cluster':
                    cluster_name = item.get('name', cluster_name)
                    quorum = item.get('quorum', 0) == 1

            # Count resources by type
            nodes = [r for r in resources if r.get('type') == 'node']
            vms = [r for r in resources if r.get('type') == 'qemu']
            containers = [r for r in resources if r.get('type') == 'lxc']
            storage_pools = [r for r in resources if r.get('type') == 'storage']

            # Count online/offline nodes
            online_nodes = sum(1 for n in nodes if n.get('status') == 'online')
            offline_nodes = len(nodes) - online_nodes

            # Build cluster info
            cluster_info = ClusterInfo(
                name=cluster_name,
                quorum=quorum,
                nodes=len(nodes),
                version=version_info.get('version') if version_info else None,
                total_vms=len(vms),
                total_containers=len(containers),
                online_nodes=online_nodes,
                offline_nodes=offline_nodes
            )

            # Prepare data for template
            return {
                'cluster': cluster_info,
                'nodes': nodes,
                'vms': vms,
                'containers': containers,
                'storage_pools': storage_pools,
                'version_info': version_info,
            }

        except Exception as e:
            logger.error(f"Error collecting cluster data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename.

        Returns:
            Template filename
        """
        return 'cluster_overview.j2'

    def get_output_path(self) -> Path:
        """Get output file path.

        Returns:
            Path to output file
        """
        return self.output_dir / 'index.mdx'
