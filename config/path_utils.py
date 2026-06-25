# config/path_utils.py
# Centralised path resolution for both development and PyInstaller-frozen environments.

import os
import re
import sys

_TENANT_ID_RE = re.compile(r'^[A-Za-z0-9_.\-\s]{1,64}$')

def is_frozen():
    """Returns True when running inside a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_resource_path(relative_path=""):
    """
    Return the absolute path to a **read-only** resource bundled with the app.

    When frozen (PyInstaller):
        Uses sys._MEIPASS which points to the _internal folder in PyInstaller 6+
    When running from source:
        <project_root>/<relative_path>
    """
    if is_frozen():
        base_path = sys._MEIPASS
    else:
        # Development: project root is one level up from config/
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    if relative_path:
        return os.path.join(base_path, relative_path)
    return base_path

class ConfigManager:
    """Singleton hermetico para el manejo del Tenant Activo en arquitectura B2B"""
    _active_tenant_id = None
    
    @classmethod
    def set_active_tenant(cls, tenant_id: str):
        if not isinstance(tenant_id, str) or not _TENANT_ID_RE.match(tenant_id):
            raise ValueError(
                "Invalid tenant ID: must be 1-64 characters (alphanumeric, underscore, hyphen, dot)."
            )
        cls._active_tenant_id = tenant_id
        
    @classmethod
    def get_active_tenant(cls) -> str:
        if cls._active_tenant_id is None:
            raise ValueError("No B2B Tenant has been selected yet. Bootloader failed.")
        return cls._active_tenant_id

    @classmethod
    def get_appdata_path(cls, *subdirs):
        """
        Base global folder (for licenses, settings) -> %APPDATA%/OficinaEficiencia/
        """
        base = os.path.join(
            os.environ.get('APPDATA', os.path.expanduser('~')),
            'OficinaEficiencia'
        )
        path = os.path.join(base, *subdirs) if subdirs else base
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_tenant_path(cls, *subdirs):
        """
        Isolated Tenant folder -> %APPDATA%/OficinaEficiencia/Tenants/[TenantID]/
        """
        tenant_base = cls.get_appdata_path("Tenants", cls.get_active_tenant())
        path = os.path.join(tenant_base, *subdirs) if subdirs else tenant_base
        os.makedirs(path, exist_ok=True)
        return path

