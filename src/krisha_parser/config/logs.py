import logging
from pathlib import Path

logger = logging.getLogger()


def setup_logs(logs_dir: Path):
    """Setup logging configuration"""
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "parser.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")
