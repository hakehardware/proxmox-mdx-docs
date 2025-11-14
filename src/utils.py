"""Utility functions for documentation generation."""

from typing import Optional, List
from datetime import datetime


def format_bytes(bytes_value: Optional[int]) -> str:
    """Convert bytes to human-readable format.

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted string (e.g., "32.00 GB")
    """
    if bytes_value is None:
        return "N/A"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_memory_mb(mb_value: Optional[int]) -> str:
    """Convert MB to human-readable format.

    Args:
        mb_value: Size in megabytes

    Returns:
        Formatted string (e.g., "4.00 GB")
    """
    if mb_value is None:
        return "N/A"

    # Convert to int if string
    if isinstance(mb_value, str):
        try:
            mb_value = int(mb_value)
        except ValueError:
            return "N/A"

    if mb_value < 1024:
        return f"{mb_value} MB"
    else:
        gb_value = mb_value / 1024.0
        return f"{gb_value:.2f} GB"


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """Format timestamp for documentation.

    Args:
        timestamp: ISO format timestamp, or None for current time

    Returns:
        Formatted timestamp string
    """
    if timestamp:
        return timestamp
    return datetime.utcnow().isoformat() + 'Z'


def parse_tags(tags_str: Optional[str]) -> List[str]:
    """Parse tags string into list.

    Args:
        tags_str: Semicolon-separated tags string

    Returns:
        List of individual tags
    """
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(';') if tag.strip()]


def parse_disk_string(disk_str: str) -> dict:
    """Parse Proxmox disk configuration string.

    Args:
        disk_str: Disk string like "local-lvm:vm-100-disk-0,size=32G"

    Returns:
        Dictionary with parsed disk information
    """
    parts = disk_str.split(',')
    result = {}

    # First part is storage:volume
    if ':' in parts[0]:
        storage, volume = parts[0].split(':', 1)
        result['storage'] = storage
        result['volume'] = volume
    else:
        result['volume'] = parts[0]

    # Parse remaining options
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key] = value

    return result


def parse_network_string(net_str: str) -> dict:
    """Parse Proxmox network configuration string.

    Args:
        net_str: Network string like "virtio=BC:24:11:2E:F4:A0,bridge=vmbr0"

    Returns:
        Dictionary with parsed network information
    """
    parts = net_str.split(',')
    result = {}

    # First part is model=macaddr
    if '=' in parts[0]:
        model, macaddr = parts[0].split('=', 1)
        result['model'] = model
        result['macaddr'] = macaddr

    # Parse remaining options
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key] = value

    return result


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename.

    Args:
        name: Original name

    Returns:
        Sanitized filename-safe string
    """
    # Replace spaces and special characters
    safe_name = name.lower()
    safe_name = safe_name.replace(' ', '-')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-_')
    return safe_name


def format_yaml_string(value: str) -> str:
    """Format a string value for YAML frontmatter.

    Args:
        value: String value

    Returns:
        Properly quoted/escaped string for YAML
    """
    if not value:
        return '""'

    # If contains special characters, quote it
    if any(c in value for c in [':', '#', '[', ']', '{', '}', '\n']):
        # Escape quotes and wrap in quotes
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'

    return value
