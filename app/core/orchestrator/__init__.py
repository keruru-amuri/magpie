"""
Orchestrator module for the MAGPIE platform.

This module provides the core orchestration functionality for routing
user requests to the appropriate specialized agent based on the content
and intent of the request.
"""

from app.core.orchestrator.orchestrator import Orchestrator

__all__ = ["Orchestrator"]
