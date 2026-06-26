import logging
from dataclasses import dataclass

logger = logging.getLogger()


def default_user_agent():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }


@dataclass(frozen=True)
class ParserConfig:
    """Parser configuration for apartment sales"""
    
    user_agent: dict = None
    ads_on_page: int = 20
    sleep_time: int = 2
    timeout: int = 20
    max_skip_ad: int = 5
    retry_delay: tuple = (15, 60, 300, 1200, 3600)
    
    # Base URLs for SALE (prodazha) not RENT
    home_url: str = "https://krisha.kz"
    prodazha_url: str = "https://krisha.kz/prodazha/kvartiry/"
    
    # URL parameters
    sep: str = "&das"
    q_pref: str = "?das"
    equ: str = "="
    br_equ: str = "[]="
    
    # Filter URLs
    has_photo_url: str = "[_sys.hasphoto]=1"
    furniture_url: str = "[live.furniture]=1"
    rooms_url: str = "[live.rooms]"
    prices_from_url: str = "[price][from]="
    prices_to_url: str = "[price][to]="
    owner_url: str = "[who]=1"
    
    def __post_init__(self):
        if self.user_agent is None:
            object.__setattr__(self, 'user_agent', default_user_agent())


def get_parser_config() -> ParserConfig:
    logger.info("Loading parser configuration for apartment SALES")
    return ParserConfig()
