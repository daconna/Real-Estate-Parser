import logging
import re

from krisha_parser.config.config import Config
from krisha_parser.config.parser import ParserConfig
from krisha_parser.config.search import District

logger = logging.getLogger()


class FirstPage:
    """Build first page URL based on search parameters"""

    @staticmethod
    def _get_param_url(arg: bool | None, url: str) -> str | None:
        if arg is None or arg is False:
            return None
        return url if arg else None

    @staticmethod
    def _get_rooms_url(rooms: list | None, parser: ParserConfig) -> str | None:
        """Build rooms filter URL"""
        if rooms is None or not rooms:
            return None
        if len(rooms) == 1:
            return parser.equ.join([parser.rooms_url, str(*rooms)])
        room_data = [
            parser.br_equ.join([parser.rooms_url, str(i)]) for i in rooms
        ]
        return re.sub(r"\b5\b", "5.100", parser.sep.join(room_data))

    @staticmethod
    def _get_price_url(price: int | None, url: str) -> str | None:
        """Build price filter URL"""
        if price is None:
            return None
        return f"{url}{price}"

    @staticmethod
    def _concatenate_params_url(
        parser: ParserConfig, base_url: str, param_urls: tuple
    ) -> str:
        """Concatenate all parameters into complete URL"""
        full_url = base_url
        search_str = parser.sep.join(i for i in param_urls if i is not None)
        if search_str:
            full_url += parser.q_pref + search_str
        return full_url

    @classmethod
    def get_url(cls, config: Config, district: District | str) -> str:
        """Build complete URL for parsing"""
        
        # If district is string, find it in config
        if isinstance(district, str):
            for d in config.search_params.districts:
                if d.name == district or d.url_slug == district:
                    district = d
                    break
        
        if isinstance(district, str):
            raise ValueError(f"District not found: {district}")
        
        search = config.search_params
        parser = config.parser_config
        
        # Build base URL with district
        base_url = parser.prodazha_url + district.url_slug + "/"
        
        # Build parameter URLs
        param_urls = (
            cls._get_param_url(search.has_photo, parser.has_photo_url),
            cls._get_param_url(search.furniture, parser.furniture_url),
            cls._get_rooms_url(search.rooms, parser),
            cls._get_price_url(search.price_from, parser.prices_from_url),
            cls._get_price_url(search.price_to, parser.prices_to_url),
            cls._get_param_url(search.owner, parser.owner_url),
        )
        
        final_url = cls._concatenate_params_url(parser, base_url, param_urls)
        logger.info(f"Generated URL for {district.display_name}: {final_url}")
        return final_url
