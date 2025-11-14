# Proxmox MDX Documentation Generator

Automatically generate comprehensive MDX documentation for your Proxmox VE infrastructure.

## Overview

This tool connects to your Proxmox VE cluster via API and generates **32 interconnected MDX documentation files** covering all aspects of your infrastructure:

- ✅ Cluster overview
- ✅ Node documentation (hardware, network)
- ✅ VM documentation (config, network, storage)
- ✅ Container documentation (config, network)
- ✅ Storage documentation (pools, assignments)
- ✅ Network documentation (topology, IP addressing, VLANs, SDN)
- ✅ Reference documentation (firewall, users, backups, HA)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Access to Proxmox VE API
- API token or username/password credentials

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd proxdocs
```

2. Create virtual environment:
```bash
python3 -m venv proxmox-docs-env
source proxmox-docs-env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Proxmox credentials
```

### Configuration

Edit `.env` file with your Proxmox details:

```bash
# Proxmox API Configuration
PROXMOX_HOST=192.168.10.10

# Authentication (use ONE method)
# Method 1: API Token (Recommended)
PROXMOX_API_TOKEN=USER@REALM!TOKENID=UUID

# Method 2: Username/Password (Alternative)
#PROXMOX_USERNAME=root@pam
#PROXMOX_PASSWORD=yourpassword

# Settings
VERIFY_SSL=false
OUTPUT_DIR=output
```

### Usage

Generate documentation:

```bash
source proxmox-docs-env/bin/activate
python generate_docs.py
```

Output will be in the `output/` directory with 32 MDX files.

## Generated Documentation

### File Structure

```
output/
├── index.mdx                         # Cluster overview
├── nodes/                            # Node documentation (9 files)
│   └── {node}/
│       ├── overview.mdx
│       ├── hardware.mdx
│       └── network.mdx
├── virtual-machines/                 # VM documentation (7 files)
│   ├── index.mdx
│   └── {vmid}-{name}/
│       ├── overview.mdx
│       ├── network.mdx
│       └── storage.mdx
├── containers/                       # Container documentation (5 files)
│   ├── index.mdx
│   └── {ctid}-{hostname}/
│       ├── overview.mdx
│       └── network.mdx
├── storage/                          # Storage documentation (2 files)
│   ├── index.mdx
│   └── assignments.mdx
├── network/                          # Network documentation (4 files)
│   ├── index.mdx
│   ├── ip-addressing.mdx
│   ├── vlans.mdx
│   └── sdn.mdx
└── reference/                        # Reference documentation (4 files)
    ├── firewall.mdx
    ├── users-permissions.mdx
    ├── backup-policies.mdx
    └── ha.mdx
