"""Pagination handler for krisha.kz"""

import logging
from typing import Generator, Optional

import requests
from bs4 import BeautifulSoup

from krisha_parser.config.config import Config
from krisha_parser.crawler.flat_parser import FlatParser
from krisha_parser.db.models import Apartment

logger = logging.getLogger()


class PaginationHandler:
    """Handle pagination through search results"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.parser_config.user_agent)
    
    def get_pages(
        self, 
        base_url: str, 
        max_pages: Optional[int] = None
    ) -> Generator[list[Apartment], None, None]:
        """
        Iterate through pages and yield apartments
        
        Args:
            base_url: Base URL for search
            max_pages: Maximum pages to parse (None = all)
        
        Yields:
            List of Apartment objects for each page
        """
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max pages limit: {max_pages}")
                break
            
            # Build URL with page parameter
            page_url = self._build_page_url(base_url, page)
            logger.info(f"Fetching page {page}: {page_url}")
            
            try:
                # Fetch page
                response = self.session.get(
                    page_url,
                    timeout=self.config.parser_config.timeout
                )
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse apartments
                parser = FlatParser(soup, self.config)
                apartments = parser.parse()
                
                if not apartments:
                    logger.info(f"No apartments found on page {page}, stopping")
                    break
                
                logger.info(f"Page {page}: Found {len(apartments)} apartments")
                yield apartments
                
                page += 1
                
                # Delay between requests to respect server
                import time
                time.sleep(self.config.parser_config.sleep_time)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Error parsing page {page}: {e}")
                break
    
    def get_total_apartments(self, base_url: str) -> int:
        """Get total number of apartments from search"""
        try:
            response = self.session.get(
                base_url,
                timeout=self.config.parser_config.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for total count
            # Pattern: "Найдено 9 585 объявлений"
            text = soup.get_text()
            import re
            match = re.search(r'Найдено\s+(\d+(?:\s+\d+)?)\s+объявлений', text)
            if match:
                count_str = match.group(1).replace('\u00a0', '').replace(' ', '')
                return int(count_str)
            
            return 0
        except Exception as e:
            logger.error(f"Error getting total apartments: {e}")
            return 0
    
    @staticmethod
    def _build_page_url(base_url: str, page: int) -> str:
        """Build URL with page parameter"""
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page}"
