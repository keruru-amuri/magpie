"""
Serialization and deserialization methods for Redis cache.
"""
import datetime
import json
import pickle
import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar, Union


class ModelJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for model objects.
    Handles datetime, UUID, and other special types.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {"__datetime__": obj.isoformat()}
        elif isinstance(obj, datetime.date):
            return {"__date__": obj.isoformat()}
        elif isinstance(obj, uuid.UUID):
            return {"__uuid__": str(obj)}
        elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()
        return super().default(obj)


def model_json_decoder_hook(obj):
    """
    Custom JSON decoder hook for model objects.
    Handles datetime, UUID, and other special types.
    """
    if "__datetime__" in obj:
        return datetime.datetime.fromisoformat(obj["__datetime__"])
    elif "__date__" in obj:
        return datetime.date.fromisoformat(obj["__date__"])
    elif "__uuid__" in obj:
        return uuid.UUID(obj["__uuid__"])
    return obj

# Type variable for generic type hints
T = TypeVar('T')


class CacheSerializer:
    """
    Utility class for serializing and deserializing data for caching.
    """

    @staticmethod
    def serialize_json(data: Any) -> bytes:
        """
        Serialize data to JSON bytes.

        Args:
            data: Data to serialize

        Returns:
            bytes: Serialized data
        """
        return json.dumps(data, cls=ModelJSONEncoder).encode('utf-8')

    @staticmethod
    def deserialize_json(data: Optional[bytes]) -> Any:
        """
        Deserialize JSON bytes to data.

        Args:
            data: Serialized data

        Returns:
            Any: Deserialized data
        """
        if data is None:
            return None
        return json.loads(data.decode('utf-8'), object_hook=model_json_decoder_hook)

    @staticmethod
    def serialize_pickle(data: Any) -> bytes:
        """
        Serialize data to pickle bytes.

        Args:
            data: Data to serialize

        Returns:
            bytes: Serialized data
        """
        return pickle.dumps(data)

    @staticmethod
    def deserialize_pickle(data: Optional[bytes]) -> Any:
        """
        Deserialize pickle bytes to data.

        Args:
            data: Serialized data

        Returns:
            Any: Deserialized data
        """
        if data is None:
            return None
        return pickle.loads(data)

    @staticmethod
    def serialize_model(model: Any) -> bytes:
        """
        Serialize model instance to JSON bytes.

        Args:
            model: Model instance

        Returns:
            bytes: Serialized model
        """
        if hasattr(model, 'to_dict'):
            # Use model's to_dict method if available
            return CacheSerializer.serialize_json(model.to_dict())
        elif hasattr(model, '__dict__'):
            # Use __dict__ if to_dict is not available
            return CacheSerializer.serialize_json(model.__dict__)
        else:
            # Fallback to pickle for complex objects
            return CacheSerializer.serialize_pickle(model)

    @staticmethod
    def deserialize_model(data: Optional[bytes], model_class: Type[T]) -> Optional[T]:
        """
        Deserialize JSON bytes to model instance.

        Args:
            data: Serialized model
            model_class: Model class

        Returns:
            Optional[T]: Deserialized model instance
        """
        if data is None:
            return None

        try:
            # Try JSON deserialization first
            json_data = CacheSerializer.deserialize_json(data)

            if hasattr(model_class, 'from_dict'):
                # Use model's from_dict method if available
                return model_class.from_dict(json_data)
            else:
                # Create instance and set attributes
                instance = model_class()
                for key, value in json_data.items():
                    setattr(instance, key, value)
                return instance
        except Exception:
            # Fallback to pickle for complex objects
            try:
                return CacheSerializer.deserialize_pickle(data)
            except Exception:
                return None

    @staticmethod
    def serialize_model_list(models: List[Any]) -> bytes:
        """
        Serialize list of model instances to JSON bytes.

        Args:
            models: List of model instances

        Returns:
            bytes: Serialized model list
        """
        serialized_models = []
        for model in models:
            if hasattr(model, 'to_dict'):
                # Use model's to_dict method if available
                serialized_models.append(model.to_dict())
            elif hasattr(model, '__dict__'):
                # Use __dict__ if to_dict is not available
                serialized_models.append(model.__dict__)
            else:
                # Skip models that can't be serialized to JSON
                continue

        return CacheSerializer.serialize_json(serialized_models)

    @staticmethod
    def deserialize_model_list(
        data: Optional[bytes],
        model_class: Type[T]
    ) -> List[T]:
        """
        Deserialize JSON bytes to list of model instances.

        Args:
            data: Serialized model list
            model_class: Model class

        Returns:
            List[T]: List of deserialized model instances
        """
        if data is None:
            return []

        try:
            json_data = CacheSerializer.deserialize_json(data)
            result = []

            for item in json_data:
                if hasattr(model_class, 'from_dict'):
                    # Use model's from_dict method if available
                    result.append(model_class.from_dict(item))
                else:
                    # Create instance and set attributes
                    instance = model_class()
                    for key, value in item.items():
                        setattr(instance, key, value)
                    result.append(instance)

            return result
        except Exception:
            return []
