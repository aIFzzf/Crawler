"""
Content analyzer for automatically identifying important content patterns on websites.
Uses various heuristics and machine learning techniques to identify valuable content.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from collections import Counter
import re
from loguru import logger

@dataclass
class ContentPattern:
    """Data class for storing content pattern information."""
    selector: str  # CSS selector or XPath
    content_type: str  # article, list, pagination, etc.
    importance_score: float  # 0-1 score indicating importance
    features: Dict[str, Any]  # Additional pattern features

class ContentAnalyzer:
    """
    Analyzes webpage content to identify important patterns and content areas.
    Uses various heuristics to determine what content is most valuable for crawling.
    """
    
    # Common content indicators
    ARTICLE_KEYWORDS = {'article', 'post', 'content', 'main', 'body', 'text'}
    LIST_KEYWORDS = {'list', 'feed', 'items', 'cards', 'grid'}
    NAVIGATION_KEYWORDS = {'nav', 'menu', 'pagination', 'pages'}
    
    # Content type definitions
    CONTENT_TYPES = {
        'article': {'article', 'post', 'content', 'main-content', 'detail'},
        'list': {'list', 'feed', 'timeline', 'cards', 'items'},
        'pagination': {'pagination', 'pages', 'next', 'prev'},
        'comments': {'comments', 'responses', 'replies'},
        'sidebar': {'sidebar', 'related', 'recommended'}
    }

    def __init__(self):
        """Initialize the content analyzer."""
        self.patterns: List[ContentPattern] = []
        self.important_selectors: Set[str] = set()

    def analyze_page(self, html: str) -> List[ContentPattern]:
        """
        Analyze a webpage and identify important content patterns.
        
        Args:
            html: Raw HTML content of the page
            
        Returns:
            List of identified content patterns
        """
        soup = BeautifulSoup(html, 'html.parser')
        self.patterns = []
        
        # Analyze page structure
        self._analyze_structure(soup)
        # Identify content areas
        self._identify_content_areas(soup)
        # Analyze text density
        self._analyze_text_density(soup)
        # Find repeated patterns
        self._find_repeated_patterns(soup)
        # Score patterns
        self._score_patterns()
        
        return sorted(self.patterns, key=lambda x: x.importance_score, reverse=True)

    def _analyze_structure(self, soup: BeautifulSoup) -> None:
        """Analyze the overall structure of the page."""
        # Look for semantic HTML5 elements
        semantic_elements = {
            'article': 0.9,
            'main': 0.8,
            'section': 0.7,
            'nav': 0.6,
            'aside': 0.4
        }
        
        for element, base_score in semantic_elements.items():
            for tag in soup.find_all(element):
                self.patterns.append(ContentPattern(
                    selector=self._get_unique_selector(tag),
                    content_type=element,
                    importance_score=base_score,
                    features={'semantic': True}
                ))

    def _identify_content_areas(self, soup: BeautifulSoup) -> None:
        """Identify main content areas using various heuristics."""
        # Check common content IDs and classes
        for element in soup.find_all(class_=True):
            classes = set(element.get('class', []))
            for content_type, keywords in self.CONTENT_TYPES.items():
                if keywords & classes:
                    self.patterns.append(ContentPattern(
                        selector=self._get_unique_selector(element),
                        content_type=content_type,
                        importance_score=0.7,
                        features={'matched_keywords': keywords & classes}
                    ))

    def _analyze_text_density(self, soup: BeautifulSoup) -> None:
        """Analyze text density to identify content-rich areas."""
        for element in soup.find_all(['div', 'article', 'section']):
            text_length = len(element.get_text(strip=True))
            tags_count = len(element.find_all())
            if tags_count > 0:
                density = text_length / tags_count
                if density > 50:  # High text density threshold
                    self.patterns.append(ContentPattern(
                        selector=self._get_unique_selector(element),
                        content_type='content',
                        importance_score=min(0.9, density / 1000),
                        features={'text_density': density}
                    ))

    def _find_repeated_patterns(self, soup: BeautifulSoup) -> None:
        """Identify repeated patterns that might indicate lists or feeds."""
        # Look for similar structures that repeat
        pattern_counts = Counter()
        
        for element in soup.find_all(['div', 'li', 'article']):
            pattern = self._get_element_pattern(element)
            if pattern:
                pattern_counts[pattern] += 1
        
        for pattern, count in pattern_counts.items():
            if count > 2:  # Minimum repetition threshold
                self.patterns.append(ContentPattern(
                    selector=pattern,
                    content_type='list',
                    importance_score=min(0.8, count / 20),  # Score based on repetition
                    features={'repetition_count': count}
                ))

    def _score_patterns(self) -> None:
        """Score and filter patterns based on various factors."""
        for pattern in self.patterns:
            # Adjust scores based on additional factors
            if 'semantic' in pattern.features:
                pattern.importance_score *= 1.2
            
            if 'text_density' in pattern.features:
                pattern.importance_score *= 1.1
            
            if 'repetition_count' in pattern.features:
                pattern.importance_score *= 1.1
            
            # Cap score at 1.0
            pattern.importance_score = min(1.0, pattern.importance_score)

    def _get_unique_selector(self, tag: Tag) -> str:
        """Generate a unique CSS selector for a tag."""
        if tag.get('id'):
            return f"#{tag['id']}"
        
        if tag.get('class'):
            classes = '.'.join(tag['class'])
            return f"{tag.name}.{classes}"
        
        # Generate path if no id/class
        path = []
        parent = tag
        while parent and parent.name != '[document]':
            if parent.get('id'):
                path.append(f"#{parent['id']}")
                break
            siblings = parent.find_previous_siblings(parent.name)
            path.append(f"{parent.name}:nth-of-type({len(siblings) + 1})")
            parent = parent.parent
        
        return ' > '.join(reversed(path))

    def _get_element_pattern(self, element: Tag) -> Optional[str]:
        """Get a simplified pattern representation of an element's structure."""
        if not element.name:
            return None
        
        pattern = [element.name]
        for child in element.children:
            if isinstance(child, Tag):
                pattern.append(child.name)
        
        return ','.join(pattern) if pattern else None

    def get_crawl_suggestions(self, patterns: List[ContentPattern]) -> Dict[str, List[str]]:
        """
        Generate crawling suggestions based on identified patterns.
        
        Args:
            patterns: List of identified content patterns
            
        Returns:
            Dictionary with crawling suggestions by content type
        """
        suggestions = {
            'content_selectors': [],
            'list_selectors': [],
            'pagination_selectors': [],
            'ignore_selectors': []
        }
        
        for pattern in patterns:
            if pattern.importance_score < 0.3:
                suggestions['ignore_selectors'].append(pattern.selector)
                continue
                
            if pattern.content_type in ['article', 'content']:
                suggestions['content_selectors'].append(pattern.selector)
            elif pattern.content_type in ['list', 'feed']:
                suggestions['list_selectors'].append(pattern.selector)
            elif pattern.content_type == 'pagination':
                suggestions['pagination_selectors'].append(pattern.selector)
        
        return suggestions
