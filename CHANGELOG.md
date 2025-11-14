# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-14

### Added
- Initial release of Proxmox MDX Documentation Generator
- Comprehensive documentation generation for Proxmox VE clusters
- Support for 32 different document types covering all infrastructure aspects
- Cluster overview documentation
- Node documentation (overview, hardware, network)
- VM documentation (overview, network, storage)
- Container documentation (overview, network)
- Storage documentation (pools, assignments)
- Network documentation (overview, IP addressing, VLANs, SDN)
- Reference documentation (firewall, users, backups, HA)
- Dual authentication support (API tokens and username/password)
- Environment-based configuration via .env file
- Automatic cross-linking between related documents
- MDX format output ready for modern documentation sites
- Graceful error handling and permission-aware operations
- Comprehensive logging to generation.log
- Support for Proxmox VE 8.x and 9.x

### Features
- 22 specialized generators for different documentation types
- 22 Jinja2 templates for MDX generation
- Type-safe data models using Python dataclasses
- Modular architecture for easy extension
- Detailed API client with retry logic
- Helper functions for formatting and parsing
- Rich YAML frontmatter in all generated documents
- Best practices and setup instructions included

### Documentation
- Comprehensive README.md with installation and usage instructions
- CONTRIBUTING.md with development guidelines
- LICENSE (MIT)
- .env.example for easy configuration

[1.0.0]: https://github.com/YOUR_USERNAME/proxdocs/releases/tag/v1.0.0
