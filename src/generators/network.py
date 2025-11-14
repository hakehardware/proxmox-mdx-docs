"""Network documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import ipaddress

from .base import BaseDocumentGenerator
from src.utils import sanitize_filename

logger = logging.getLogger(__name__)


class NetworkOverviewGenerator(BaseDocumentGenerator):
    """Generator for network overview documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect network overview data from cluster.

        Returns:
            Dictionary containing network configuration
        """
        try:
            # Get all nodes
            nodes = self.api.get_nodes()
            if not nodes:
                logger.error("Failed to fetch nodes")
                return None

            node_networks = []

            # Collect network info from each node
            for node in nodes:
                node_name = node.get('node')
                if not node_name:
                    continue

                # Get node network interfaces
                interfaces = self.api.get(f'/nodes/{node_name}/network')
                if interfaces:
                    node_networks.append({
                        'node': node_name,
                        'interfaces': interfaces,
                    })

            # Categorize interfaces across all nodes
            all_bridges = []
            all_bonds = []
            all_vlans = []
            all_physical = []

            for node_net in node_networks:
                node_name = node_net['node']
                for iface in node_net['interfaces']:
                    iface_data = iface.copy()
                    iface_data['node'] = node_name

                    iface_type = iface.get('type', '')
                    if iface_type == 'bridge':
                        all_bridges.append(iface_data)
                    elif iface_type == 'bond':
                        all_bonds.append(iface_data)
                    elif iface_type == 'vlan':
                        all_vlans.append(iface_data)
                    elif iface_type in ['eth', 'alias']:
                        all_physical.append(iface_data)

            return {
                'node_networks': node_networks,
                'all_bridges': all_bridges,
                'all_bonds': all_bonds,
                'all_vlans': all_vlans,
                'all_physical': all_physical,
                'total_nodes': len(node_networks),
                'total_bridges': len(all_bridges),
                'total_bonds': len(all_bonds),
                'total_vlans': len(all_vlans),
                'total_physical': len(all_physical),
            }

        except Exception as e:
            logger.error(f"Error collecting network overview data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'network_overview.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'network' / 'index.mdx'


class IPAddressingGenerator(BaseDocumentGenerator):
    """Generator for IP addressing plan documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect IP addressing data from cluster.

        Returns:
            Dictionary containing IP addressing information
        """
        try:
            ip_assignments = []

            # Get all nodes
            nodes = self.api.get_nodes()
            if not nodes:
                logger.error("Failed to fetch nodes")
                return None

            # Collect IPs from node interfaces
            for node in nodes:
                node_name = node.get('node')
                if not node_name:
                    continue

                interfaces = self.api.get(f'/nodes/{node_name}/network')
                if interfaces:
                    for iface in interfaces:
                        # Get IPv4 address
                        if iface.get('address'):
                            ip_assignments.append({
                                'ip': iface.get('address'),
                                'netmask': iface.get('netmask'),
                                'cidr': iface.get('cidr'),
                                'gateway': iface.get('gateway'),
                                'type': 'Node',
                                'name': node_name,
                                'interface': iface.get('iface'),
                                'description': f"Node {node_name} - {iface.get('iface')}",
                            })

                        # Get IPv6 address
                        if iface.get('address6'):
                            ip_assignments.append({
                                'ip': iface.get('address6'),
                                'netmask': iface.get('netmask6'),
                                'cidr': iface.get('cidr6'),
                                'gateway': iface.get('gateway6'),
                                'type': 'Node',
                                'name': node_name,
                                'interface': iface.get('iface'),
                                'description': f"Node {node_name} - {iface.get('iface')} (IPv6)",
                            })

            # Get all VMs and containers
            all_resources = self.api.get_cluster_resources()
            if all_resources:
                vms = [r for r in all_resources if r.get('type') == 'qemu']
                containers = [r for r in all_resources if r.get('type') == 'lxc']

                # Collect IPs from VMs
                for vm in vms:
                    node_name = vm.get('node')
                    vmid = vm.get('vmid')
                    vm_name = vm.get('name', f'vm-{vmid}')

                    if node_name and vmid:
                        vm_config = self.api.get(f'/nodes/{node_name}/qemu/{vmid}/config')
                        if vm_config:
                            # Parse network interfaces
                            for key, value in vm_config.items():
                                if key.startswith('net') and isinstance(value, str):
                                    # Parse IP from config if static
                                    parts = value.split(',')
                                    ip_addr = None
                                    gw = None
                                    bridge = None
                                    for part in parts:
                                        if '=' in part:
                                            k, v = part.split('=', 1)
                                            if k.strip() == 'ip':
                                                ip_addr = v.strip()
                                            elif k.strip() == 'gw':
                                                gw = v.strip()
                                            elif k.strip() == 'bridge':
                                                bridge = v.strip()

                                    if ip_addr:
                                        ip_assignments.append({
                                            'ip': ip_addr,
                                            'gateway': gw,
                                            'type': 'VM',
                                            'name': vm_name,
                                            'vmid': vmid,
                                            'interface': key,
                                            'bridge': bridge,
                                            'description': f"VM {vmid} ({vm_name}) - {key}",
                                        })

                            # Try to get guest agent IPs
                            try:
                                guest_ips = self.api.get(f'/nodes/{node_name}/qemu/{vmid}/agent/network-get-interfaces')
                                if guest_ips and isinstance(guest_ips, dict):
                                    result = guest_ips.get('result', [])
                                    for iface_info in result:
                                        if isinstance(iface_info, dict):
                                            iface_name = iface_info.get('name', '')
                                            ip_addrs = iface_info.get('ip-addresses', [])
                                            for ip_info in ip_addrs:
                                                if isinstance(ip_info, dict):
                                                    ip_addr = ip_info.get('ip-address')
                                                    ip_type = ip_info.get('ip-address-type', '')
                                                    prefix = ip_info.get('prefix', '')

                                                    if ip_addr and iface_name != 'lo':
                                                        # Check if we already have this IP from config
                                                        already_listed = any(
                                                            a.get('ip', '').split('/')[0] == ip_addr
                                                            for a in ip_assignments
                                                            if a.get('vmid') == vmid
                                                        )
                                                        if not already_listed:
                                                            ip_assignments.append({
                                                                'ip': f"{ip_addr}/{prefix}" if prefix else ip_addr,
                                                                'type': 'VM',
                                                                'name': vm_name,
                                                                'vmid': vmid,
                                                                'interface': iface_name,
                                                                'description': f"VM {vmid} ({vm_name}) - {iface_name} (Guest Agent)",
                                                            })
                            except:
                                pass  # Guest agent not available

                # Collect IPs from containers
                for ct in containers:
                    node_name = ct.get('node')
                    vmid = ct.get('vmid')

                    if node_name and vmid:
                        ct_config = self.api.get(f'/nodes/{node_name}/lxc/{vmid}/config')
                        if ct_config:
                            ct_hostname = ct_config.get('hostname', f'ct-{vmid}')

                            # Parse network interfaces
                            for key, value in ct_config.items():
                                if key.startswith('net') and isinstance(value, str):
                                    parts = value.split(',')
                                    ip_addr = None
                                    gw = None
                                    bridge = None
                                    for part in parts:
                                        if '=' in part:
                                            k, v = part.split('=', 1)
                                            if k.strip() == 'ip':
                                                ip_addr = v.strip()
                                            elif k.strip() == 'gw':
                                                gw = v.strip()
                                            elif k.strip() == 'bridge':
                                                bridge = v.strip()

                                    if ip_addr:
                                        ip_assignments.append({
                                            'ip': ip_addr,
                                            'gateway': gw,
                                            'type': 'Container',
                                            'name': ct_hostname,
                                            'vmid': vmid,
                                            'interface': key,
                                            'bridge': bridge,
                                            'description': f"CT {vmid} ({ct_hostname}) - {key}",
                                        })

            # Sort IP assignments by IP address
            def ip_sort_key(item):
                try:
                    ip_str = item.get('ip', '').split('/')[0]
                    return ipaddress.ip_address(ip_str)
                except:
                    return ipaddress.ip_address('0.0.0.0')

            ip_assignments_sorted = sorted(ip_assignments, key=ip_sort_key)

            # Group by subnet
            subnets = {}
            for assignment in ip_assignments_sorted:
                try:
                    ip_str = assignment.get('ip', '')
                    if '/' in ip_str:
                        network = ipaddress.ip_network(ip_str, strict=False)
                        subnet_str = str(network)
                    else:
                        # Default to /24 for grouping
                        ip_obj = ipaddress.ip_address(ip_str)
                        if isinstance(ip_obj, ipaddress.IPv4Address):
                            network = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                        else:
                            network = ipaddress.ip_network(f"{ip_str}/64", strict=False)
                        subnet_str = str(network)

                    if subnet_str not in subnets:
                        subnets[subnet_str] = []
                    subnets[subnet_str].append(assignment)
                except:
                    # Can't parse IP, put in "Other"
                    if 'Other' not in subnets:
                        subnets['Other'] = []
                    subnets['Other'].append(assignment)

            return {
                'ip_assignments': ip_assignments_sorted,
                'subnets': subnets,
                'total_ips': len(ip_assignments_sorted),
            }

        except Exception as e:
            logger.error(f"Error collecting IP addressing data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'ip_addressing.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'network' / 'ip-addressing.mdx'


class VLANGenerator(BaseDocumentGenerator):
    """Generator for VLAN documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect VLAN data from cluster.

        Returns:
            Dictionary containing VLAN information
        """
        try:
            vlans = []

            # Get all nodes
            nodes = self.api.get_nodes()
            if not nodes:
                logger.error("Failed to fetch nodes")
                return None

            # Collect VLANs from node interfaces
            for node in nodes:
                node_name = node.get('node')
                if not node_name:
                    continue

                interfaces = self.api.get(f'/nodes/{node_name}/network')
                if interfaces:
                    for iface in interfaces:
                        # VLAN interfaces
                        if iface.get('type') == 'vlan':
                            vlan_id = iface.get('vlan-id') or iface.get('vlan_id')
                            vlans.append({
                                'node': node_name,
                                'interface': iface.get('iface'),
                                'vlan_id': vlan_id,
                                'vlan_raw_device': iface.get('vlan-raw-device') or iface.get('vlan_raw_device'),
                                'address': iface.get('address'),
                                'netmask': iface.get('netmask'),
                                'comments': iface.get('comments'),
                            })

                        # Bridge with VLAN awareness
                        if iface.get('bridge_vlan_aware') == 1 or iface.get('bridge-vlan-aware') == 1:
                            vlans.append({
                                'node': node_name,
                                'interface': iface.get('iface'),
                                'type': 'VLAN-aware bridge',
                                'address': iface.get('address'),
                                'bridge_ports': iface.get('bridge_ports') or iface.get('bridge-ports'),
                                'comments': iface.get('comments'),
                            })

            # Group VLANs by VLAN ID
            vlans_by_id = {}
            for vlan in vlans:
                vlan_id = vlan.get('vlan_id')
                if vlan_id:
                    if vlan_id not in vlans_by_id:
                        vlans_by_id[vlan_id] = []
                    vlans_by_id[vlan_id].append(vlan)

            # Sort VLANs by ID
            vlans_by_id_sorted = dict(sorted(vlans_by_id.items(), key=lambda x: int(x[0]) if x[0] else 0))

            return {
                'vlans': vlans,
                'vlans_by_id': vlans_by_id_sorted,
                'total_vlans': len(vlans),
                'vlan_ids': list(vlans_by_id_sorted.keys()),
            }

        except Exception as e:
            logger.error(f"Error collecting VLAN data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'vlans.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'network' / 'vlans.mdx'


class SDNGenerator(BaseDocumentGenerator):
    """Generator for SDN (Software Defined Networking) documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect SDN data from cluster.

        Returns:
            Dictionary containing SDN information
        """
        try:
            # Check if SDN is configured
            try:
                sdn_zones = self.api.get('/cluster/sdn/zones')
                sdn_vnets = self.api.get('/cluster/sdn/vnets')
            except:
                # SDN not available or not configured
                logger.info("SDN not configured or not available")
                return {
                    'sdn_enabled': False,
                    'zones': [],
                    'vnets': [],
                }

            sdn_enabled = bool(sdn_zones or sdn_vnets)

            return {
                'sdn_enabled': sdn_enabled,
                'zones': sdn_zones if sdn_zones else [],
                'vnets': sdn_vnets if sdn_vnets else [],
                'total_zones': len(sdn_zones) if sdn_zones else 0,
                'total_vnets': len(sdn_vnets) if sdn_vnets else 0,
            }

        except Exception as e:
            logger.error(f"Error collecting SDN data: {e}", exc_info=True)
            return {
                'sdn_enabled': False,
                'zones': [],
                'vnets': [],
            }

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'sdn.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'network' / 'sdn.mdx'
