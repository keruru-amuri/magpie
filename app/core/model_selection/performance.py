"""
Performance tracking module for the MAGPIE platform.

This module provides functionality for tracking and analyzing
the performance of LLM models over time.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.model_selection.registry import get_model_registry
from app.models.performance import (
    ModelPerformanceSnapshot, ModelUsageRecord, PerformanceMetric, PerformanceMetricType
)

# Configure logging
logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracker for model performance.
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize performance tracker.

        Args:
            db: Database session
        """
        self.db = db
        self.registry = get_model_registry()

    def record_usage(
        self,
        model_id: str,
        query_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        conversation_id: Optional[str] = None,
        quality_score: Optional[float] = None,
        feedback: Optional[str] = None
    ) -> Optional[ModelUsageRecord]:
        """
        Record model usage.

        Args:
            model_id: Model ID
            query_id: Query ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Latency in milliseconds
            success: Whether the request was successful
            error_message: Error message if the request failed
            conversation_id: Optional conversation ID
            quality_score: Optional quality score
            feedback: Optional feedback

        Returns:
            Optional[ModelUsageRecord]: Usage record if saved, None otherwise
        """
        if not self.db:
            logger.warning("Cannot record usage without database session")
            return None
            
        # Get model information
        model = self.registry.get_model(model_id)
        if not model:
            logger.warning(f"Cannot record usage for unknown model: {model_id}")
            return None
            
        # Calculate cost
        cost = model.cost.calculate_cost(input_tokens, output_tokens)
        
        # Create usage record
        usage_record = ModelUsageRecord(
            model_id=model_id,
            query_id=query_id,
            conversation_id=conversation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            cost=cost,
            quality_score=quality_score,
            feedback=feedback
        )
        
        try:
            # Save to database
            self.db.add(usage_record)
            self.db.commit()
            self.db.refresh(usage_record)
            
            # Update model registry with latest performance data
            self._update_model_registry(model_id)
            
            return usage_record
        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            self.db.rollback()
            return None

    def get_model_performance(
        self,
        model_id: str,
        time_period: str = "day",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[ModelPerformanceSnapshot]:
        """
        Get model performance for a time period.

        Args:
            model_id: Model ID
            time_period: Time period (hour, day, week, month)
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            Optional[ModelPerformanceSnapshot]: Performance snapshot
        """
        if not self.db:
            logger.warning("Cannot get performance without database session")
            return None
            
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
            
        if not start_time:
            if time_period == "hour":
                start_time = end_time - timedelta(hours=1)
            elif time_period == "day":
                start_time = end_time - timedelta(days=1)
            elif time_period == "week":
                start_time = end_time - timedelta(weeks=1)
            elif time_period == "month":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)
                
        try:
            # Query usage records
            records = self.db.query(ModelUsageRecord).filter(
                ModelUsageRecord.model_id == model_id,
                ModelUsageRecord.timestamp >= start_time,
                ModelUsageRecord.timestamp <= end_time
            ).all()
            
            # Create performance snapshot
            return ModelPerformanceSnapshot.from_usage_records(model_id, records)
        except Exception as e:
            logger.error(f"Failed to get model performance: {str(e)}")
            return None

    def get_comparative_performance(
        self,
        time_period: str = "day",
        metric_type: PerformanceMetricType = PerformanceMetricType.SUCCESS_RATE
    ) -> Dict[str, float]:
        """
        Get comparative performance for all models.

        Args:
            time_period: Time period (hour, day, week, month)
            metric_type: Metric type

        Returns:
            Dict[str, float]: Model IDs mapped to metric values
        """
        if not self.db:
            logger.warning("Cannot get comparative performance without database session")
            return {}
            
        try:
            # Get latest metrics for each model
            subquery = self.db.query(
                PerformanceMetric.model_id,
                PerformanceMetric.metric_type,
                PerformanceMetric.time_period,
                PerformanceMetric.value
            ).filter(
                PerformanceMetric.metric_type == metric_type,
                PerformanceMetric.time_period == time_period
            ).order_by(
                PerformanceMetric.end_time.desc()
            ).subquery()
            
            results = {}
            for model in self.registry.get_all_models():
                metric = self.db.query(subquery).filter(
                    subquery.c.model_id == model.id
                ).first()
                
                if metric:
                    results[model.id] = metric.value
                else:
                    results[model.id] = 0.0
                    
            return results
        except Exception as e:
            logger.error(f"Failed to get comparative performance: {str(e)}")
            return {}

    def _update_model_registry(self, model_id: str) -> None:
        """
        Update model registry with latest performance data.

        Args:
            model_id: Model ID
        """
        try:
            # Get performance snapshot for the last day
            snapshot = self.get_model_performance(model_id, "day")
            if not snapshot:
                return
                
            # Update model in registry
            self.registry.update_model_performance(
                model_id=model_id,
                performance_score=snapshot.average_quality_score or 0.0,
                success_rate=snapshot.success_rate,
                average_latency=snapshot.average_latency / 1000.0  # Convert to seconds
            )
        except Exception as e:
            logger.error(f"Failed to update model registry: {str(e)}")

    def aggregate_metrics(self, force_update: bool = False) -> None:
        """
        Aggregate performance metrics.

        Args:
            force_update: Whether to force update even if recent aggregation exists
        """
        if not self.db:
            logger.warning("Cannot aggregate metrics without database session")
            return
            
        try:
            # Get all models
            models = self.registry.get_all_models(active_only=False)
            
            # Current time
            now = datetime.utcnow()
            
            # Time periods to aggregate
            periods = [
                ("hourly", timedelta(hours=1)),
                ("daily", timedelta(days=1)),
                ("weekly", timedelta(weeks=1)),
                ("monthly", timedelta(days=30))
            ]
            
            for model in models:
                for period_name, period_delta in periods:
                    # Check if recent aggregation exists
                    if not force_update:
                        recent_metric = self.db.query(PerformanceMetric).filter(
                            PerformanceMetric.model_id == model.id,
                            PerformanceMetric.time_period == period_name,
                            PerformanceMetric.end_time >= now - timedelta(hours=1)
                        ).first()
                        
                        if recent_metric:
                            logger.debug(f"Skipping recent {period_name} aggregation for {model.id}")
                            continue
                    
                    # Time range for aggregation
                    start_time = now - period_delta
                    
                    # Get usage records
                    records = self.db.query(ModelUsageRecord).filter(
                        ModelUsageRecord.model_id == model.id,
                        ModelUsageRecord.timestamp >= start_time,
                        ModelUsageRecord.timestamp <= now
                    ).all()
                    
                    if not records:
                        logger.debug(f"No usage records for {model.id} in {period_name} period")
                        continue
                        
                    # Create performance snapshot
                    snapshot = ModelPerformanceSnapshot.from_usage_records(model.id, records)
                    
                    # Create metrics
                    metrics = [
                        PerformanceMetric(
                            model_id=model.id,
                            metric_type=PerformanceMetricType.SUCCESS_RATE,
                            time_period=period_name,
                            start_time=start_time,
                            end_time=now,
                            value=snapshot.success_rate,
                            sample_size=snapshot.total_requests
                        ),
                        PerformanceMetric(
                            model_id=model.id,
                            metric_type=PerformanceMetricType.LATENCY,
                            time_period=period_name,
                            start_time=start_time,
                            end_time=now,
                            value=snapshot.average_latency,
                            sample_size=snapshot.total_requests
                        ),
                        PerformanceMetric(
                            model_id=model.id,
                            metric_type=PerformanceMetricType.TOKEN_USAGE,
                            time_period=period_name,
                            start_time=start_time,
                            end_time=now,
                            value=snapshot.total_tokens,
                            sample_size=snapshot.total_requests
                        ),
                        PerformanceMetric(
                            model_id=model.id,
                            metric_type=PerformanceMetricType.COST,
                            time_period=period_name,
                            start_time=start_time,
                            end_time=now,
                            value=snapshot.total_cost,
                            sample_size=snapshot.total_requests
                        )
                    ]
                    
                    # Add quality score if available
                    if snapshot.average_quality_score is not None:
                        metrics.append(
                            PerformanceMetric(
                                model_id=model.id,
                                metric_type=PerformanceMetricType.QUALITY_SCORE,
                                time_period=period_name,
                                start_time=start_time,
                                end_time=now,
                                value=snapshot.average_quality_score,
                                sample_size=snapshot.total_requests
                            )
                        )
                    
                    # Save metrics
                    self.db.add_all(metrics)
                    
            # Commit changes
            self.db.commit()
            logger.info("Performance metrics aggregated successfully")
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {str(e)}")
            self.db.rollback()
