"""
Unit tests for cache serialization.
"""
import pytest
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.core.cache.serialization import CacheSerializer


class TestCacheSerializer:
    """
    Test cache serialization functionality.
    """
    
    def test_serialize_json(self):
        """
        Test serialize_json method.
        """
        # Serialize data
        data = {"name": "Test", "value": 42}
        serialized = CacheSerializer.serialize_json(data)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
        assert b'"name": "Test"' in serialized
        assert b'"value": 42' in serialized
    
    def test_deserialize_json(self):
        """
        Test deserialize_json method.
        """
        # Deserialize data
        serialized = b'{"name": "Test", "value": 42}'
        deserialized = CacheSerializer.deserialize_json(serialized)
        
        # Verify deserialization
        assert isinstance(deserialized, dict)
        assert deserialized["name"] == "Test"
        assert deserialized["value"] == 42
    
    def test_deserialize_json_none(self):
        """
        Test deserialize_json method with None.
        """
        # Deserialize None
        deserialized = CacheSerializer.deserialize_json(None)
        
        # Verify deserialization
        assert deserialized is None
    
    def test_serialize_pickle(self):
        """
        Test serialize_pickle method.
        """
        # Create complex object
        class TestObject:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        # Serialize object
        obj = TestObject("Test", 42)
        serialized = CacheSerializer.serialize_pickle(obj)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
    
    def test_deserialize_pickle(self):
        """
        Test deserialize_pickle method.
        """
        # Create complex object
        class TestObject:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        # Serialize and deserialize object
        obj = TestObject("Test", 42)
        serialized = CacheSerializer.serialize_pickle(obj)
        deserialized = CacheSerializer.deserialize_pickle(serialized)
        
        # Verify deserialization
        assert isinstance(deserialized, TestObject)
        assert deserialized.name == "Test"
        assert deserialized.value == 42
    
    def test_deserialize_pickle_none(self):
        """
        Test deserialize_pickle method with None.
        """
        # Deserialize None
        deserialized = CacheSerializer.deserialize_pickle(None)
        
        # Verify deserialization
        assert deserialized is None
    
    def test_serialize_model_to_dict(self):
        """
        Test serialize_model method with to_dict.
        """
        # Create model with to_dict method
        class TestModel:
            def __init__(self, name, value):
                self.name = name
                self.value = value
            
            def to_dict(self):
                return {"name": self.name, "value": self.value}
        
        # Serialize model
        model = TestModel("Test", 42)
        serialized = CacheSerializer.serialize_model(model)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
        assert b'"name": "Test"' in serialized
        assert b'"value": 42' in serialized
    
    def test_serialize_model_dict(self):
        """
        Test serialize_model method with __dict__.
        """
        # Create model with __dict__
        class TestModel:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        # Serialize model
        model = TestModel("Test", 42)
        serialized = CacheSerializer.serialize_model(model)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
        assert b'"name": "Test"' in serialized
        assert b'"value": 42' in serialized
    
    def test_serialize_model_pickle(self):
        """
        Test serialize_model method with pickle fallback.
        """
        # Create complex model
        class TestModel:
            def __init__(self, name, value):
                self._name = name
                self._value = value
                
            @property
            def name(self):
                return self._name
                
            @property
            def value(self):
                return self._value
        
        # Serialize model
        model = TestModel("Test", 42)
        serialized = CacheSerializer.serialize_model(model)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
    
    def test_deserialize_model_from_dict(self):
        """
        Test deserialize_model method with from_dict.
        """
        # Create model class with from_dict
        class TestModel:
            def __init__(self, name=None, value=None):
                self.name = name
                self.value = value
            
            @classmethod
            def from_dict(cls, data):
                return cls(data["name"], data["value"])
        
        # Serialize and deserialize model
        model = TestModel("Test", 42)
        serialized = CacheSerializer.serialize_model(model)
        deserialized = CacheSerializer.deserialize_model(serialized, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, TestModel)
        assert deserialized.name == "Test"
        assert deserialized.value == 42
    
    def test_deserialize_model_attributes(self):
        """
        Test deserialize_model method with attribute setting.
        """
        # Create model class without from_dict
        class TestModel:
            def __init__(self):
                self.name = None
                self.value = None
        
        # Serialize and deserialize model
        model = TestModel()
        model.name = "Test"
        model.value = 42
        serialized = CacheSerializer.serialize_model(model)
        deserialized = CacheSerializer.deserialize_model(serialized, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, TestModel)
        assert deserialized.name == "Test"
        assert deserialized.value == 42
    
    def test_deserialize_model_pickle(self):
        """
        Test deserialize_model method with pickle fallback.
        """
        # Create complex model
        class TestModel:
            def __init__(self, name, value):
                self._name = name
                self._value = value
                
            @property
            def name(self):
                return self._name
                
            @property
            def value(self):
                return self._value
        
        # Serialize and deserialize model
        model = TestModel("Test", 42)
        serialized = CacheSerializer.serialize_pickle(model)
        deserialized = CacheSerializer.deserialize_model(serialized, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, TestModel)
        assert deserialized.name == "Test"
        assert deserialized.value == 42
    
    def test_deserialize_model_none(self):
        """
        Test deserialize_model method with None.
        """
        # Create model class
        class TestModel:
            pass
        
        # Deserialize None
        deserialized = CacheSerializer.deserialize_model(None, TestModel)
        
        # Verify deserialization
        assert deserialized is None
    
    def test_serialize_model_list(self):
        """
        Test serialize_model_list method.
        """
        # Create model with to_dict method
        class TestModel:
            def __init__(self, name, value):
                self.name = name
                self.value = value
            
            def to_dict(self):
                return {"name": self.name, "value": self.value}
        
        # Serialize model list
        models = [
            TestModel("Test1", 1),
            TestModel("Test2", 2),
            TestModel("Test3", 3)
        ]
        serialized = CacheSerializer.serialize_model_list(models)
        
        # Verify serialization
        assert isinstance(serialized, bytes)
        assert b'"name": "Test1"' in serialized
        assert b'"value": 1' in serialized
        assert b'"name": "Test2"' in serialized
        assert b'"value": 2' in serialized
        assert b'"name": "Test3"' in serialized
        assert b'"value": 3' in serialized
    
    def test_deserialize_model_list_from_dict(self):
        """
        Test deserialize_model_list method with from_dict.
        """
        # Create model class with from_dict
        class TestModel:
            def __init__(self, name=None, value=None):
                self.name = name
                self.value = value
            
            @classmethod
            def from_dict(cls, data):
                return cls(data["name"], data["value"])
            
            def to_dict(self):
                return {"name": self.name, "value": self.value}
        
        # Serialize and deserialize model list
        models = [
            TestModel("Test1", 1),
            TestModel("Test2", 2),
            TestModel("Test3", 3)
        ]
        serialized = CacheSerializer.serialize_model_list(models)
        deserialized = CacheSerializer.deserialize_model_list(serialized, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, list)
        assert len(deserialized) == 3
        assert all(isinstance(model, TestModel) for model in deserialized)
        assert deserialized[0].name == "Test1"
        assert deserialized[0].value == 1
        assert deserialized[1].name == "Test2"
        assert deserialized[1].value == 2
        assert deserialized[2].name == "Test3"
        assert deserialized[2].value == 3
    
    def test_deserialize_model_list_attributes(self):
        """
        Test deserialize_model_list method with attribute setting.
        """
        # Create model class without from_dict
        class TestModel:
            def __init__(self):
                self.name = None
                self.value = None
        
        # Create models
        models = []
        for i in range(3):
            model = TestModel()
            model.name = f"Test{i+1}"
            model.value = i+1
            models.append(model)
        
        # Serialize and deserialize model list
        serialized = CacheSerializer.serialize_model_list(models)
        deserialized = CacheSerializer.deserialize_model_list(serialized, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, list)
        assert len(deserialized) == 3
        assert all(isinstance(model, TestModel) for model in deserialized)
        assert deserialized[0].name == "Test1"
        assert deserialized[0].value == 1
        assert deserialized[1].name == "Test2"
        assert deserialized[1].value == 2
        assert deserialized[2].name == "Test3"
        assert deserialized[2].value == 3
    
    def test_deserialize_model_list_none(self):
        """
        Test deserialize_model_list method with None.
        """
        # Create model class
        class TestModel:
            pass
        
        # Deserialize None
        deserialized = CacheSerializer.deserialize_model_list(None, TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, list)
        assert len(deserialized) == 0
    
    def test_deserialize_model_list_error(self):
        """
        Test deserialize_model_list method with error.
        """
        # Create model class
        class TestModel:
            pass
        
        # Deserialize invalid data
        deserialized = CacheSerializer.deserialize_model_list(b"invalid", TestModel)
        
        # Verify deserialization
        assert isinstance(deserialized, list)
        assert len(deserialized) == 0
