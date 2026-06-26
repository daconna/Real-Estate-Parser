"""Main crawler spider"""

import logging
import sqlite3
from typing import Type

import requests
from bs4 import BeautifulSoup

from krisha_parser.config.config import Config
from krisha_parser.crawler.flat_parser import FlatParser
from krisha_parser.db.service import init_database

logger = logging.getLogger()


def run_crawler(
    config: Config,
    connector: sqlite3.Connection,
    first_page_url: str,
    parser_class: Type[FlatParser],
):
    """Run the crawler"""
    
    # Initialize database
    init_database(connector)
    
    logger.info(f"Starting crawler for URL: {first_page_url}")
    
    try:
        # Fetch first page
        response = requests.get(
            first_page_url,
            headers=config.parser_config.user_agent,
            timeout=config.parser_config.timeout
        )
        response.raise_for_status()
        
        logger.info(f"Fetched page, status code: {response.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize parser
        flat_parser = parser_class(soup, config)
        
        # Extract apartments
        apartments = flat_parser.parse()
        logger.info(f"Parsed {len(apartments)} apartments")
        
        # Save to database
        for apartment in apartments:
            from krisha_parser.db.service import save_apartment
            save_apartment(connector, apartment)
        
        logger.info(f"Saved {len(apartments)} apartments to database")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching page: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during parsing: {e}")
        raise
