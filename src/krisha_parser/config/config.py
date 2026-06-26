from dataclasses import dataclass

from krisha_parser.config.logs import setup_logs
from krisha_parser.config.parser import ParserConfig, get_parser_config
from krisha_parser.config.path import AppPaths, get_app_paths
from krisha_parser.config.search import SearchParameters, get_search_parameters


@dataclass
class Config:
    """Main configuration"""
    
    path: AppPaths
    parser_config: ParserConfig
    search_params: SearchParameters


def load_config() -> Config:
    """Load all configurations"""
    path = get_app_paths()
    setup_logs(path.logs_dir)
    parser_config = get_parser_config()
    search_params = get_search_parameters(path.search_params_file)
    
    return Config(
        path=path,
        parser_config=parser_config,
        search_params=search_params,
    )
