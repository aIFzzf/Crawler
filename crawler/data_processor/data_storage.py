"""
Data storage implementation.
"""
import os
import json
from typing import Dict, Any, List
import aiofiles
from loguru import logger
from ..interfaces import IDataStorage

class DataStorage(IDataStorage):
    """
    Handles data storage and retrieval.
    """
    
    def __init__(self, storage_dir: str):
        """
        Initialize data storage.
        
        Args:
            storage_dir: Directory for storing data
        """
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_category_path(self, category: str) -> str:
        """Get path for category file."""
        return os.path.join(self.storage_dir, f"{category}.json")
    
    async def save(self, data: Dict[str, Any], category: str) -> bool:
        """
        Save data to storage.
        
        Args:
            data: Data to save
            category: Category label for the data
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            category_path = self._get_category_path(category)
            
            # Load existing data
            existing_data = []
            if os.path.exists(category_path):
                async with aiofiles.open(category_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content:
                        existing_data = json.loads(content)
            
            # Append new data
            existing_data.append(data)
            
            # Save updated data
            async with aiofiles.open(category_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(existing_data, indent=2, ensure_ascii=False))
            
            logger.info(f"Saved data to category: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False
    
    async def retrieve(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve data from storage.
        
        Args:
            query: Query parameters for filtering data
            
        Returns:
            List of matching data items
        """
        try:
            category = query.get('category')
            if not category:
                return []
            
            category_path = self._get_category_path(category)
            if not os.path.exists(category_path):
                return []
            
            async with aiofiles.open(category_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content:
                    return []
                data = json.loads(content)
            
            # Filter data based on query parameters
            filtered_data = []
            for item in data:
                match = True
                for key, value in query.items():
                    if key != 'category' and (key not in item or item[key] != value):
                        match = False
                        break
                if match:
                    filtered_data.append(item)
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return []
    
    async def update(self, query: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
        """
        Update existing data.
        
        Args:
            query: Query to find data to update
            new_data: New data to apply
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            category = query.get('category')
            if not category:
                return False
            
            category_path = self._get_category_path(category)
            if not os.path.exists(category_path):
                return False
            
            # Load existing data
            async with aiofiles.open(category_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content:
                    return False
                data = json.loads(content)
            
            # Update matching items
            updated = False
            for item in data:
                match = True
                for key, value in query.items():
                    if key != 'category' and (key not in item or item[key] != value):
                        match = False
                        break
                if match:
                    item.update(new_data)
                    updated = True
            
            if updated:
                # Save updated data
                async with aiofiles.open(category_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, indent=2, ensure_ascii=False))
                logger.info(f"Updated data in category: {category}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return False
