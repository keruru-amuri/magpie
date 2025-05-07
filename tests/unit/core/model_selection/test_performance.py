"""
Unit tests for performance tracking module.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.core.model_selection.performance import PerformanceTracker
from app.models.performance import (
    ModelPerformanceSnapshot, ModelUsageRecord, PerformanceMetric, PerformanceMetricType
)


class TestPerformanceTracker:
    """
    Tests for PerformanceTracker.
    """

    def setup_method(self):
        """
        Set up test fixtures.
        """
        # Create mock database session
        self.mock_db = MagicMock()

        # Create mock registry
        self.mock_registry = MagicMock()
        self.mock_registry.get_model.return_value = MagicMock(
            cost=MagicMock(
                calculate_cost=MagicMock(return_value=0.05)
            )
        )

        # Create tracker with mock dependencies
        with patch("app.core.model_selection.performance.get_model_registry", return_value=self.mock_registry):
            self.tracker = PerformanceTracker(self.mock_db)

    def test_record_usage(self):
        """
        Test recording model usage.
        """
        # Record usage
        usage_record = self.tracker.record_usage(
            model_id="test-model",
            query_id="test-query",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500,
            success=True,
            conversation_id="test-conversation"
        )

        # Verify registry was queried
        self.mock_registry.get_model.assert_called_with("test-model")

        # Verify cost was calculated
        self.mock_registry.get_model().cost.calculate_cost.assert_called_with(100, 50)

        # Verify record was created and saved
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

        # Verify record properties
        assert usage_record.model_id == "test-model"
        assert usage_record.query_id == "test-query"
        assert usage_record.input_tokens == 100
        assert usage_record.output_tokens == 50
        assert usage_record.latency_ms == 500
        assert usage_record.success is True
        assert usage_record.conversation_id == "test-conversation"
        assert usage_record.cost == 0.05

    def test_record_usage_error(self):
        """
        Test error handling when recording usage.
        """
        # Set up mock db to raise exception
        self.mock_db.commit.side_effect = Exception("Test error")

        # Record usage (should not raise exception)
        usage_record = self.tracker.record_usage(
            model_id="test-model",
            query_id="test-query",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500
        )

        # Verify rollback was called
        self.mock_db.rollback.assert_called_once()

        # Verify no record was returned
        assert usage_record is None

    def test_record_usage_unknown_model(self):
        """
        Test recording usage for unknown model.
        """
        # Set up mock registry to return None
        self.mock_registry.get_model.return_value = None

        # Record usage
        usage_record = self.tracker.record_usage(
            model_id="unknown-model",
            query_id="test-query",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500
        )

        # Verify no record was created
        self.mock_db.add.assert_not_called()

        # Verify no record was returned
        assert usage_record is None

    def test_record_usage_no_db(self):
        """
        Test recording usage without database session.
        """
        # Create tracker without database session
        with patch("app.core.model_selection.performance.get_model_registry", return_value=self.mock_registry):
            tracker = PerformanceTracker(db=None)

        # Record usage
        usage_record = tracker.record_usage(
            model_id="test-model",
            query_id="test-query",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500
        )

        # Verify no record was returned
        assert usage_record is None

    def test_get_model_performance(self):
        """
        Test getting model performance.
        """
        # Create mock usage records
        mock_records = [
            MagicMock(
                model_id="test-model",
                timestamp=datetime.utcnow(),
                input_tokens=100,
                output_tokens=50,
                latency_ms=500,
                success=True,
                cost=0.05,
                quality_score=8.0
            ),
            MagicMock(
                model_id="test-model",
                timestamp=datetime.utcnow(),
                input_tokens=200,
                output_tokens=100,
                latency_ms=600,
                success=True,
                cost=0.1,
                quality_score=7.0
            )
        ]

        # Set up mock db to return records
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_records

        # Get model performance
        performance = self.tracker.get_model_performance(
            model_id="test-model",
            time_period="day"
        )

        # Verify db was queried
        self.mock_db.query.assert_called_once()

        # Verify performance snapshot
        assert performance.model_id == "test-model"
        assert performance.total_requests == 2
        assert performance.success_rate == 1.0
        assert performance.average_latency == 550.0
        assert performance.total_tokens == 450
        assert round(performance.total_cost, 2) == 0.15
        assert performance.average_quality_score == 7.5

    def test_get_model_performance_no_records(self):
        """
        Test getting model performance with no records.
        """
        # Set up mock db to return no records
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        # Get model performance
        performance = self.tracker.get_model_performance(
            model_id="test-model",
            time_period="day"
        )

        # Verify performance snapshot
        assert performance.model_id == "test-model"
        assert performance.total_requests == 0
        assert performance.success_rate == 0.0
        assert performance.average_latency == 0.0
        assert performance.total_tokens == 0
        assert performance.total_cost == 0.0
        assert performance.average_quality_score is None

    def test_get_model_performance_no_db(self):
        """
        Test getting model performance without database session.
        """
        # Create tracker without database session
        tracker = PerformanceTracker(db=None)

        # Get model performance
        performance = tracker.get_model_performance(
            model_id="test-model",
            time_period="day"
        )

        # Verify no performance was returned
        assert performance is None

    def test_get_comparative_performance(self):
        """
        Test getting comparative performance.
        """
        # Create mock metrics
        mock_subquery = MagicMock()
        mock_subquery.c.model_id = "model_id"
        mock_subquery.c.value = "value"

        # Set up mock db
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.subquery.return_value = mock_subquery
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(value=0.9),  # First model
            MagicMock(value=0.8),  # Second model
            None  # Third model (no metrics)
        ]

        # Set up mock registry
        self.mock_registry.get_all_models.return_value = [
            MagicMock(id="model1"),
            MagicMock(id="model2"),
            MagicMock(id="model3")
        ]

        # Get comparative performance
        performance = self.tracker.get_comparative_performance(
            time_period="day",
            metric_type=PerformanceMetricType.SUCCESS_RATE
        )

        # Verify db was queried
        self.mock_db.query.assert_called()

        # Verify performance metrics
        assert performance["model1"] == 0.9
        assert performance["model2"] == 0.8
        assert performance["model3"] == 0.0  # Default for model with no metrics

    def test_get_comparative_performance_no_db(self):
        """
        Test getting comparative performance without database session.
        """
        # Create tracker without database session
        tracker = PerformanceTracker(db=None)

        # Get comparative performance
        performance = tracker.get_comparative_performance()

        # Verify empty dict was returned
        assert performance == {}
