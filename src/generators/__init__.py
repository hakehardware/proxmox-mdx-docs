"""Document generators for Proxmox infrastructure."""

from .base import BaseDocumentGenerator
from .cluster import ClusterOverviewGenerator
from .node import NodeOverviewGenerator, NodeHardwareGenerator, NodeNetworkGenerator
from .vm import VMIndexGenerator, VMOverviewGenerator, VMNetworkGenerator, VMStorageGenerator
from .container import ContainerIndexGenerator, ContainerOverviewGenerator, ContainerNetworkGenerator
from .storage import StorageIndexGenerator, StoragePoolGenerator, StorageAssignmentsGenerator
from .network import NetworkOverviewGenerator, IPAddressingGenerator, VLANGenerator, SDNGenerator
from .reference import FirewallGenerator, UsersPermissionsGenerator, BackupPoliciesGenerator, HAGenerator

__all__ = [
    'BaseDocumentGenerator',
    'ClusterOverviewGenerator',
    'NodeOverviewGenerator',
    'NodeHardwareGenerator',
    'NodeNetworkGenerator',
    'VMIndexGenerator',
    'VMOverviewGenerator',
    'VMNetworkGenerator',
    'VMStorageGenerator',
    'ContainerIndexGenerator',
    'ContainerOverviewGenerator',
    'ContainerNetworkGenerator',
    'StorageIndexGenerator',
    'StoragePoolGenerator',
    'StorageAssignmentsGenerator',
    'NetworkOverviewGenerator',
    'IPAddressingGenerator',
    'VLANGenerator',
    'SDNGenerator',
    'FirewallGenerator',
    'UsersPermissionsGenerator',
    'BackupPoliciesGenerator',
    'HAGenerator',
]
