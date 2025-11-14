# Contributing to Proxmox MDX Documentation Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/proxdocs.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

```bash
# Create virtual environment
python3 -m venv proxmox-docs-env
source proxmox-docs-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env with your Proxmox credentials

# Run the generator
python generate_docs.py
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all classes and functions
- Keep functions focused and modular
- Use meaningful variable and function names

### Example

```python
def my_function(param1: str, param2: int) -> Optional[Dict[str, Any]]:
    """Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing results, or None if failed
    """
    # Implementation
    pass
```

## Adding New Generators

To add a new generator:

1. Create generator class in `src/generators/`
2. Extend `BaseDocumentGenerator`
3. Implement required methods:
   - `collect_data()` - Fetch data from Proxmox API
   - `get_template_name()` - Return template filename
   - `get_output_path()` - Return output file path
4. Create Jinja2 template in `src/templates/`
5. Export generator in `src/generators/__init__.py`
6. Add generator to `generate_docs.py`
7. Test thoroughly
8. Update README.md if needed

### Example Generator

```python
from .base import BaseDocumentGenerator
from pathlib import Path
from typing import Dict, Any, Optional

class MyNewGenerator(BaseDocumentGenerator):
    """Generator for my new documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from Proxmox API."""
        try:
            data = self.api.get('/my/endpoint')
            return {'my_data': data}
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'my_new_template.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'my_category' / 'index.mdx'
```

## Testing

Before submitting a pull request:

1. Test with your Proxmox cluster
2. Verify all generated MDX files are valid
3. Check cross-links work correctly
4. Ensure no errors in `generation.log`
5. Test with both API token and username/password authentication

## Pull Request Guidelines

- Keep pull requests focused on a single feature or fix
- Update README.md if adding new features
- Update CHANGELOG.md with your changes
- Ensure code follows style guidelines
- Write clear commit messages
- Test thoroughly before submitting

### Commit Message Format

```
type: brief description

Longer description if needed
- bullet point details
- additional context
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Reporting Issues

When reporting issues, please include:

- Proxmox VE version
- Python version
- Error messages from `generation.log`
- Steps to reproduce
- Expected vs actual behavior

## Questions?

Feel free to open an issue for:
- Feature requests
- Bug reports
- Documentation improvements
- Questions about the code

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
