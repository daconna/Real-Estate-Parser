import logging
import sys

from krisha_parser.config.config import load_config
from krisha_parser.crawler.first_page import FirstPage
from krisha_parser.crawler.flat_parser import FlatParser
from krisha_parser.crawler.spider import run_crawler
from krisha_parser.db.service import get_connection

logger = logging.getLogger()


def main():
    """Main entry point"""
    config = load_config()
    connector = get_connection(config.path.db_file)
    
    logger.info("="*60)
    logger.info("Starting Real Estate KZ Parser")
    logger.info(f"City: {config.search_params.city_name}")
    logger.info(f"Districts: {', '.join([d.display_name for d in config.search_params.districts])}")
    logger.info("="*60)
    
    # Parse apartments for each district
    total_parsed = 0
    for district in config.search_params.districts:
        logger.info(f"\nParsing district: {district.display_name}")
        try:
            first_page_url = FirstPage.get_url(config, district)
            run_crawler(config, connector, first_page_url, FlatParser)
            logger.info(f"Successfully parsed {district.display_name}")
        except Exception as e:
            logger.error(f"Error parsing {district.display_name}: {e}")
            continue
    
    logger.info("\n" + "="*60)
    logger.info("Parsing completed successfully")
    logger.info("="*60)
    
    connector.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.critical(msg=error, exc_info=True)
        sys.exit(1)
