"""
Integration test harness for tracking component interactions.

This module provides utilities for tracking interactions between components
during integration testing.
"""
import time
import logging
import asyncio
import inspect
import functools
from typing import Dict, List, Any, Optional, Union, Callable, Type, Set
from enum import Enum
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Enum for interaction types."""
    METHOD_CALL = "method_call"
    EVENT = "event"
    EXCEPTION = "exception"
    RESPONSE = "response"


class ComponentInteraction:
    """
    Model for component interactions.
    """
    
    def __init__(
        self,
        source: str,
        target: str,
        interaction_type: InteractionType,
        method_name: Optional[str] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        exception: Optional[Exception] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a component interaction.
        
        Args:
            source: Source component
            target: Target component
            interaction_type: Interaction type
            method_name: Optional method name
            args: Optional method arguments
            kwargs: Optional method keyword arguments
            result: Optional method result
            exception: Optional exception
            timestamp: Optional timestamp
        """
        self.source = source
        self.target = target
        self.interaction_type = interaction_type
        self.method_name = method_name
        self.args = args or []
        self.kwargs = kwargs or {}
        self.result = result
        self.exception = exception
        self.timestamp = timestamp or datetime.now()
        self.duration = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "source": self.source,
            "target": self.target,
            "interaction_type": self.interaction_type.value,
            "method_name": self.method_name,
            "args": [str(arg) for arg in self.args],
            "kwargs": {k: str(v) for k, v in self.kwargs.items()},
            "result": str(self.result) if self.result is not None else None,
            "exception": str(self.exception) if self.exception is not None else None,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration
        }


class InteractionTracker:
    """
    Tracker for component interactions.
    """
    
    def __init__(self):
        """Initialize the interaction tracker."""
        self.interactions = []
        self.start_time = datetime.now()
    
    def record_interaction(self, interaction: ComponentInteraction):
        """
        Record a component interaction.
        
        Args:
            interaction: Component interaction
        """
        self.interactions.append(interaction)
    
    def get_interactions(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        interaction_type: Optional[InteractionType] = None,
        method_name: Optional[str] = None
    ) -> List[ComponentInteraction]:
        """
        Get interactions matching the specified criteria.
        
        Args:
            source: Optional source component
            target: Optional target component
            interaction_type: Optional interaction type
            method_name: Optional method name
            
        Returns:
            List of matching interactions
        """
        result = []
        
        for interaction in self.interactions:
            if source and interaction.source != source:
                continue
            
            if target and interaction.target != target:
                continue
            
            if interaction_type and interaction.interaction_type != interaction_type:
                continue
            
            if method_name and interaction.method_name != method_name:
                continue
            
            result.append(interaction)
        
        return result
    
    def get_interaction_count(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        interaction_type: Optional[InteractionType] = None,
        method_name: Optional[str] = None
    ) -> int:
        """
        Get count of interactions matching the specified criteria.
        
        Args:
            source: Optional source component
            target: Optional target component
            interaction_type: Optional interaction type
            method_name: Optional method name
            
        Returns:
            Count of matching interactions
        """
        return len(self.get_interactions(source, target, interaction_type, method_name))
    
    def get_interaction_sequence(self) -> List[ComponentInteraction]:
        """
        Get interactions in chronological order.
        
        Returns:
            List of interactions in chronological order
        """
        return sorted(self.interactions, key=lambda x: x.timestamp)
    
    def get_component_interactions(self, component: str) -> List[ComponentInteraction]:
        """
        Get all interactions involving the specified component.
        
        Args:
            component: Component name
            
        Returns:
            List of interactions involving the component
        """
        return [
            interaction for interaction in self.interactions
            if interaction.source == component or interaction.target == component
        ]
    
    def get_components(self) -> Set[str]:
        """
        Get all components involved in interactions.
        
        Returns:
            Set of component names
        """
        components = set()
        
        for interaction in self.interactions:
            components.add(interaction.source)
            components.add(interaction.target)
        
        return components
    
    def clear(self):
        """Clear all recorded interactions."""
        self.interactions = []
        self.start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "interactions": [interaction.to_dict() for interaction in self.interactions],
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "interaction_count": len(self.interactions),
            "component_count": len(self.get_components())
        }


