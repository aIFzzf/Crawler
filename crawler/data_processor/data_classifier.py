"""
Data classifier module for content categorization.
"""
from typing import Dict, List, Tuple, Any
from ..interfaces import IDataClassifier

class DataClassifier(IDataClassifier):
    """
    Implements content classification functionality.
    Uses a keyword-based approach for text classification.
    """
    
    def __init__(self):
        """Initialize the classifier with empty categories."""
        self.categories: Dict[str, List[str]] = {}
        self.training_data: List[Tuple[str, str]] = []
    
    def classify(self, content: str) -> str:
        """
        Classify content based on keyword matching.
        
        Args:
            content: Content to classify
            
        Returns:
            Category label
        """
        if not self.categories:
            raise ValueError("No categories defined. Please add categories before classification.")
        
        max_matches = 0
        best_category = next(iter(self.categories))  # Default to first category
        
        for category, keywords in self.categories.items():
            matches = sum(1 for keyword in keywords if keyword in content)
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        return best_category
    
    def get_categories(self) -> List[str]:
        """
        Get list of available categories.
        
        Returns:
            List of category labels
        """
        return list(self.categories.keys())
    
    def train(self, training_data: List[Tuple[str, str]]) -> None:
        """
        Train classifier with labeled data.
        Updates keyword lists based on training data.
        
        Args:
            training_data: List of (content, label) pairs
        """
        self.training_data.extend(training_data)
        
        # Update keyword lists based on frequency analysis
        for content, label in training_data:
            if label in self.categories:
                words = content.split()
                for word in words:
                    if len(word) > 1 and word not in self.categories[label]:
                        self.categories[label].append(word)
    
    def add_category(self, category: str, keywords: List[str] = None) -> None:
        """
        Add a new category with optional keywords.
        
        Args:
            category: New category name
            keywords: Initial keywords for the category
        """
        if category not in self.categories:
            self.categories[category] = keywords or []
    
    def remove_category(self, category: str) -> bool:
        """
        Remove a category.
        
        Args:
            category: Category to remove
            
        Returns:
            True if category was removed, False if it didn't exist
        """
        if category in self.categories:
            del self.categories[category]
            return True
        return False
    
    def update_keywords(self, category: str, keywords: List[str], mode: str = 'add') -> bool:
        """
        Update keywords for a category.
        
        Args:
            category: Target category
            keywords: Keywords to add or remove
            mode: Operation mode, either 'add' or 'remove'
            
        Returns:
            True if update was successful, False otherwise
        """
        if category not in self.categories:
            return False
            
        if mode == 'add':
            self.categories[category].extend([k for k in keywords if k not in self.categories[category]])
        elif mode == 'remove':
            self.categories[category] = [k for k in self.categories[category] if k not in keywords]
        else:
            raise ValueError("Mode must be either 'add' or 'remove'")
            
        return True
