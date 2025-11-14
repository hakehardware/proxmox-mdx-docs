"""Reference documentation generators."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDocumentGenerator

logger = logging.getLogger(__name__)


class FirewallGenerator(BaseDocumentGenerator):
    """Generator for cluster firewall rules documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect firewall rules from cluster.

        Returns:
            Dictionary containing firewall rules
        """
        try:
            # Get cluster firewall options
            try:
                firewall_options = self.api.get('/cluster/firewall/options')
            except:
                firewall_options = {}

            # Get cluster firewall rules
            try:
                cluster_rules = self.api.get('/cluster/firewall/rules')
            except:
                cluster_rules = []

            # Get security groups
            try:
                security_groups = self.api.get('/cluster/firewall/groups')
            except:
                security_groups = []

            # Get aliases (IP aliases for firewall rules)
            try:
                aliases = self.api.get('/cluster/firewall/aliases')
            except:
                aliases = []

            # Get IPSets
            try:
                ipsets = self.api.get('/cluster/firewall/ipset')
            except:
                ipsets = []

            firewall_enabled = firewall_options.get('enable', 0) == 1 if firewall_options else False

            return {
                'firewall_enabled': firewall_enabled,
                'firewall_options': firewall_options if firewall_options else {},
                'cluster_rules': cluster_rules if cluster_rules else [],
                'security_groups': security_groups if security_groups else [],
                'aliases': aliases if aliases else [],
                'ipsets': ipsets if ipsets else [],
                'total_rules': len(cluster_rules) if cluster_rules else 0,
                'total_groups': len(security_groups) if security_groups else 0,
                'total_aliases': len(aliases) if aliases else 0,
                'total_ipsets': len(ipsets) if ipsets else 0,
            }

        except Exception as e:
            logger.error(f"Error collecting firewall data: {e}", exc_info=True)
            return {
                'firewall_enabled': False,
                'firewall_options': {},
                'cluster_rules': [],
                'security_groups': [],
                'aliases': [],
                'ipsets': [],
                'total_rules': 0,
                'total_groups': 0,
                'total_aliases': 0,
                'total_ipsets': 0,
            }

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'firewall.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'reference' / 'firewall.mdx'


class UsersPermissionsGenerator(BaseDocumentGenerator):
    """Generator for users and permissions documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect users and permissions from cluster.

        Returns:
            Dictionary containing user and permission information
        """
        try:
            # Get users
            try:
                users = self.api.get('/access/users')
            except:
                users = []

            # Get groups
            try:
                groups = self.api.get('/access/groups')
            except:
                groups = []

            # Get roles
            try:
                roles = self.api.get('/access/roles')
            except:
                roles = []

            # Get ACLs
            try:
                acls = self.api.get('/access/acl')
            except:
                acls = []

            # Get API tokens
            api_tokens = []
            for user in users:
                userid = user.get('userid')
                if userid:
                    try:
                        tokens = self.api.get(f'/access/users/{userid}/token')
                        if tokens:
                            for token in tokens:
                                token_info = token.copy()
                                token_info['user'] = userid
                                api_tokens.append(token_info)
                    except:
                        pass

            # Group users by realm
            users_by_realm = {}
            for user in users:
                realm = userid.split('@')[1] if '@' in user.get('userid', '') else 'unknown'
                if realm not in users_by_realm:
                    users_by_realm[realm] = []
                users_by_realm[realm].append(user)

            return {
                'users': users if users else [],
                'groups': groups if groups else [],
                'roles': roles if roles else [],
                'acls': acls if acls else [],
                'api_tokens': api_tokens,
                'users_by_realm': users_by_realm,
                'total_users': len(users) if users else 0,
                'total_groups': len(groups) if groups else 0,
                'total_roles': len(roles) if roles else 0,
                'total_acls': len(acls) if acls else 0,
                'total_tokens': len(api_tokens),
            }

        except Exception as e:
            logger.error(f"Error collecting users/permissions data: {e}", exc_info=True)
            return {
                'users': [],
                'groups': [],
                'roles': [],
                'acls': [],
                'api_tokens': [],
                'users_by_realm': {},
                'total_users': 0,
                'total_groups': 0,
                'total_roles': 0,
                'total_acls': 0,
                'total_tokens': 0,
            }

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'users_permissions.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'reference' / 'users-permissions.mdx'


class BackupPoliciesGenerator(BaseDocumentGenerator):
    """Generator for backup policies documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect backup policies from cluster.

        Returns:
            Dictionary containing backup configuration
        """
        try:
            # Get backup jobs
            try:
                backup_jobs = self.api.get('/cluster/backup')
            except:
                backup_jobs = []

            # Get backup storages (storage pools that support backups)
            backup_storages = []
            try:
                storage_list = self.api.get('/storage')
                if storage_list:
                    for pool in storage_list:
                        content_types = pool.get('content', '').split(',')
                        if 'backup' in content_types:
                            backup_storages.append(pool)
            except:
                pass

            # Group backup jobs by storage
            jobs_by_storage = {}
            for job in backup_jobs:
                storage = job.get('storage', 'unknown')
                if storage not in jobs_by_storage:
                    jobs_by_storage[storage] = []
                jobs_by_storage[storage].append(job)

            # Group backup jobs by schedule
            jobs_by_schedule = {}
            for job in backup_jobs:
                schedule = job.get('schedule', 'manual')
                if schedule not in jobs_by_schedule:
                    jobs_by_schedule[schedule] = []
                jobs_by_schedule[schedule].append(job)

            return {
                'backup_jobs': backup_jobs if backup_jobs else [],
                'backup_storages': backup_storages,
                'jobs_by_storage': jobs_by_storage,
                'jobs_by_schedule': jobs_by_schedule,
                'total_jobs': len(backup_jobs) if backup_jobs else 0,
                'total_storages': len(backup_storages),
            }

        except Exception as e:
            logger.error(f"Error collecting backup policies data: {e}", exc_info=True)
            return {
                'backup_jobs': [],
                'backup_storages': [],
                'jobs_by_storage': {},
                'jobs_by_schedule': {},
                'total_jobs': 0,
                'total_storages': 0,
            }

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'backup_policies.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'reference' / 'backup-policies.mdx'


class HAGenerator(BaseDocumentGenerator):
    """Generator for High Availability configuration documentation."""

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect HA configuration from cluster.

        Returns:
            Dictionary containing HA information
        """
        try:
            # Check if HA is configured
            ha_enabled = False
            ha_groups = []
            ha_resources = []

            try:
                # Get HA status
                ha_status = self.api.get('/cluster/ha/status/current')
                if ha_status:
                    ha_enabled = True
            except:
                pass

            try:
                # Get HA groups
                ha_groups = self.api.get('/cluster/ha/groups')
            except:
                pass

            try:
                # Get HA resources
                ha_resources = self.api.get('/cluster/ha/resources')
            except:
                pass

            # Group resources by group
            resources_by_group = {}
            for resource in ha_resources:
                group = resource.get('group', 'default')
                if group not in resources_by_group:
                    resources_by_group[group] = []
                resources_by_group[group].append(resource)

            return {
                'ha_enabled': ha_enabled or bool(ha_groups) or bool(ha_resources),
                'ha_groups': ha_groups if ha_groups else [],
                'ha_resources': ha_resources if ha_resources else [],
                'resources_by_group': resources_by_group,
                'total_groups': len(ha_groups) if ha_groups else 0,
                'total_resources': len(ha_resources) if ha_resources else 0,
            }

        except Exception as e:
            logger.error(f"Error collecting HA data: {e}", exc_info=True)
            return {
                'ha_enabled': False,
                'ha_groups': [],
                'ha_resources': [],
                'resources_by_group': {},
                'total_groups': 0,
                'total_resources': 0,
            }

    def get_template_name(self) -> str:
        """Get template filename."""
        return 'ha.j2'

    def get_output_path(self) -> Path:
        """Get output file path."""
        return self.output_dir / 'reference' / 'ha.mdx'
