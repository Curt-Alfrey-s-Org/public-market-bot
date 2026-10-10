"""
Internet Access Control Module
Allows users to allow/forbid internet connectivity for bots
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class InternetAccessControl:
    def __init__(self, config_dir: str = "."):
        """Initialize internet access control.
        
        Args:
            config_dir: Directory to store internet access config
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / ".internet_access"
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create default config if it doesn't exist."""
        if not self.config_file.exists():
            self.set_internet_access(True)  # Default: allow internet
    
    def set_internet_access(self, allowed: bool) -> dict:
        """Set whether internet access is allowed.
        
        Args:
            allowed: True to allow internet access, False to forbid
            
        Returns:
            Updated configuration
        """
        config = {
            "allowed": allowed,
            "updated_at": datetime.utcnow().isoformat(),
            "allowed_str": "ALLOWED" if allowed else "FORBIDDEN"
        }
        
        try:
            self._apply_firewall_rule(allowed)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Internet access: {config['allowed_str']}")
            return config
        except Exception as e:
            logger.error(f"Failed to set internet access: {e}")
            raise
    
    def get_internet_access(self) -> dict:
        """Get current internet access setting.
        
        Returns:
            Current configuration with 'allowed' boolean and 'allowed_str' status
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                config['allowed_str'] = "ALLOWED" if config.get('allowed', True) else "FORBIDDEN"
                return config
            else:
                return self.set_internet_access(True)  # Default to allowed
        except Exception as e:
            logger.error(f"Failed to read internet access config: {e}")
            return {"allowed": True, "allowed_str": "ALLOWED", "error": str(e)}
    
    def is_allowed(self) -> bool:
        """Check if internet access is currently allowed.
        
        Returns:
            True if allowed, False if forbidden
        """
        config = self.get_internet_access()
        return config.get('allowed', True)
    
    def enforce_access(self) -> None:
        """Enforce internet access restrictions.
        
        If internet access is forbidden, this should be checked before
        making external API calls. Raises an exception if forbidden.
        """
        if not self.is_allowed():
            raise PermissionError(
                "Internet access is currently FORBIDDEN. "
                "Cannot connect to external services. "
                "Use the dashboard to allow internet access."
            )

    def _apply_firewall_rule(self, allowed: bool) -> None:
        """Apply or remove the outbound firewall rule for this user.

        Uses iptables to block all non-private outbound traffic for the
        current user. This keeps LAN/localhost access working while
        forbidding public internet access.
        
        Since iptables doesn't support multiple ! -d flags in one rule,
        we create separate rules to ACCEPT private ranges first, then
        REJECT everything else from this user.
        """
        uid = os.getuid()
        comment = "bot-internet-block"
        
        # Rules to accept private/local networks (evaluated first)
        accept_rules = [
            ["-m", "owner", "--uid-owner", str(uid), "-d", "127.0.0.0/8", "-m", "comment", "--comment", f"{comment}-allow-lo", "-j", "ACCEPT"],
            ["-m", "owner", "--uid-owner", str(uid), "-d", "10.0.0.0/8", "-m", "comment", "--comment", f"{comment}-allow-10", "-j", "ACCEPT"],
            ["-m", "owner", "--uid-owner", str(uid), "-d", "172.16.0.0/12", "-m", "comment", "--comment", f"{comment}-allow-172", "-j", "ACCEPT"],
            ["-m", "owner", "--uid-owner", str(uid), "-d", "192.168.0.0/16", "-m", "comment", "--comment", f"{comment}-allow-192", "-j", "ACCEPT"],
        ]
        
        # Final rule to reject all other traffic from this user
        reject_rule = [
            "-m", "owner", "--uid-owner", str(uid),
            "-m", "comment", "--comment", comment,
            "-j", "REJECT",
        ]
        
        # Apply or remove all rules
        if allowed:
            # Remove block rules (reverse order)
            self._iptables_toggle_rule(True, reject_rule)
            for rule in reversed(accept_rules):
                self._iptables_toggle_rule(True, rule)
        else:
            # Add accept rules first, then reject rule
            for rule in accept_rules:
                self._iptables_toggle_rule(False, rule)
            self._iptables_toggle_rule(False, reject_rule)
    
    def _iptables_toggle_rule(self, remove: bool, rule: list) -> None:
        """Add or remove a single iptables rule."""
        iptables = os.getenv("IPTABLES_PATH", "/usr/sbin/iptables")
        use_sudo = os.getenv("IPTABLES_USE_SUDO", "true").lower() == "true"
        base_cmd = [iptables]
        if use_sudo:
            base_cmd = ["sudo", iptables]

        check_cmd = base_cmd + ["-C", "OUTPUT"] + rule
        add_cmd = base_cmd + ["-A", "OUTPUT"] + rule
        del_cmd = base_cmd + ["-D", "OUTPUT"] + rule

        if remove:
            # Remove rule if it exists
            if self._run_iptables(check_cmd):
                self._run_iptables(del_cmd, allow_fail=True)
        else:
            # Add rule if it doesn't exist
            if not self._run_iptables(check_cmd):
                self._run_iptables(add_cmd, allow_fail=False)

    def _iptables_toggle(self, allowed: bool, rule: list) -> None:
        """Add or remove an iptables rule for the current user.

        Raises RuntimeError if iptables cannot apply the change.
        """
        iptables = os.getenv("IPTABLES_PATH", "/usr/sbin/iptables")
        use_sudo = os.getenv("IPTABLES_USE_SUDO", "true").lower() == "true"
        base_cmd = [iptables]
        if use_sudo:
            base_cmd = ["sudo", iptables]

        check_cmd = base_cmd + ["-C", "OUTPUT"] + rule
        add_cmd = base_cmd + ["-A", "OUTPUT"] + rule
        del_cmd = base_cmd + ["-D", "OUTPUT"] + rule

        if allowed:
            if self._run_iptables(check_cmd):
                if not self._run_iptables(del_cmd, allow_fail=True):
                    raise RuntimeError("Failed to remove internet block rule")
        else:
            if not self._run_iptables(check_cmd):
                if not self._run_iptables(add_cmd, allow_fail=False):
                    raise RuntimeError("Failed to apply internet block rule")

    def _run_iptables(self, cmd: list, allow_fail: bool = False) -> bool:
        """Run iptables command and return True on success."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return True
            if not allow_fail:
                logger.error(f"iptables error: {result.stderr.strip()}")
            return False
        except FileNotFoundError:
            logger.error("iptables not found. Set IPTABLES_PATH or install iptables.")
            return False
        except Exception as e:
            logger.error(f"iptables execution failed: {e}")
            return False
