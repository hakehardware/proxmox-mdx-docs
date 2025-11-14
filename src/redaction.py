"""Redaction utilities for public documentation generation."""

import re
from typing import Optional, Dict, Any, List
from .config import ProxmoxConfig


class Redactor:
    """Handles redaction of sensitive information for public documentation."""

    def __init__(self, config: ProxmoxConfig):
        """Initialize redactor with configuration.

        Args:
            config: ProxmoxConfig instance with redaction settings
        """
        self.config = config
        self._username_map: Dict[str, str] = {}
        self._username_counter = 0

    def redact_mac_address(self, mac: Optional[str]) -> Optional[str]:
        """Redact MAC address if configured.

        Args:
            mac: MAC address string (e.g., "aa:bb:cc:dd:ee:ff")

        Returns:
            Redacted MAC or original value
        """
        if not mac or not self.config.redact_mac_addresses:
            return mac
        return "XX:XX:XX:XX:XX:XX"

    def redact_serial(self, serial: Optional[str]) -> Optional[str]:
        """Redact hardware serial number if configured.

        Args:
            serial: Serial number string

        Returns:
            Redacted serial or original value
        """
        if not serial or not self.config.redact_hardware_serials:
            return serial
        return "REDACTED"

    def redact_wwn(self, wwn: Optional[str]) -> Optional[str]:
        """Redact WWN identifier if configured.

        Args:
            wwn: WWN identifier string

        Returns:
            Redacted WWN or original value
        """
        if not wwn or not self.config.redact_hardware_serials:
            return wwn
        return "REDACTED"

    def redact_cpu_flags(self, flags: Optional[str]) -> Optional[str]:
        """Redact CPU flags if configured.

        Args:
            flags: CPU flags string

        Returns:
            Redacted message or original flags
        """
        if not flags or not self.config.redact_cpu_flags:
            return flags
        return "Available (details redacted for public documentation)"

    def redact_username(self, username: Optional[str]) -> Optional[str]:
        """Redact username if configured.

        System usernames like 'root@pam' are never redacted.
        Other usernames are converted to 'user1@realm', 'user2@realm', etc.

        Args:
            username: Username string (e.g., "john@pam")

        Returns:
            Redacted username or original value
        """
        if not username or not self.config.redact_usernames:
            return username

        # Never redact root@pam or root@pve
        if username.startswith('root@'):
            return username

        # Use consistent mapping for same username
        if username in self._username_map:
            return self._username_map[username]

        # Extract realm from username
        parts = username.split('@')
        realm = parts[1] if len(parts) > 1 else 'pam'

        # Create new anonymized username
        self._username_counter += 1
        redacted = f"user{self._username_counter}@{realm}"
        self._username_map[username] = redacted

        return redacted

    def redact_email(self, email: Optional[str]) -> Optional[str]:
        """Redact email address if configured.

        Args:
            email: Email address string

        Returns:
            Redacted email or original value
        """
        if not email or not self.config.redact_email_addresses:
            return email
        return "REDACTED"

    def redact_token_id(self, token_id: Optional[str]) -> Optional[str]:
        """Redact API token ID if configured.

        Args:
            token_id: Token ID string

        Returns:
            Redacted token ID or original value
        """
        if not token_id or not self.config.redact_api_tokens:
            return token_id
        return "REDACTED"

    def redact_network_interface(self, interface: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from network interface dictionary.

        Args:
            interface: Network interface dictionary with potential MAC address

        Returns:
            Interface dictionary with redacted MAC if configured
        """
        if not interface:
            return interface

        # Create a copy to avoid modifying original
        redacted = interface.copy()

        # Redact MAC addresses in various possible keys
        for key in ['hwaddr', 'mac', 'macaddr', 'hardware-address']:
            if key in redacted:
                redacted[key] = self.redact_mac_address(redacted[key])

        return redacted

    def redact_disk_info(self, disk: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from disk information dictionary.

        Args:
            disk: Disk information dictionary

        Returns:
            Disk dictionary with redacted serials/WWN if configured
        """
        if not disk:
            return disk

        # Create a copy to avoid modifying original
        redacted = disk.copy()

        # Redact serial and WWN
        if 'serial' in redacted:
            redacted['serial'] = self.redact_serial(redacted['serial'])
        if 'wwn' in redacted:
            redacted['wwn'] = self.redact_wwn(redacted['wwn'])

        return redacted

    def redact_user_info(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from user information dictionary.

        Args:
            user: User information dictionary

        Returns:
            User dictionary with redacted email/username if configured
        """
        if not user:
            return user

        # Create a copy to avoid modifying original
        redacted = user.copy()

        # Redact email
        if 'email' in redacted:
            redacted['email'] = self.redact_email(redacted['email'])

        # Redact username (userid)
        if 'userid' in redacted:
            redacted['userid'] = self.redact_username(redacted['userid'])

        return redacted

    def redact_token_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from API token information dictionary.

        Args:
            token: Token information dictionary

        Returns:
            Token dictionary with redacted ID/user if configured
        """
        if not token:
            return token

        # Create a copy to avoid modifying original
        redacted = token.copy()

        # Redact token ID
        if 'tokenid' in redacted:
            redacted['tokenid'] = self.redact_token_id(redacted['tokenid'])

        # Redact associated username
        if 'user' in redacted:
            redacted['user'] = self.redact_username(redacted['user'])

        return redacted

    def should_redact_anything(self) -> bool:
        """Check if any redaction is enabled.

        Returns:
            True if any redaction setting is enabled
        """
        return any([
            self.config.redact_mac_addresses,
            self.config.redact_hardware_serials,
            self.config.redact_api_tokens,
            self.config.redact_cpu_flags,
            self.config.redact_usernames,
            self.config.redact_email_addresses,
        ])

    def get_redaction_summary(self) -> List[str]:
        """Get list of active redaction settings.

        Returns:
            List of human-readable redaction settings that are enabled
        """
        summary = []
        if self.config.redact_mac_addresses:
            summary.append("MAC addresses")
        if self.config.redact_hardware_serials:
            summary.append("Hardware serial numbers and WWN")
        if self.config.redact_api_tokens:
            summary.append("API token IDs")
        if self.config.redact_cpu_flags:
            summary.append("CPU flags and capabilities")
        if self.config.redact_usernames:
            summary.append("Usernames (except root)")
        if self.config.redact_email_addresses:
            summary.append("Email addresses")
        return summary
