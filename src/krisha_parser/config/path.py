import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger()


@dataclass(frozen=True)
class AppPaths:
    """Application paths"""
    project_root: Path
    search_params_file: Path
    db_file: Path
    logs_dir: Path


def get_app_paths() -> AppPaths:
    """Get application paths"""
    project_root = Path(__file__).parent.parent.parent.parent
    
    paths = AppPaths(
        project_root=project_root,
        search_params_file=project_root / "SEARCH_PARAMETERS.json",
        db_file=project_root / "krisha_data.db",
        logs_dir=project_root / "logs",
    )
    
    # Create logs directory if it doesn't exist
    paths.logs_dir.mkdir(exist_ok=True)
    
    logger.info(f"Project root: {paths.project_root}")
    logger.info(f"Database file: {paths.db_file}")
    
    return paths
