"""Configuration management for Proxmox documentation generator."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ProxmoxConfig:
    """Configuration for Proxmox documentation generator."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Proxmox connection
        self.proxmox_host: str = os.getenv('PROXMOX_HOST', '')
        self.proxmox_api_token: Optional[str] = os.getenv('PROXMOX_API_TOKEN')
        self.proxmox_username: Optional[str] = os.getenv('PROXMOX_USERNAME')
        self.proxmox_password: Optional[str] = os.getenv('PROXMOX_PASSWORD')
        self.verify_ssl: bool = os.getenv('VERIFY_SSL', 'false').lower() == 'true'

        # Output settings
        self.output_dir: Path = Path(os.getenv('OUTPUT_DIR', 'output'))

        # Generation options
        self.include_descriptions: bool = True
        self.include_tags: bool = True

        # Validate required settings
        self._validate()

    def _validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.proxmox_host:
            raise ValueError("PROXMOX_HOST is required")

        if not self.proxmox_api_token and not (self.proxmox_username and self.proxmox_password):
            raise ValueError(
                "Either PROXMOX_API_TOKEN or both PROXMOX_USERNAME and "
                "PROXMOX_PASSWORD must be provided"
            )

    @property
    def auth_method(self) -> str:
        """Return the authentication method being used."""
        return "token" if self.proxmox_api_token else "password"
