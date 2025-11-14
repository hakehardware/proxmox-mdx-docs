"""Data models for Proxmox resources."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ClusterInfo:
    """Represents Proxmox cluster information."""
    name: str
    quorum: bool
    nodes: int
    version: Optional[str] = None
    total_vms: int = 0
    total_containers: int = 0
    online_nodes: int = 0
    offline_nodes: int = 0


@dataclass
class NodeInfo:
    """Represents a Proxmox node."""
    name: str
    status: str
    description: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_sockets: Optional[int] = None
    cpu_cores: Optional[int] = None
    total_cpu_cores: Optional[int] = None
    total_memory: Optional[int] = None  # in bytes
    pve_version: Optional[str] = None
    kernel_version: Optional[str] = None
    network_interfaces: List[Dict[str, Any]] = field(default_factory=list)
    storage_pools: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VirtualMachine:
    """Represents a Proxmox VM."""
    vmid: int
    name: str
    node: str
    description: Optional[str] = None
    cores: Optional[int] = None
    memory: Optional[int] = None  # in MB
    sockets: Optional[int] = None
    cpu_type: Optional[str] = None
    ostype: Optional[str] = None
    boot_order: Optional[str] = None
    bios: Optional[str] = None
    machine: Optional[str] = None
    onboot: bool = False
    protection: bool = False
    agent_enabled: bool = False
    tags: List[str] = field(default_factory=list)
    network_interfaces: List[Dict[str, Any]] = field(default_factory=list)
    disks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Container:
    """Represents a Proxmox LXC container."""
    vmid: int
    hostname: str
    node: str
    description: Optional[str] = None
    cores: Optional[int] = None
    memory: Optional[int] = None  # in MB
    swap: Optional[int] = None  # in MB
    ostype: Optional[str] = None
    arch: Optional[str] = None
    unprivileged: bool = True
    onboot: bool = False
    protection: bool = False
    tags: List[str] = field(default_factory=list)
    network_interfaces: List[Dict[str, Any]] = field(default_factory=list)
    rootfs: Optional[Dict[str, Any]] = None
    mount_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StoragePool:
    """Represents a storage pool."""
    storage_id: str
    storage_type: str
    path: Optional[str] = None
    total_capacity: Optional[int] = None  # in bytes
    content_types: List[str] = field(default_factory=list)
    nodes: List[str] = field(default_factory=list)
    shared: bool = False
    enabled: bool = True


@dataclass
class NetworkInterface:
    """Represents a network interface."""
    iface: str
    interface_type: str
    address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    bridge_ports: Optional[str] = None
    bond_slaves: Optional[str] = None
    vlan_id: Optional[int] = None
    mtu: Optional[int] = None
    active: bool = False
    autostart: bool = False
    comments: Optional[str] = None
