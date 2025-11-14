"""Proxmox API client for fetching configuration data."""

import requests
from typing import Any, Dict, Optional, List
from urllib3.exceptions import InsecureRequestWarning
import logging

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ProxmoxAPIClient:
    """Client for interacting with Proxmox VE API."""

    def __init__(
        self,
        host: str,
        api_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = False
    ):
        """Initialize Proxmox API client.

        Args:
            host: Proxmox host (e.g., 'proxmox.example.com' or '192.168.1.100')
            api_token: API token in format 'USER@REALM!TOKENID=SECRET' (recommended)
            username: Username in format 'user@pam' or 'user@pve' (fallback)
            password: Password (fallback)
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = f"https://{host}:8006/api2/json"
        self.api_token = api_token
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.ticket: Optional[str] = None
        self.csrf_token: Optional[str] = None

        # Determine authentication method
        if api_token:
            self.auth_method = "token"
            logger.info("Using API Token authentication")
        elif username and password:
            self.auth_method = "password"
            logger.info("Using username/password authentication")
        else:
            raise ValueError("Must provide either api_token or username+password")

    def authenticate(self) -> bool:
        """Authenticate with Proxmox API.

        Returns:
            True if authentication successful, False otherwise
        """
        if self.auth_method == "token":
            logger.info("✓ API Token configured")
            return True

        # Username/password requires getting a ticket
        auth_url = f"{self.base_url}/access/ticket"
        auth_data = {
            'username': self.username,
            'password': self.password
        }

        try:
            response = requests.post(
                auth_url,
                data=auth_data,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()['data']
            self.ticket = data['ticket']
            self.csrf_token = data['CSRFPreventionToken']
            logger.info("✓ Authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Authentication failed: {e}")
            return False

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make authenticated GET request to Proxmox API.

        Args:
            endpoint: API endpoint path (e.g., '/nodes')
            params: Optional query parameters

        Returns:
            Response data dictionary or None if request failed
        """
        url = f"{self.base_url}{endpoint}"

        if self.auth_method == "token":
            headers = {'Authorization': f'PVEAPIToken={self.api_token}'}
            cookies = None
        else:
            headers = {'CSRFPreventionToken': self.csrf_token}
            cookies = {'PVEAuthCookie': self.ticket}

        try:
            response = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                params=params,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.json()['data']

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API request failed for {endpoint}: {e}")
            return None

    def get_cluster_status(self) -> Optional[Dict[str, Any]]:
        """Get cluster status information."""
        return self.get('/cluster/status')

    def get_cluster_resources(self, resource_type: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get cluster resources.

        Args:
            resource_type: Filter by type ('vm', 'lxc', 'node', 'storage')

        Returns:
            List of resources or None
        """
        params = {'type': resource_type} if resource_type else None
        return self.get('/cluster/resources', params=params)

    def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Proxmox VE version information."""
        return self.get('/version')

    def get_nodes(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all nodes in the cluster."""
        return self.get('/nodes')

    def get_node_config(self, node: str) -> Optional[Dict[str, Any]]:
        """Get node configuration including description.

        Args:
            node: Node name

        Returns:
            Node configuration or None
        """
        return self.get(f'/nodes/{node}/config')

    def get_node_status(self, node: str) -> Optional[Dict[str, Any]]:
        """Get node status information.

        Args:
            node: Node name

        Returns:
            Node status or None
        """
        return self.get(f'/nodes/{node}/status')

    def get_node_version(self, node: str) -> Optional[Dict[str, Any]]:
        """Get Proxmox VE version for a specific node.

        Args:
            node: Node name

        Returns:
            Version information or None
        """
        return self.get(f'/nodes/{node}/version')

    def get_node_network(self, node: str) -> Optional[List[Dict[str, Any]]]:
        """Get network configuration for a node.

        Args:
            node: Node name

        Returns:
            List of network interfaces or None
        """
        return self.get(f'/nodes/{node}/network')

    def get_node_storage(self, node: str) -> Optional[List[Dict[str, Any]]]:
        """Get storage information for a node.

        Args:
            node: Node name

        Returns:
            List of storage pools or None
        """
        return self.get(f'/nodes/{node}/storage')

    def get_vm_config(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get VM configuration.

        Args:
            node: Node name
            vmid: VM ID

        Returns:
            VM configuration or None
        """
        return self.get(f'/nodes/{node}/qemu/{vmid}/config')

    def get_container_config(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get container configuration.

        Args:
            node: Node name
            vmid: Container ID

        Returns:
            Container configuration or None
        """
        return self.get(f'/nodes/{node}/lxc/{vmid}/config')
