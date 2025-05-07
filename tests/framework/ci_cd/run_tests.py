"""
Script for running tests in CI/CD.

This script provides a command-line interface for running tests in CI/CD pipelines.
"""
import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from tests.framework.ci_cd.pipeline import TestType, TestStatus, TestPipeline
from tests.framework.ci_cd.config import CIConfig, create_default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run tests in CI/CD pipeline")
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to CI/CD configuration file"
    )
    
    parser.add_argument(
        "--type",
        type=str,
        choices=[t.value for t in TestType],
        help="Test type to run"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for test results"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        help="Pass rate threshold (0.0-1.0)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        help="Test timeout in seconds"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def run_tests(args):
    """
    Run tests based on command-line arguments.
    
    Args:
        args: Command-line arguments
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load or create configuration
    if args.config:
        config = CIConfig("MAGPIE CI", config_file=args.config)
    else:
        config = create_default_config()
    
    # Override threshold if specified
    if args.threshold is not None:
        config.set_threshold("pass_rate", args.threshold)
    
    # Override timeout if specified
    if args.timeout is not None:
        for suite_config in config.config["test_suites"].values():
            suite_config["timeout"] = args.timeout
    
    # Create pipeline
    pipeline = config.create_pipeline(output_dir=args.output)
    
    # Run tests
    if args.type:
        # Run specific test type
        test_type = TestType(args.type)
        
        logger.info(f"Running {test_type.value} tests")
        
        # Get test suites of specified type
        suites = [
            suite for suite in pipeline.suites
            if suite.type == test_type
        ]
        
        if not suites:
            logger.warning(f"No test suites found for type: {test_type.value}")
            return 1
        
        # Run each suite
        results = {}
        
        for suite in suites:
            suite_results = pipeline.run_suite(suite)
            results[suite.name] = suite_results
    else:
        # Run all tests
        logger.info("Running all tests")
        
        results = pipeline.run_all()
    
    # Save results
    pipeline.save_results()
    
    # Get summary
    summary = pipeline.get_summary()
    
    logger.info(f"Test Summary:")
    logger.info(f"  Total Suites: {summary['total_suites']}")
    logger.info(f"  Total Results: {summary['total_results']}")
    logger.info(f"  Pass Rate: {summary['pass_rate']:.2%}")
    logger.info(f"  Total Duration: {summary['total_duration']:.2f} seconds")
    logger.info(f"  Status Counts:")
    
    for status, count in summary["status_counts"].items():
        logger.info(f"    {status}: {count}")
    
    # Check pass rate threshold
    pass_rate_threshold = config.get_threshold("pass_rate")
    
    if summary["pass_rate"] < pass_rate_threshold:
        logger.error(f"Pass rate {summary['pass_rate']:.2%} is below threshold {pass_rate_threshold:.2%}")
        return 1
    
    return 0


def main():
    """Main entry point."""
    args = parse_args()
    exit_code = run_tests(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
