#!/bin/bash
# Cron script for automated parsing

cd /path/to/Real-Estate-Parser
source .venv/bin/activate
python -m krisha_parser

echo "Parser run completed at $(date)" >> logs/cron.log
