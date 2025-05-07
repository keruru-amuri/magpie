"""
Unit tests for model registry module.
"""
import pytest
from unittest.mock import patch

from app.core.model_selection.registry import ModelRegistry, get_model_registry
from app.models.agent import ModelSize
from app.models.model_registry import ModelCapability, ModelCost, ModelInfo


class TestModelRegistry:
    """
    Tests for ModelRegistry.
    """

    def test_initialize_default_models(self):
        """
        Test initialization of default models.
        """
        # Create registry
        registry = ModelRegistry()
        
        # Verify default models were initialized
        models = registry.get_all_models()
        assert len(models) >= 3
        
        # Verify models by size
        small_models = registry.get_models_by_size(ModelSize.SMALL)
        medium_models = registry.get_models_by_size(ModelSize.MEDIUM)
        large_models = registry.get_models_by_size(ModelSize.LARGE)
        
        assert len(small_models) >= 1
        assert len(medium_models) >= 1
        assert len(large_models) >= 1
        
        # Verify model capabilities
        for model in models:
            assert len(model.capabilities) > 0
            assert model.cost is not None

    def test_register_model(self):
        """
        Test registering a new model.
        """
        # Create registry
        registry = ModelRegistry()
        
        # Register a new model
        model_info = registry.register_model(
            id="test-model",
            name="Test Model",
            size=ModelSize.MEDIUM,
            description="Test model for unit tests",
            max_tokens=8000,
            capabilities={
                ModelCapability.BASIC_COMPLETION,
                ModelCapability.CHAT_COMPLETION
            },
            cost=ModelCost(
                input_cost_per_1k_tokens=0.001,
                output_cost_per_1k_tokens=0.002
            )
        )
        
        # Verify model was registered
        assert model_info.id == "test-model"
        assert model_info.name == "Test Model"
        assert model_info.size == ModelSize.MEDIUM
        assert model_info.max_tokens == 8000
        assert len(model_info.capabilities) == 2
        assert model_info.is_active is True
        
        # Verify model can be retrieved
        retrieved_model = registry.get_model("test-model")
        assert retrieved_model is not None
        assert retrieved_model.id == "test-model"

    def test_get_models_by_capability(self):
        """
        Test getting models by capability.
        """
        # Create registry
        registry = ModelRegistry()
        
        # Get models by capability
        basic_models = registry.get_models_by_capability(ModelCapability.BASIC_COMPLETION)
        reasoning_models = registry.get_models_by_capability(ModelCapability.REASONING)
        
        # All models should support basic completion
        assert len(basic_models) >= 3
        
        # Not all models may support reasoning
        assert all(ModelCapability.BASIC_COMPLETION in model.capabilities for model in basic_models)
        assert all(ModelCapability.REASONING in model.capabilities for model in reasoning_models)

    def test_update_model_performance(self):
        """
        Test updating model performance metrics.
        """
        # Create registry
        registry = ModelRegistry()
        
        # Get a model
        models = registry.get_all_models()
        model = models[0]
        
        # Initial performance metrics
        initial_performance = model.performance_score
        initial_success_rate = model.success_rate
        initial_latency = model.average_latency
        
        # Update performance metrics
        success = registry.update_model_performance(
            model_id=model.id,
            performance_score=8.5,
            success_rate=0.95,
            average_latency=0.5
        )
        
        # Verify update was successful
        assert success is True
        
        # Verify metrics were updated
        updated_model = registry.get_model(model.id)
        assert updated_model.performance_score == 8.5
        assert updated_model.success_rate == 0.95
        assert updated_model.average_latency == 0.5
        
        # Test updating non-existent model
        success = registry.update_model_performance(
            model_id="non-existent-model",
            performance_score=8.5
        )
        assert success is False

    def test_deactivate_activate_model(self):
        """
        Test deactivating and activating a model.
        """
        # Create registry
        registry = ModelRegistry()
        
        # Get a model
        models = registry.get_all_models()
        model = models[0]
        
        # Deactivate model
        success = registry.deactivate_model(model.id)
        assert success is True
        
        # Verify model is inactive
        inactive_model = registry.get_model(model.id)
        assert inactive_model.is_active is False
        
        # Verify model is not returned when getting active models
        active_models = registry.get_all_models(active_only=True)
        assert all(m.id != model.id for m in active_models)
        
        # Activate model
        success = registry.activate_model(model.id)
        assert success is True
        
        # Verify model is active
        active_model = registry.get_model(model.id)
        assert active_model.is_active is True
        
        # Test deactivating non-existent model
        success = registry.deactivate_model("non-existent-model")
        assert success is False

    def test_get_model_registry_singleton(self):
        """
        Test get_model_registry singleton function.
        """
        # Get registry instances
        registry1 = get_model_registry()
        registry2 = get_model_registry()
        
        # Verify they are the same instance
        assert registry1 is registry2
        
        # Verify registry is initialized
        assert len(registry1.get_all_models()) >= 3

    @patch("app.core.model_selection.registry.settings")
    def test_get_model_by_deployment_name(self, mock_settings):
        """
        Test get_model_by_deployment_name method.
        """
        # Set up mock settings
        mock_settings.GPT_4_1_DEPLOYMENT_NAME = "gpt-4-1"
        mock_settings.GPT_4_1_MINI_DEPLOYMENT_NAME = "gpt-4-1-mini"
        mock_settings.GPT_4_1_NANO_DEPLOYMENT_NAME = "gpt-4-1-nano"
        
        # Create registry
        registry = ModelRegistry()
        
        # Test getting models by deployment name
        large_model = registry.get_model_by_deployment_name("gpt-4-1")
        medium_model = registry.get_model_by_deployment_name("gpt-4-1-mini")
        small_model = registry.get_model_by_deployment_name("gpt-4-1-nano")
        
        # Verify models were found
        assert large_model is not None
        assert medium_model is not None
        assert small_model is not None
        
        # Verify model sizes
        assert large_model.size == ModelSize.LARGE
        assert medium_model.size == ModelSize.MEDIUM
        assert small_model.size == ModelSize.SMALL
        
        # Test getting model by unknown deployment name
        unknown_model = registry.get_model_by_deployment_name("unknown-deployment")
        assert unknown_model is None
