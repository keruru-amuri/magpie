"""
Model selection module for the MAGPIE platform.

This module provides functionality for selecting the appropriate LLM model
based on task complexity, cost considerations, and performance requirements.
"""

from app.core.model_selection.selector import ModelSelector

__all__ = ["ModelSelector"]
