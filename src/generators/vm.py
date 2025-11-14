"""Virtual Machine documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDocumentGenerator
from src.models import VirtualMachine
from src.utils import format_bytes, parse_tags, parse_disk_string, parse_network_string, sanitize_filename

logger = logging.getLogger(__name__)


class VMIndexGenerator(BaseDocumentGenerator):
    """Generator for VM index/list documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect all VMs from cluster.

        Returns:
            Dictionary containing VM list
        """
        try:
            # Get all VMs from cluster
            vms = self.api.get_cluster_resources(resource_type='vm')
            if vms is None:
                logger.error("Failed to fetch VMs from cluster")
                return None

            # Sort by node, then by vmid
            vms_sorted = sorted(vms, key=lambda x: (x.get('node', ''), x.get('vmid', 0)))

            # Group by node
            vms_by_node = {}
            for vm in vms_sorted:
                node = vm.get('node', 'unknown')
                if node not in vms_by_node:
                    vms_by_node[node] = []
                vms_by_node[node].append(vm)

            return {
                'vms': vms_sorted,
                'vms_by_node': vms_by_node,
                'total_vms': len(vms_sorted),
            }

        except Exception as e:
            logger.error(f"Error collecting VM index data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'vm_index.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'virtual-machines' / 'index.mdx'


class VMOverviewGenerator(BaseDocumentGenerator):
    """Generator for VM overview documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str, vmid: int):
        """Initialize VM overview generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Node where VM is located
            vmid: VM ID
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name
        self.vmid = vmid

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect VM overview data from API.

        Returns:
            Dictionary containing VM information
        """
        try:
            # Get VM configuration
            config = self.api.get_vm_config(self.node_name, self.vmid)
            if not config:
                logger.error(f"Failed to fetch config for VM {self.vmid}")
                return None

            # Extract basic info
            vm_name = config.get('name', f'vm-{self.vmid}')
            description = config.get('description', '')

            # CPU configuration
            cores = config.get('cores', 0)
            sockets = config.get('sockets', 1)
            cpu_type = config.get('cpu', 'kvm64')

            # Memory (in MB)
            memory = config.get('memory', 0)

            # Other settings
            ostype = config.get('ostype', '')
            boot = config.get('boot', '')
            bios = config.get('bios', 'seabios')
            machine = config.get('machine', '')
            onboot = config.get('onboot', 0) == 1
            protection = config.get('protection', 0) == 1
            agent = config.get('agent', '')
            agent_enabled = '1' in str(agent) if agent else False

            # Tags
            tags = parse_tags(config.get('tags', ''))

            # Build VM model
            vm = VirtualMachine(
                vmid=self.vmid,
                name=vm_name,
                node=self.node_name,
                description=description,
                cores=cores,
                memory=memory,
                sockets=sockets,
                cpu_type=cpu_type,
                ostype=ostype,
                boot_order=boot,
                bios=bios,
                machine=machine,
                onboot=onboot,
                protection=protection,
                agent_enabled=agent_enabled,
                tags=tags
            )

            return {
                'vm': vm,
                'config': config,
            }

        except Exception as e:
            logger.error(f"Error collecting VM overview data for {self.vmid}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'vm_overview.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        # Get VM name for directory
        config = self.api.get_vm_config(self.node_name, self.vmid)
        vm_name = config.get('name', 'vm') if config else 'vm'
        safe_name = sanitize_filename(vm_name)

        return self.output_dir / 'virtual-machines' / f'{self.vmid}-{safe_name}' / 'overview.mdx'


class VMNetworkGenerator(BaseDocumentGenerator):
    """Generator for VM network documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str, vmid: int):
        """Initialize VM network generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Node where VM is located
            vmid: VM ID
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name
        self.vmid = vmid

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect VM network data from API.

        Returns:
            Dictionary containing network information
        """
        try:
            # Get VM configuration
            config = self.api.get_vm_config(self.node_name, self.vmid)
            if not config:
                logger.error(f"Failed to fetch config for VM {self.vmid}")
                return None

            vm_name = config.get('name', f'vm-{self.vmid}')

            # Parse network interfaces (net0, net1, etc.)
            network_interfaces = []
            for key, value in config.items():
                if key.startswith('net') and key[3:].isdigit():
                    iface_num = key[3:]
                    parsed = parse_network_string(value)
                    parsed['interface'] = key
                    parsed['interface_num'] = iface_num
                    # Apply MAC address redaction
                    parsed = self.redactor.redact_network_interface(parsed)
                    network_interfaces.append(parsed)

            # Sort by interface number
            network_interfaces.sort(key=lambda x: int(x.get('interface_num', 0)))

            # Try to get guest agent network info (may not be available)
            guest_network = None
            try:
                guest_network_raw = self.api.get(f'/nodes/{self.node_name}/qemu/{self.vmid}/agent/network-get-interfaces')
                # Apply MAC address redaction to guest network interfaces
                if guest_network_raw and 'result' in guest_network_raw:
                    guest_network = guest_network_raw.copy()
                    guest_network['result'] = [self.redactor.redact_network_interface(iface) for iface in guest_network_raw.get('result', [])]
                else:
                    guest_network = guest_network_raw
            except:
                pass

            # Get firewall configuration
            firewall_rules = self.api.get(f'/nodes/{self.node_name}/qemu/{self.vmid}/firewall/rules')

            return {
                'vm_name': vm_name,
                'vmid': self.vmid,
                'node_name': self.node_name,
                'network_interfaces': network_interfaces,
                'guest_network': guest_network,
                'firewall_rules': firewall_rules if firewall_rules else [],
            }

        except Exception as e:
            logger.error(f"Error collecting VM network data for {self.vmid}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'vm_network.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        config = self.api.get_vm_config(self.node_name, self.vmid)
        vm_name = config.get('name', 'vm') if config else 'vm'
        safe_name = sanitize_filename(vm_name)

        return self.output_dir / 'virtual-machines' / f'{self.vmid}-{safe_name}' / 'network.mdx'


class VMStorageGenerator(BaseDocumentGenerator):
    """Generator for VM storage documentation."""

    def __init__(self, api_client, config, output_dir: Path, node_name: str, vmid: int):
        """Initialize VM storage generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance
            output_dir: Base output directory
            node_name: Node where VM is located
            vmid: VM ID
        """
        super().__init__(api_client, config, output_dir)
        self.node_name = node_name
        self.vmid = vmid

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect VM storage data from API.

        Returns:
            Dictionary containing storage information
        """
        try:
            # Get VM configuration
            config = self.api.get_vm_config(self.node_name, self.vmid)
            if not config:
                logger.error(f"Failed to fetch config for VM {self.vmid}")
                return None

            vm_name = config.get('name', f'vm-{self.vmid}')

            # Parse disk configurations
            disks = []

            # Common disk types
            disk_types = ['scsi', 'virtio', 'sata', 'ide']

            for disk_type in disk_types:
                for i in range(32):  # Support up to 32 disks per type
                    key = f'{disk_type}{i}'
                    if key in config:
                        value = config[key]
                        parsed = parse_disk_string(value)
                        parsed['interface'] = key
                        parsed['disk_type'] = disk_type
                        parsed['disk_num'] = i
                        disks.append(parsed)

            # Also check for unused disks
            for key, value in config.items():
                if key.startswith('unused'):
                    parsed = parse_disk_string(value)
                    parsed['interface'] = key
                    parsed['disk_type'] = 'unused'
                    disks.append(parsed)

            # Sort disks by interface
            disks.sort(key=lambda x: (x.get('disk_type', ''), x.get('disk_num', 0)))

            # Parse CDROM/ISO attachments
            cdroms = []
            for disk_type in disk_types:
                for i in range(8):
                    key = f'{disk_type}{i}'
                    if key in config:
                        value = config[key]
                        if 'media=cdrom' in value or '.iso' in value.lower():
                            parsed = parse_disk_string(value)
                            parsed['interface'] = key
                            cdroms.append(parsed)

            # Get storage controller type
            scsihw = config.get('scsihw', 'lsi')

            return {
                'vm_name': vm_name,
                'vmid': self.vmid,
                'node_name': self.node_name,
                'disks': disks,
                'cdroms': cdroms,
                'scsihw': scsihw,
                'config': config,
            }

        except Exception as e:
            logger.error(f"Error collecting VM storage data for {self.vmid}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'vm_storage.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        config = self.api.get_vm_config(self.node_name, self.vmid)
        vm_name = config.get('name', 'vm') if config else 'vm'
        safe_name = sanitize_filename(vm_name)

        return self.output_dir / 'virtual-machines' / f'{self.vmid}-{safe_name}' / 'storage.mdx'
