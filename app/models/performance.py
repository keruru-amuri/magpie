"""
Performance models for the MAGPIE platform.

This module provides data models for tracking and analyzing
the performance of LLM models over time.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAlchemyEnum, 
    Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel as SQLBaseModel


class PerformanceMetricType(str, Enum):
    """
    Enum for performance metric types.
    """
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    QUALITY_SCORE = "quality_score"


class ModelUsageRecord(SQLBaseModel):
    """
    Model for tracking model usage.
    """
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    query_id = Column(String(50), nullable=False)
    conversation_id = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    cost = Column(Float, nullable=False)
    
    # Optional quality feedback
    quality_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)


class PerformanceMetric(SQLBaseModel):
    """
    Model for aggregated performance metrics.
    """
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    metric_type = Column(SQLAlchemyEnum(PerformanceMetricType), nullable=False)
    time_period = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class ModelPerformanceSnapshot(BaseModel):
    """
    Model for a snapshot of model performance metrics.
    """
    model_id: str
    timestamp: datetime
    success_rate: float
    average_latency: float
    total_requests: int
    total_tokens: int
    total_cost: float
    average_quality_score: Optional[float] = None
    
    @classmethod
    def from_usage_records(cls, model_id: str, records: List[ModelUsageRecord]) -> "ModelPerformanceSnapshot":
        """
        Create a performance snapshot from usage records.
        
        Args:
            model_id: Model ID
            records: List of usage records
            
        Returns:
            ModelPerformanceSnapshot: Performance snapshot
        """
        if not records:
            return cls(
                model_id=model_id,
                timestamp=datetime.utcnow(),
                success_rate=0.0,
                average_latency=0.0,
                total_requests=0,
                total_tokens=0,
                total_cost=0.0,
                average_quality_score=None
            )
            
        # Calculate metrics
        total_requests = len(records)
        successful_requests = sum(1 for r in records if r.success)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        # Calculate latency (only for successful requests)
        successful_records = [r for r in records if r.success]
        average_latency = sum(r.latency_ms for r in successful_records) / len(successful_records) if successful_records else 0.0
        
        # Calculate token usage and cost
        total_tokens = sum(r.input_tokens + r.output_tokens for r in records)
        total_cost = sum(r.cost for r in records)
        
        # Calculate quality score if available
        quality_records = [r for r in records if r.quality_score is not None]
        average_quality_score = sum(r.quality_score for r in quality_records) / len(quality_records) if quality_records else None
        
        return cls(
            model_id=model_id,
            timestamp=datetime.utcnow(),
            success_rate=success_rate,
            average_latency=average_latency,
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            average_quality_score=average_quality_score
        )
