"""Storage documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDocumentGenerator
from src.models import StoragePool
from src.utils import format_bytes, sanitize_filename

logger = logging.getLogger(__name__)


class StorageIndexGenerator(BaseDocumentGenerator):
    """Generator for storage index/list documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect all storage pools from cluster.

        Returns:
            Dictionary containing storage pool list
        """
        try:
            # Get all storage pools
            storage_list = self.api.get('/storage')
            if not storage_list:
                logger.error("Failed to fetch storage list")
                return None

            # Get cluster resources for storage capacity info
            all_resources = self.api.get_cluster_resources()

            # Get detailed info for each pool
            storage_pools = []
            for pool in storage_list:
                storage_id = pool.get('storage')
                if not storage_id:
                    continue

                # Start with basic info from storage list
                pool_data = {
                    'storage_id': storage_id,
                    'type': pool.get('type', 'unknown'),
                    'content': pool.get('content', '').split(',') if pool.get('content') else [],
                    'shared': pool.get('shared', 0) == 1,
                    'enabled': pool.get('disable', 0) == 0,
                    'nodes': pool.get('nodes', '').split(',') if pool.get('nodes') else [],
                    'path': pool.get('path'),
                }

                # Try to get detailed storage info (may fail due to permissions)
                try:
                    storage_detail = self.api.get(f'/storage/{storage_id}')
                    if storage_detail:
                        # Update with detailed info if we got it
                        pool_data.update({
                            'type': storage_detail.get('type', pool_data['type']),
                            'content': storage_detail.get('content', '').split(',') if storage_detail.get('content') else pool_data['content'],
                            'shared': storage_detail.get('shared', 0) == 1,
                            'enabled': storage_detail.get('disable', 0) == 0,
                            'nodes': storage_detail.get('nodes', '').split(',') if storage_detail.get('nodes') else pool_data['nodes'],
                            'path': storage_detail.get('path', pool_data.get('path')),
                            'pool': storage_detail.get('pool'),
                            'maxfiles': storage_detail.get('maxfiles'),
                        })
                except Exception as e:
                    # Permission denied or other error - continue with basic info
                    logger.warning(f"Could not get detailed info for storage {storage_id}, using basic info: {e}")

                # Get storage status to find capacity from cluster resources
                if all_resources:
                    for resource in all_resources:
                        if resource.get('type') == 'storage' and resource.get('storage') == storage_id:
                            pool_data['total'] = resource.get('maxdisk', 0)
                            pool_data['used'] = resource.get('disk', 0)
                            pool_data['available'] = resource.get('maxdisk', 0) - resource.get('disk', 0)
                            break

                storage_pools.append(pool_data)

            # Sort by storage ID
            storage_pools_sorted = sorted(storage_pools, key=lambda x: x.get('storage_id', ''))

            # Group by type
            storage_by_type = {}
            for pool in storage_pools_sorted:
                pool_type = pool.get('type', 'unknown')
                if pool_type not in storage_by_type:
                    storage_by_type[pool_type] = []
                storage_by_type[pool_type].append(pool)

            return {
                'storage_pools': storage_pools_sorted,
                'storage_by_type': storage_by_type,
                'total_pools': len(storage_pools_sorted),
            }

        except Exception as e:
            logger.error(f"Error collecting storage index data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'storage_index.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'storage' / 'index.mdx'


class StoragePoolGenerator(BaseDocumentGenerator):
    """Generator for individual storage pool documentation."""

    def __init__(self, api_client, output_dir: Path, storage_id: str):
        """Initialize storage pool generator.

        Args:
            api_client: ProxmoxAPIClient instance
            output_dir: Base output directory
            storage_id: Storage pool ID
        """
        super().__init__(api_client, output_dir)
        self.storage_id = storage_id

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect storage pool data from API.

        Returns:
            Dictionary containing storage pool information
        """
        try:
            # Get storage configuration
            storage_config = self.api.get(f'/storage/{self.storage_id}')
            if not storage_config:
                logger.error(f"Failed to fetch config for storage {self.storage_id}")
                return None

            # Get storage status/capacity from cluster resources
            total_capacity = 0
            used_capacity = 0
            available_capacity = 0

            all_resources = self.api.get_cluster_resources()
            if all_resources:
                for resource in all_resources:
                    if resource.get('type') == 'storage' and resource.get('storage') == self.storage_id:
                        total_capacity = resource.get('maxdisk', 0)
                        used_capacity = resource.get('disk', 0)
                        available_capacity = total_capacity - used_capacity
                        break

            # Parse configuration
            storage_type = storage_config.get('type', 'unknown')
            content_types = storage_config.get('content', '').split(',') if storage_config.get('content') else []
            shared = storage_config.get('shared', 0) == 1
            enabled = storage_config.get('disable', 0) == 0
            nodes = storage_config.get('nodes', '').split(',') if storage_config.get('nodes') else []

            # Type-specific fields
            path = storage_config.get('path')
            pool = storage_config.get('pool')
            maxfiles = storage_config.get('maxfiles')
            krbd = storage_config.get('krbd', 0) == 1
            monhost = storage_config.get('monhost')

            # Find which VMs/containers use this storage
            using_vms = []
            using_containers = []

            # Get all VMs and containers
            if all_resources:
                vms = [r for r in all_resources if r.get('type') == 'qemu']
                containers = [r for r in all_resources if r.get('type') == 'lxc']

                # Check each VM
                for vm in vms:
                    node_name = vm.get('node')
                    vmid = vm.get('vmid')
                    if node_name and vmid:
                        vm_config = self.api.get(f'/nodes/{node_name}/qemu/{vmid}/config')
                        if vm_config:
                            # Check all disk configurations
                            for key, value in vm_config.items():
                                if key.startswith(('scsi', 'sata', 'ide', 'virtio', 'efidisk', 'tpmstate')):
                                    if isinstance(value, str) and value.startswith(f'{self.storage_id}:'):
                                        using_vms.append({
                                            'vmid': vmid,
                                            'name': vm.get('name', f'vm-{vmid}'),
                                            'node': node_name,
                                            'disk': key,
                                        })
                                        break

                # Check each container
                for ct in containers:
                    node_name = ct.get('node')
                    vmid = ct.get('vmid')
                    if node_name and vmid:
                        ct_config = self.api.get(f'/nodes/{node_name}/lxc/{vmid}/config')
                        if ct_config:
                            # Check rootfs and mount points
                            for key, value in ct_config.items():
                                if key in ['rootfs'] or key.startswith('mp'):
                                    if isinstance(value, str) and value.startswith(f'{self.storage_id}:'):
                                        using_containers.append({
                                            'vmid': vmid,
                                            'hostname': ct_config.get('hostname', f'ct-{vmid}'),
                                            'node': node_name,
                                            'mount': key,
                                        })
                                        break

            return {
                'storage_id': self.storage_id,
                'storage_type': storage_type,
                'content_types': content_types,
                'shared': shared,
                'enabled': enabled,
                'nodes': nodes,
                'path': path,
                'pool': pool,
                'maxfiles': maxfiles,
                'krbd': krbd,
                'monhost': monhost,
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'available_capacity': available_capacity,
                'config': storage_config,
                'using_vms': using_vms,
                'using_containers': using_containers,
            }

        except Exception as e:
            logger.error(f"Error collecting storage pool data for {self.storage_id}: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'storage_pool.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        safe_name = sanitize_filename(self.storage_id)
        return self.output_dir / 'storage' / f'{safe_name}.mdx'


class StorageAssignmentsGenerator(BaseDocumentGenerator):
    """Generator for storage assignments documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect storage assignment data from API.

        Returns:
            Dictionary containing storage assignments
        """
        try:
            # Get all resources
            all_resources = self.api.get_cluster_resources()
            if not all_resources:
                logger.error("Failed to fetch cluster resources")
                return None

            vms = [r for r in all_resources if r.get('type') == 'qemu']
            containers = [r for r in all_resources if r.get('type') == 'lxc']

            # Build assignment map: {storage_id: {vms: [...], containers: [...]}}
            assignments = {}

            # Process VMs
            for vm in vms:
                node_name = vm.get('node')
                vmid = vm.get('vmid')
                vm_name = vm.get('name', f'vm-{vmid}')

                if node_name and vmid:
                    vm_config = self.api.get(f'/nodes/{node_name}/qemu/{vmid}/config')
                    if vm_config:
                        # Check all disk configurations
                        for key, value in vm_config.items():
                            if key.startswith(('scsi', 'sata', 'ide', 'virtio', 'efidisk', 'tpmstate')):
                                if isinstance(value, str) and ':' in value:
                                    storage_id = value.split(':')[0]
                                    if storage_id not in assignments:
                                        assignments[storage_id] = {'vms': [], 'containers': []}

                                    # Parse disk size
                                    disk_size = None
                                    if 'size=' in value:
                                        for part in value.split(','):
                                            if part.startswith('size='):
                                                disk_size = part.split('=')[1]
                                                break

                                    assignments[storage_id]['vms'].append({
                                        'vmid': vmid,
                                        'name': vm_name,
                                        'node': node_name,
                                        'disk': key,
                                        'size': disk_size,
                                    })

            # Process containers
            for ct in containers:
                node_name = ct.get('node')
                vmid = ct.get('vmid')

                if node_name and vmid:
                    ct_config = self.api.get(f'/nodes/{node_name}/lxc/{vmid}/config')
                    if ct_config:
                        ct_hostname = ct_config.get('hostname', f'ct-{vmid}')

                        # Check rootfs and mount points
                        for key, value in ct_config.items():
                            if key in ['rootfs'] or key.startswith('mp'):
                                if isinstance(value, str) and ':' in value:
                                    storage_id = value.split(':')[0]
                                    if storage_id not in assignments:
                                        assignments[storage_id] = {'vms': [], 'containers': []}

                                    # Parse disk size
                                    disk_size = None
                                    if 'size=' in value:
                                        for part in value.split(','):
                                            if part.startswith('size='):
                                                disk_size = part.split('=')[1]
                                                break

                                    assignments[storage_id]['containers'].append({
                                        'vmid': vmid,
                                        'hostname': ct_hostname,
                                        'node': node_name,
                                        'mount': key,
                                        'size': disk_size,
                                    })

            # Sort assignments by storage ID
            sorted_assignments = dict(sorted(assignments.items()))

            return {
                'assignments': sorted_assignments,
                'total_storages': len(sorted_assignments),
            }

        except Exception as e:
            logger.error(f"Error collecting storage assignments data: {e}", exc_info=True)
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'storage_assignments.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'storage' / 'assignments.mdx'
