"""Node documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDocumentGenerator
from src.models import NodeInfo
from src.utils import format_bytes, format_memory_mb, sanitize_filename

logger = logging.getLogger(__name__)


class NodeOverviewGenerator(BaseDocumentGenerator):
    """Generator for node overview documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str):
        """Initialize node overview generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Name of the node to document
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect node overview data from API.

        Returns:
            Dictionary containing node information
        """
        try:
            # Get node configuration (includes description/notes)
            config = self.api.get_node_config(self.node_name)
            if config is None:
                logger.warning(f"Could not fetch config for node {self.node_name}, using empty config")
                config = {}

            # Get node status (hardware info)
            status = self.api.get_node_status(self.node_name)
            if not status:
                logger.error(f"Failed to fetch status for node {self.node_name}")
                return None

            # Get version info
            version = self.api.get_node_version(self.node_name)

            # Get storage pools on this node
            storage = self.api.get_node_storage(self.node_name)

            # Get network interfaces
            network = self.api.get_node_network(self.node_name)

            # Extract CPU info
            cpu_info = status.get('cpuinfo', {})
            cpu_model = cpu_info.get('model', 'N/A')
            cpu_sockets = cpu_info.get('sockets', 0)
            cpu_cores_per_socket = cpu_info.get('cores', 0)
            total_cores = cpu_info.get('cpus', 0)

            # Extract memory info
            memory_info = status.get('memory', {})
            total_memory = memory_info.get('total', 0)

            # Extract root filesystem info
            rootfs = status.get('rootfs', {})
            rootfs_total = rootfs.get('total', 0)
            rootfs_used = rootfs.get('used', 0)

            # Build node info
            node_info = NodeInfo(
                name=self.node_name,
                status='online',  # If we can fetch it, it's online
                description=config.get('description'),
                cpu_model=cpu_model,
                cpu_sockets=cpu_sockets,
                cpu_cores=cpu_cores_per_socket,
                total_cpu_cores=total_cores,
                total_memory=total_memory,
                pve_version=version.get('version') if version else None,
                kernel_version=status.get('kversion'),
                storage_pools=storage if storage else [],
                network_interfaces=network if network else []
            )

            # Get VMs and containers on this node
            all_resources = self.api.get_cluster_resources()
            vms_on_node = [
                r for r in all_resources
                if r.get('type') == 'qemu' and r.get('node') == self.node_name
            ] if all_resources else []

            containers_on_node = [
                r for r in all_resources
                if r.get('type') == 'lxc' and r.get('node') == self.node_name
            ] if all_resources else []

            return {
                'node': node_info,
                'status_data': status,
                'version_data': version,
                'storage_pools': storage if storage else [],
                'network_interfaces': network if network else [],
                'vms': vms_on_node,
                'containers': containers_on_node,
                'rootfs_total': rootfs_total,
                'rootfs_used': rootfs_used,
                'rootfs_free': rootfs.get('free', 0) or rootfs.get('avail', 0),
            }

        except Exception as e:
            logger.error(f"Error collecting node overview data for {self.node_name}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'node_overview.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        safe_name = sanitize_filename(self.node_name)
        return self.output_dir / 'nodes' / safe_name / 'overview.mdx'


class NodeHardwareGenerator(BaseDocumentGenerator):
    """Generator for node hardware documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str):
        """Initialize node hardware generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Name of the node to document
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect node hardware data from API.

        Returns:
            Dictionary containing hardware information
        """
        try:
            # Get node status (includes hardware info)
            status = self.api.get_node_status(self.node_name)
            if not status:
                logger.error(f"Failed to fetch status for node {self.node_name}")
                return None

            # Try to get disk information
            disks = self.api.get('/nodes/{}/disks/list'.format(self.node_name))

            # Try to get PCI devices
            pci_devices = self.api.get('/nodes/{}/hardware/pci'.format(self.node_name))

            # Extract CPU details
            cpu_info = status.get('cpuinfo', {})

            # Apply CPU flags redaction if configured
            if 'flags' in cpu_info:
                cpu_info = cpu_info.copy()
                cpu_info['flags'] = self.redactor.redact_cpu_flags(cpu_info.get('flags'))

            # Extract memory details
            memory_info = status.get('memory', {})
            swap_info = status.get('swap', {})

            # Extract root filesystem
            rootfs = status.get('rootfs', {})

            # Apply disk redaction if configured
            redacted_disks = []
            if disks:
                for disk in disks:
                    redacted_disks.append(self.redactor.redact_disk_info(disk))
            else:
                redacted_disks = []

            return {
                'node_name': self.node_name,
                'cpu_info': cpu_info,
                'memory': memory_info,
                'swap': swap_info,
                'rootfs': rootfs,
                'disks': redacted_disks,
                'pci_devices': pci_devices if pci_devices else [],
            }

        except Exception as e:
            logger.error(f"Error collecting hardware data for {self.node_name}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'node_hardware.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        safe_name = sanitize_filename(self.node_name)
        return self.output_dir / 'nodes' / safe_name / 'hardware.mdx'


class NodeNetworkGenerator(BaseDocumentGenerator):
    """Generator for node network documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str):
        """Initialize node network generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Name of the node to document
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect node network data from API.

        Returns:
            Dictionary containing network information
        """
        try:
            # Get network configuration
            network = self.api.get_node_network(self.node_name)
            if not network:
                logger.error(f"Failed to fetch network config for node {self.node_name}")
                return None

            # Try to get DNS configuration
            dns = self.api.get('/nodes/{}/dns'.format(self.node_name))

            # Categorize interfaces by type
            physical_interfaces = []
            bridges = []
            bonds = []
            vlans = []
            other_interfaces = []

            for iface in network:
                # Apply MAC address redaction
                redacted_iface = self.redactor.redact_network_interface(iface)

                iface_type = redacted_iface.get('type', 'unknown')
                if iface_type == 'eth':
                    physical_interfaces.append(redacted_iface)
                elif iface_type == 'bridge':
                    bridges.append(redacted_iface)
                elif iface_type == 'bond':
                    bonds.append(redacted_iface)
                elif iface_type == 'vlan':
                    vlans.append(redacted_iface)
                else:
                    other_interfaces.append(redacted_iface)

            # Also redact the all_interfaces list
            redacted_all = [self.redactor.redact_network_interface(iface) for iface in network]

            return {
                'node_name': self.node_name,
                'all_interfaces': redacted_all,
                'physical_interfaces': physical_interfaces,
                'bridges': bridges,
                'bonds': bonds,
                'vlans': vlans,
                'other_interfaces': other_interfaces,
                'dns': dns if dns else {},
            }

        except Exception as e:
            logger.error(f"Error collecting network data for {self.node_name}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'node_network.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        safe_name = sanitize_filename(self.node_name)
        return self.output_dir / 'nodes' / safe_name / 'network.mdx'