class TrackedComponent:
    """
    Base class for tracked components.
    """
    
    def __init__(self, name: str, tracker: InteractionTracker):
        """
        Initialize a tracked component.
        
        Args:
            name: Component name
            tracker: Interaction tracker
        """
        self.name = name
        self.tracker = tracker
    
    def track_method(self, method: Callable) -> Callable:
        """
        Decorator for tracking method calls.
        
        Args:
            method: Method to track
            
        Returns:
            Tracked method
        """
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # Get target from method call
            if len(args) > 0 and hasattr(args[0], "__class__"):
                target = args[0].__class__.__name__
            else:
                target = "unknown"
            
            # Record method call
            interaction = ComponentInteraction(
                source=self.name,
                target=target,
                interaction_type=InteractionType.METHOD_CALL,
                method_name=method.__name__,
                args=args,
                kwargs=kwargs
            )
            
            start_time = time.time()
            
            try:
                # Call method
                result = method(*args, **kwargs)
                
                # Record result
                interaction.result = result
                interaction.interaction_type = InteractionType.RESPONSE
            except Exception as e:
                # Record exception
                interaction.exception = e
                interaction.interaction_type = InteractionType.EXCEPTION
                
                # Re-raise exception
                raise
            finally:
                # Record duration
                interaction.duration = time.time() - start_time
                
                # Record interaction
                self.tracker.record_interaction(interaction)
            
            return result
        
        return wrapper
    
    def track_async_method(self, method: Callable) -> Callable:
        """
        Decorator for tracking async method calls.
        
        Args:
            method: Async method to track
            
        Returns:
            Tracked async method
        """
        @functools.wraps(method)
        async def wrapper(*args, **kwargs):
            # Get target from method call
            if len(args) > 0 and hasattr(args[0], "__class__"):
                target = args[0].__class__.__name__
            else:
                target = "unknown"
            
            # Record method call
            interaction = ComponentInteraction(
                source=self.name,
                target=target,
                interaction_type=InteractionType.METHOD_CALL,
                method_name=method.__name__,
                args=args,
                kwargs=kwargs
            )
            
            start_time = time.time()
            
            try:
                # Call method
                result = await method(*args, **kwargs)
                
                # Record result
                interaction.result = result
                interaction.interaction_type = InteractionType.RESPONSE
            except Exception as e:
                # Record exception
                interaction.exception = e
                interaction.interaction_type = InteractionType.EXCEPTION
                
                # Re-raise exception
                raise
            finally:
                # Record duration
                interaction.duration = time.time() - start_time
                
                # Record interaction
                self.tracker.record_interaction(interaction)
            
            return result
        
        return wrapper
    
    def track_event(
        self,
        event_name: str,
        target: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Track an event.
        
        Args:
            event_name: Event name
            target: Target component
            data: Optional event data
        """
        # Record event
        interaction = ComponentInteraction(
            source=self.name,
            target=target,
            interaction_type=InteractionType.EVENT,
            method_name=event_name,
            kwargs=data or {}
        )
        
        # Record interaction
        self.tracker.record_interaction(interaction)


def track_class(cls: Type, name: Optional[str] = None, tracker: Optional[InteractionTracker] = None) -> Type:
    """
    Decorator for tracking all methods of a class.
    
    Args:
        cls: Class to track
        name: Optional component name (defaults to class name)
        tracker: Optional interaction tracker
        
    Returns:
        Tracked class
    """
    # Get component name
    component_name = name or cls.__name__
    
    # Get or create tracker
    component_tracker = tracker or InteractionTracker()
    
    # Create tracked component
    tracked_component = TrackedComponent(component_name, component_tracker)
    
    # Track methods
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and not attr_name.startswith("__"):
            if asyncio.iscoroutinefunction(attr_value):
                setattr(cls, attr_name, tracked_component.track_async_method(attr_value))
            else:
                setattr(cls, attr_name, tracked_component.track_method(attr_value))
    
    return cls


# Example usage
if __name__ == "__main__":
    # Create interaction tracker
    tracker = InteractionTracker()
    
    # Create tracked component
    component = TrackedComponent("TestComponent", tracker)
    
    # Define test method
    @component.track_method
    def test_method(x, y):
        return x + y
    
    # Call test method
    result = test_method(1, 2)
    
    # Get interactions
    interactions = tracker.get_interactions()
    
    # Print interactions
    for interaction in interactions:
        print(f"{interaction.source} -> {interaction.target}: {interaction.method_name}")
        print(f"  Args: {interaction.args}")
        print(f"  Result: {interaction.result}")
        print(f"  Duration: {interaction.duration} seconds")
