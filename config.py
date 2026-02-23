#!/usr/bin/env python3
"""
Configuration loader for Azure AD / Dataverse credentials
Loads credentials from .env file or environment variables
"""

import os
from pathlib import Path

def load_config():
    """
    Load configuration from .env file if it exists
    Returns dict with credentials
    """
    # Try to load from .env file
    env_file = Path(__file__).parent / '.env'

    if env_file.exists():
        # Simple .env parser (no external dependencies)
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

        return {
            'TENANT_ID': config.get('TENANT_ID'),
            'CLIENT_ID': config.get('CLIENT_ID'),
            'CLIENT_SECRET': config.get('CLIENT_SECRET'),
            'ORG_URL': config.get('ORG_URL'),
            'API_URL': f"{config.get('ORG_URL')}/api/data/v9.2"
        }
    else:
        # Fall back to environment variables
        org_url = os.getenv('ORG_URL', 'https://org3a2a4fe5.crm6.dynamics.com')
        return {
            'TENANT_ID': os.getenv('TENANT_ID'),
            'CLIENT_ID': os.getenv('CLIENT_ID'),
            'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
            'ORG_URL': org_url,
            'API_URL': f"{org_url}/api/data/v9.2"
        }

# Global config instance
CONFIG = load_config()

# Convenient accessors
TENANT_ID = CONFIG['TENANT_ID']
CLIENT_ID = CONFIG['CLIENT_ID']
CLIENT_SECRET = CONFIG['CLIENT_SECRET']
ORG_URL = CONFIG['ORG_URL']
API_URL = CONFIG['API_URL']
