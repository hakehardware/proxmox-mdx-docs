"""Container (LXC) documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDocumentGenerator
from src.models import Container
from src.utils import format_bytes, parse_tags, sanitize_filename

logger = logging.getLogger(__name__)


class ContainerIndexGenerator(BaseDocumentGenerator):
    """Generator for container index/list documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect all containers from cluster.

        Returns:
            Dictionary containing container list
        """
        try:
            # Get all resources and filter containers
            all_resources = self.api.get_cluster_resources()
            if all_resources is None:
                logger.error("Failed to fetch cluster resources")
                return None

            # Filter only LXC containers
            containers = [r for r in all_resources if r.get('type') == 'lxc']

            # Sort by node, then by vmid
            containers_sorted = sorted(containers, key=lambda x: (x.get('node', ''), x.get('vmid', 0)))

            # Group by node
            containers_by_node = {}
            for ct in containers_sorted:
                node = ct.get('node', 'unknown')
                if node not in containers_by_node:
                    containers_by_node[node] = []
                containers_by_node[node].append(ct)

            return {
                'containers': containers_sorted,
                'containers_by_node': containers_by_node,
                'total_containers': len(containers_sorted),
            }

        except Exception as e:
            logger.error(f"Error collecting container index data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'container_index.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'containers' / 'index.mdx'


class ContainerOverviewGenerator(BaseDocumentGenerator):
    """Generator for container overview documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str, vmid: int):
        """Initialize container overview generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Node where container is located
            vmid: Container ID
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name
        self.vmid = vmid

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect container overview data from API.

        Returns:
            Dictionary containing container information
        """
        try:
            # Get container configuration
            config = self.api.get_container_config(self.node_name, self.vmid)
            if not config:
                logger.error(f"Failed to fetch config for container {self.vmid}")
                return None

            # Extract basic info
            hostname = config.get('hostname', f'ct-{self.vmid}')
            description = config.get('description', '')

            # CPU and memory (in MB)
            cores = config.get('cores', 0)
            memory = config.get('memory', 0)
            swap = config.get('swap', 0)

            # OS info
            ostype = config.get('ostype', '')
            arch = config.get('arch', 'amd64')

            # Container type
            unprivileged = config.get('unprivileged', 1) == 1

            # Other settings
            onboot = config.get('onboot', 0) == 1
            protection = config.get('protection', 0) == 1

            # Tags
            tags = parse_tags(config.get('tags', ''))

            # Features (nesting, keyctl, fuse, etc.)
            features = {}
            features_str = config.get('features', '')
            if features_str:
                for feature in features_str.split(','):
                    if '=' in feature:
                        key, value = feature.split('=', 1)
                        features[key.strip()] = value.strip()

            # Parse rootfs
            rootfs = {}
            rootfs_str = config.get('rootfs', '')
            if rootfs_str:
                parts = rootfs_str.split(',')
                if ':' in parts[0]:
                    storage, volume = parts[0].split(':', 1)
                    rootfs['storage'] = storage
                    rootfs['volume'] = volume
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        rootfs[key] = value

            # Parse mount points
            mount_points = []
            for key, value in config.items():
                if key.startswith('mp') and key[2:].isdigit():
                    mp_num = key[2:]
                    mp_data = {'key': key, 'mp_num': mp_num}
                    parts = value.split(',')
                    if ':' in parts[0]:
                        storage, volume = parts[0].split(':', 1)
                        mp_data['storage'] = storage
                        mp_data['volume'] = volume
                    for part in parts[1:]:
                        if '=' in part:
                            k, v = part.split('=', 1)
                            mp_data[k] = v
                    mount_points.append(mp_data)

            # Build container model
            container = Container(
                vmid=self.vmid,
                hostname=hostname,
                node=self.node_name,
                description=description,
                cores=cores,
                memory=memory,
                swap=swap,
                ostype=ostype,
                arch=arch,
                unprivileged=unprivileged,
                onboot=onboot,
                protection=protection,
                tags=tags,
                rootfs=rootfs,
                mount_points=mount_points
            )

            return {
                'container': container,
                'config': config,
                'features': features,
            }

        except Exception as e:
            logger.error(f"Error collecting container overview data for {self.vmid}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'container_overview.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        # Get container hostname for directory
        config = self.api.get_container_config(self.node_name, self.vmid)
        hostname = config.get('hostname', 'container') if config else 'container'
        safe_name = sanitize_filename(hostname)

        return self.output_dir / 'containers' / f'{self.vmid}-{safe_name}' / 'overview.mdx'


class ContainerNetworkGenerator(BaseDocumentGenerator):
    """Generator for container network documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str, vmid: int):
        """Initialize container network generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Node where container is located
            vmid: Container ID
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name
        self.vmid = vmid

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect container network data from API.

        Returns:
            Dictionary containing network information
        """
        try:
            # Get container configuration
            config = self.api.get_container_config(self.node_name, self.vmid)
            if not config:
                logger.error(f"Failed to fetch config for container {self.vmid}")
                return None

            hostname = config.get('hostname', f'ct-{self.vmid}')

            # Parse network interfaces (net0, net1, etc.)
            network_interfaces = []
            for key, value in config.items():
                if key.startswith('net') and key[3:].isdigit():
                    iface_num = key[3:]
                    iface_data = {'interface': key, 'interface_num': iface_num}

                    # Parse network string
                    # Format: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1,hwaddr=AA:BB:CC:DD:EE:FF
                    parts = value.split(',')
                    for part in parts:
                        if '=' in part:
                            k, v = part.split('=', 1)
                            iface_data[k.strip()] = v.strip()

                    # Apply MAC address redaction
                    iface_data = self.redactor.redact_network_interface(iface_data)
                    network_interfaces.append(iface_data)

            # Sort by interface number
            network_interfaces.sort(key=lambda x: int(x.get('interface_num', 0)))

            # Try to get actual interfaces from container
            container_interfaces = None
            try:
                container_interfaces_raw = self.api.get(f'/nodes/{self.node_name}/lxc/{self.vmid}/interfaces')
                # Apply MAC address redaction to container interfaces
                if container_interfaces_raw:
                    container_interfaces = [self.redactor.redact_network_interface(iface) for iface in container_interfaces_raw]
            except:
                pass

            # Get firewall configuration
            firewall_rules = self.api.get(f'/nodes/{self.node_name}/lxc/{self.vmid}/firewall/rules')

            return {
                'hostname': hostname,
                'vmid': self.vmid,
                'node_name': self.node_name,
                'network_interfaces': network_interfaces,
                'container_interfaces': container_interfaces,
                'firewall_rules': firewall_rules if firewall_rules else [],
            }

        except Exception as e:
            logger.error(f"Error collecting container network data for {self.vmid}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'container_network.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        config = self.api.get_container_config(self.node_name, self.vmid)
        hostname = config.get('hostname', 'container') if config else 'container'
        safe_name = sanitize_filename(hostname)

        return self.output_dir / 'containers' / f'{self.vmid}-{safe_name}' / 'network.mdx'