```

## Features

### Comprehensive Coverage

- **Infrastructure**: All nodes with hardware and network details
- **Workloads**: All VMs and containers with complete configuration
- **Resources**: Storage pools, network topology, IP addressing
- **Management**: Firewall rules, users, backup policies, HA config

### Smart Documentation

- **Cross-linking**: All documents link to related resources
- **MDX Format**: Ready for modern documentation sites
- **Rich Metadata**: YAML frontmatter in all files
- **Best Practices**: Includes setup guides and recommendations

### Robust Operation

- **Error Handling**: Gracefully handles API errors and missing data
- **Permission Aware**: Adapts to available API permissions
- **Dual Authentication**: Supports API tokens and username/password
- **Detailed Logging**: Complete logs in `generation.log`

## Automation

### Schedule Regular Updates

Add to crontab for daily documentation updates:

```bash
# Update documentation daily at 6 AM
0 6 * * * cd /path/to/proxdocs && source proxmox-docs-env/bin/activate && python generate_docs.py
```

### Integration with Documentation Sites

The generated MDX files work with:

- **Docusaurus** - React-based documentation
- **Next.js** - Built-in MDX support
- **Astro** - MDX content collections
- **Gatsby** - MDX plugin

## API Permissions

### Required Permissions (Minimum)

The tool requires these permissions to function:
- `VM.Audit` - Read VM configurations
- `Datastore.Audit` - Read storage information
- `Sys.Audit` - Read system information

### Optional Permissions (Enhanced Features)

For complete documentation, grant these additional permissions:
- `Datastore.Allocate` - Read detailed storage pool configs

### Creating API Token (Recommended)

1. Log into Proxmox web UI
2. Navigate to Datacenter → Permissions → API Tokens
3. Click "Add"
4. Fill in:
   - **User**: Select user
   - **Token ID**: e.g., "documentation"
   - **Privilege Separation**: Uncheck (to inherit user permissions)
5. Copy the token UUID (shown only once!)
6. Add to `.env` as `PROXMOX_API_TOKEN`

## Troubleshooting

### Common Issues

**"Failed to authenticate"**
- Check `PROXMOX_HOST` is correct
- Verify API token or username/password
- Ensure user has necessary permissions

**"Permission check failed"**
- Some features need additional API permissions
- Tool will continue with available data
- See "API Permissions" section

**"QEMU guest agent is not running"**
- Expected if guest agent not installed in VMs
- Tool documents configured network settings instead

**SSL Certificate Errors**
- Set `VERIFY_SSL=false` for self-signed certificates

### Debug Logging

Check `generation.log` for detailed information about the generation process.

## Documentation Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Cluster** | 1 | Overall cluster status and summary |
| **Nodes** | 9 | Overview, hardware specs, network config (3 nodes) |
| **VMs** | 7 | Configuration, network, storage + index |
| **Containers** | 5 | Configuration, network + index |
| **Storage** | 2 | Pool overview, VM/CT assignments |
| **Network** | 4 | Topology, IP plan, VLANs, SDN |
| **Reference** | 4 | Firewall, users, backups, HA |
| **TOTAL** | **32** | Complete infrastructure documentation |

## Architecture

### Code Structure

```
src/
├── config.py              # Configuration management
├── api_client.py          # Proxmox API client
├── models.py              # Data models
├── utils.py               # Helper functions
├── generators/            # Document generators (22 total)
│   ├── base.py            # Base generator class
│   ├── cluster.py         # 1 generator
│   ├── node.py            # 3 generators
│   ├── vm.py              # 4 generators
│   ├── container.py       # 3 generators
│   ├── storage.py         # 3 generators
│   ├── network.py         # 4 generators
│   └── reference.py       # 4 generators
└── templates/             # Jinja2 templates (22 files)
```

### How It Works

1. **Authenticate** with Proxmox API (token or password)
2. **Discover** all resources (nodes, VMs, containers, storage)
3. **Collect** data via ~150 API calls
4. **Generate** MDX files using Jinja2 templates
5. **Write** documentation to output directory

Generation time: ~15-17 seconds for complete infrastructure.

## What Gets Documented

### Infrastructure
- Cluster name, version, quorum status
- Node hardware (CPU, memory, disks, PCI devices)
- Node network (interfaces, bridges, bonds)

### Workloads
- VM configuration, network interfaces, storage disks
- Container configuration, features, mount points
- Static IP addresses and DHCP assignments

### Resources
- Storage pools (types, capacity, usage)
- Storage assignments (which VMs/CTs use which pools)
- Network topology and IP addressing plan
- VLANs and SDN configuration

### Management
- Firewall rules (cluster and per-resource)
- Users, groups, roles, and permissions
- Backup jobs and schedules
- High availability configuration

## Development

### Adding Custom Generators

1. Create new generator class in `src/generators/`
2. Extend `BaseDocumentGenerator`
3. Implement required methods
4. Create Jinja2 template in `src/templates/`
5. Add generator to `generate_docs.py`

See existing generators for examples.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions welcome! Please fork and submit pull requests.

## Credits

Built with Python, Requests, and Jinja2.

---

**Status:** Production Ready
**Version:** 1.0.0
**Documentation Files:** 32 MDX files
**Code:** ~4,800 lines of Python + templates
