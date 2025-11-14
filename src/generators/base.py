"""Base class for all document generators."""

from abc import ABC, abstractmethod
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from src.config import ProxmoxConfig
from src.redaction import Redactor

logger = logging.getLogger(__name__)


class BaseDocumentGenerator(ABC):
    """Base class for all documentation generators."""

    def __init__(self, api_client, config: ProxmoxConfig, output_dir: Path):
        """Initialize generator.

        Args:
            api_client: ProxmoxAPIClient instance
            config: ProxmoxConfig instance with settings
            output_dir: Base output directory path
        """
        self.api = api_client
        self.config = config
        self.output_dir = Path(output_dir)
        self.redactor = Redactor(config)

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / 'templates'
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Add custom filters
        self.template_env.filters['format_bytes'] = self._format_bytes
        self.template_env.filters['format_memory'] = self._format_memory

    @staticmethod
    def _format_bytes(bytes_value: Optional[int]) -> str:
        """Template filter for formatting bytes."""
        from src.utils import format_bytes
        return format_bytes(bytes_value)

    @staticmethod
    def _format_memory(mb_value: Optional[int]) -> str:
        """Template filter for formatting memory."""
        from src.utils import format_memory_mb
        return format_memory_mb(mb_value)

    @abstractmethod
    def collect_data(self) -> Dict[str, Any]:
        """Collect data from API.

        Must be implemented by subclasses.

        Returns:
            Dictionary of data to pass to template
        """
        pass

    @abstractmethod
    def get_template_name(self) -> str:
        """Get template filename.

        Must be implemented by subclasses.

        Returns:
            Template filename (e.g., 'cluster_overview.j2')
        """
        pass

    @abstractmethod
    def get_output_path(self) -> Path:
        """Get output file path.

        Must be implemented by subclasses.

        Returns:
            Full path where the generated file should be written
        """
        pass

    def generate(self) -> Optional[Path]:
        """Generate documentation file.

        Main method that orchestrates the generation process:
        1. Collects data from API
        2. Adds common metadata
        3. Renders template
        4. Writes to file

        Returns:
            Path to generated file, or None if generation failed
        """
        try:
            logger.info(f"📄 Generating {self.__class__.__name__}...")

            # Collect data
            data = self.collect_data()
            if data is None:
                logger.error(f"Failed to collect data for {self.__class__.__name__}")
                return None

            # Add common metadata
            data['generated'] = datetime.utcnow().isoformat() + 'Z'

            # Render template
            template = self.template_env.get_template(self.get_template_name())
            content = template.render(**data)

            # Write to file
            output_path = self.get_output_path()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')

            logger.info(f"✓ Generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"✗ Failed to generate {self.__class__.__name__}: {e}", exc_info=True)
            return None
