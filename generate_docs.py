#!/usr/bin/env python3
"""
Proxmox MDX Documentation Generator

Main entry point for generating infrastructure documentation from Proxmox API.
"""

import logging
import sys
from pathlib import Path

from src.config import ProxmoxConfig
from src.api_client import ProxmoxAPIClient
from src.generators import (
    ClusterOverviewGenerator,
    NodeOverviewGenerator,
    NodeHardwareGenerator,
    NodeNetworkGenerator,
    VMIndexGenerator,
    VMOverviewGenerator,
    VMNetworkGenerator,
    VMStorageGenerator,
    ContainerIndexGenerator,
    ContainerOverviewGenerator,
    ContainerNetworkGenerator,
    StorageIndexGenerator,
    StoragePoolGenerator,
    StorageAssignmentsGenerator,
    NetworkOverviewGenerator,
    IPAddressingGenerator,
    VLANGenerator,
    SDNGenerator,
    FirewallGenerator,
    UsersPermissionsGenerator,
    BackupPoliciesGenerator,
    HAGenerator,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('generation.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to generate documentation."""
    print("=" * 70)
    print("Proxmox MDX Documentation Generator")
    print("=" * 70)
    print()

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = ProxmoxConfig()
        logger.info(f"✓ Configuration loaded")
        logger.info(f"  Host: {config.proxmox_host}")
        logger.info(f"  Auth method: {config.auth_method}")
        logger.info(f"  Output directory: {config.output_dir}")
        print()

        # Initialize API client
        logger.info("Initializing Proxmox API client...")
        api = ProxmoxAPIClient(
            host=config.proxmox_host,
            api_token=config.proxmox_api_token,
            username=config.proxmox_username,
            password=config.proxmox_password,
            verify_ssl=config.verify_ssl
        )

        # Authenticate
        if not api.authenticate():
            logger.error("Failed to authenticate with Proxmox API")
            sys.exit(1)
        print()

        # Create output directory
        config.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {config.output_dir.absolute()}")
        print()

        # Generate documentation
        logger.info("Starting documentation generation...")
        print()

        # Get list of nodes
        logger.info("Fetching node list...")
        nodes = api.get_nodes()
        if not nodes:
            logger.error("Failed to fetch nodes list")
            sys.exit(1)

        node_names = [node.get('node') for node in nodes]
        logger.info(f"Found {len(node_names)} node(s): {', '.join(node_names)}")
        print()

        # Get list of VMs (type='qemu' not 'vm' to exclude containers)
        logger.info("Fetching VM list...")
        all_resources = api.get_cluster_resources()
        if all_resources is None:
            logger.warning("Failed to fetch resources list, skipping VM documentation")
            vms = []
        else:
            # Filter only QEMU VMs (not LXC containers which may show up as 'vm')
            vms = [r for r in all_resources if r.get('type') == 'qemu']
            logger.info(f"Found {len(vms)} VM(s)")
            for vm in vms:
                logger.info(f"  - VM {vm.get('vmid')}: {vm.get('name', 'unnamed')} on {vm.get('node')}")
        print()

        # Build list of generators
        generators = [
            # Cluster overview
            ClusterOverviewGenerator(api, config.output_dir),
        ]

        # Add node generators for each node
        for node_name in node_names:
            generators.extend([
                NodeOverviewGenerator(api, config.output_dir, node_name),
                NodeHardwareGenerator(api, config.output_dir, node_name),
                NodeNetworkGenerator(api, config.output_dir, node_name),
            ])

        # Add VM generators
        if vms:
            # VM index
            generators.append(VMIndexGenerator(api, config.output_dir))

            # Per-VM generators
            for vm in vms:
                vmid = vm.get('vmid')
                node_name = vm.get('node')
                if vmid and node_name:
                    generators.extend([
                        VMOverviewGenerator(api, config.output_dir, node_name, vmid),
                        VMNetworkGenerator(api, config.output_dir, node_name, vmid),
                        VMStorageGenerator(api, config.output_dir, node_name, vmid),
                    ])

        # Get list of containers
        logger.info("Fetching container list...")
        if all_resources is None:
            logger.warning("Failed to fetch resources list, skipping container documentation")
            containers = []
        else:
            # Filter only LXC containers
            containers = [r for r in all_resources if r.get('type') == 'lxc']
            logger.info(f"Found {len(containers)} container(s)")
            for ct in containers:
                logger.info(f"  - CT {ct.get('vmid')}: {ct.get('name', 'unnamed')} on {ct.get('node')}")
        print()

        # Add container generators
        if containers:
            # Container index
            generators.append(ContainerIndexGenerator(api, config.output_dir))

            # Per-container generators
            for ct in containers:
                vmid = ct.get('vmid')
                node_name = ct.get('node')
                if vmid and node_name:
                    generators.extend([
                        ContainerOverviewGenerator(api, config.output_dir, node_name, vmid),
                        ContainerNetworkGenerator(api, config.output_dir, node_name, vmid),
                    ])

        # Get list of storage pools
        logger.info("Fetching storage pool list...")
        storage_list = api.get('/storage')
        if storage_list:
            storage_ids = [pool.get('storage') for pool in storage_list if pool.get('storage')]
            logger.info(f"Found {len(storage_ids)} storage pool(s): {', '.join(storage_ids)}")
        else:
            logger.warning("Failed to fetch storage list, skipping storage documentation")
            storage_ids = []
        print()

        # Add storage generators
        if storage_ids:
            # Storage index
            generators.append(StorageIndexGenerator(api, config.output_dir))

            # Per-storage generators
            for storage_id in storage_ids:
                generators.append(StoragePoolGenerator(api, config.output_dir, storage_id))

            # Storage assignments
            generators.append(StorageAssignmentsGenerator(api, config.output_dir))

        # Add network generators
        logger.info("Adding network documentation generators...")
        generators.extend([
            NetworkOverviewGenerator(api, config.output_dir),
            IPAddressingGenerator(api, config.output_dir),
            VLANGenerator(api, config.output_dir),
            SDNGenerator(api, config.output_dir),
        ])
        print()

        # Add reference generators
        logger.info("Adding reference documentation generators...")
        generators.extend([
            FirewallGenerator(api, config.output_dir),
            UsersPermissionsGenerator(api, config.output_dir),
            BackupPoliciesGenerator(api, config.output_dir),
            HAGenerator(api, config.output_dir),
        ])
        print()

        generated_files = []
        failed = []

        # Generate all documents
        for generator in generators:
            result = generator.generate()
            if result:
                generated_files.append(result)
            else:
                failed.append(generator.__class__.__name__)

        # Summary
        print()
        print("=" * 70)
        print("Generation Summary")
        print("=" * 70)
        print(f"✓ Successfully generated: {len(generated_files)} document(s)")
        if failed:
            print(f"✗ Failed: {len(failed)} document(s)")
            for name in failed:
                print(f"  - {name}")

        print()
        print("Generated files:")
        for file_path in generated_files:
            print(f"  - {file_path}")

        print()
        print(f"Documentation generated in: {config.output_dir.absolute()}")
        print()

        # Exit code
        sys.exit(0 if not failed else 1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
