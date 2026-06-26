import logging
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger()


@dataclass
class District:
    """District configuration"""
    name: str
    display_name: str
    url_slug: str


@dataclass
class SearchParameters:
    """Search parameters for parser"""
    city: int
    city_name: str
    districts: list
    rooms: list
    price_from: int | None
    price_to: int | None
    has_photo: bool
    furniture: bool | None
    owner: bool | None


def get_search_parameters(config_path: Path) -> SearchParameters:
    """Load search parameters from JSON file"""
    logger.info(f"Loading search parameters from {config_path}")
    
    if not config_path.exists():
        logger.error(f"Search parameters file not found: {config_path}")
        raise FileNotFoundError(f"SEARCH_PARAMETERS.json not found at {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Parse districts
    districts = [
        District(
            name=d['name'],
            display_name=d['display_name'],
            url_slug=d['url_slug']
        )
        for d in config_data.get('districts', [])
    ]
    
    search_params = config_data.get('search_params', {})
    
    params = SearchParameters(
        city=config_data.get('city', 2),
        city_name=config_data.get('city_name', 'astana'),
        districts=districts,
        rooms=search_params.get('rooms', [1, 2, 3]),
        price_from=search_params.get('price_from'),
        price_to=search_params.get('price_to'),
        has_photo=search_params.get('has_photo', True),
        furniture=search_params.get('furniture'),
        owner=search_params.get('owner'),
    )
    
    logger.info(f"Loaded parameters for {len(districts)} districts")
    logger.info(f"Districts: {', '.join([d.display_name for d in districts])}")
    logger.info(f"Search filters: rooms={params.rooms}, price={params.price_from}-{params.price_to}")
    
    return params
