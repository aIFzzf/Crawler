"""
Configuration management implementation.
"""
from typing import Any, Dict
import json
import os
from loguru import logger
from ..interfaces import IConfigManager

class ConfigManager(IConfigManager):
    """
    Manages system configuration.
    Handles loading, updating, and accessing configuration values.
    """
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = {}
        self.config_files = {}
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.config.update(config)
            self.config_files[config_path] = config
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise
    
    def update_config(self, config_path: str, new_config: Dict[str, Any]) -> bool:
        """
        Update configuration file.
        
        Args:
            config_path: Path to configuration file
            new_config: New configuration values
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Merge with existing config
            if config_path in self.config_files:
                current_config = self.config_files[config_path].copy()
                current_config.update(new_config)
            else:
                current_config = new_config
            
            # Write to file
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=2)
            
            # Update internal state
            self.config_files[config_path] = current_config
            self.config.update(new_config)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating config {config_path}: {e}")
            return False
    
    def get_config_value(self, key: str) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Configuration value or None if not found
        """
        return self.config.get(key)
