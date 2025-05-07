#!/usr/bin/env python
"""Script to generate mock data for MAGPIE platform."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.mock.config import MockDataConfig, MockDataSource
from app.core.mock.generator import MockDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate mock data for MAGPIE platform")
    
    parser.add_argument(
        "--schemas-only",
        action="store_true",
        help="Generate only JSON schemas without mock data",
    )
    
    parser.add_argument(
        "--documentation",
        action="store_true",
        help="Generate only documentation mock data",
    )
    
    parser.add_argument(
        "--troubleshooting",
        action="store_true",
        help="Generate only troubleshooting mock data",
    )
    
    parser.add_argument(
        "--maintenance",
        action="store_true",
        help="Generate only maintenance mock data",
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all mock data (default)",
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Create mock data generator
    generator = MockDataGenerator()
    
    # Generate schemas
    logger.info("Generating JSON schemas...")
    generator.generate_all_schemas()
    
    # If schemas-only flag is set, exit
    if args.schemas_only:
        logger.info("Schemas generated successfully. Exiting...")
        return
    
    # Determine what to generate
    generate_all = args.all or not (args.documentation or args.troubleshooting or args.maintenance)
    
    if generate_all:
        logger.info("Generating all mock data...")
        generator.generate_all_data()
    else:
        # Generate specific mock data
        if args.documentation:
            logger.info("Generating documentation mock data...")
            generator.generate_documentation_data()
            
        if args.troubleshooting:
            logger.info("Generating troubleshooting mock data...")
            generator.generate_troubleshooting_data()
            
        if args.maintenance:
            logger.info("Generating maintenance mock data...")
            generator.generate_maintenance_data()
    
    logger.info("Mock data generation completed successfully.")


if __name__ == "__main__":
    main()
