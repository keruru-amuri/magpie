"""
Unit tests for database models.
"""
import pytest
import uuid
from datetime import datetime

from app.models.base import BaseModel
from app.models.user import User, UserRole
from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.agent import AgentConfiguration, ModelSize


class TestBaseModel:
    """
    Test base model functionality.
    """
    
    def test_to_dict(self):
        """
        Test to_dict method.
        """
        # Create test model class
        class TestModel(BaseModel):
            pass
        
        # Create instance
        model = TestModel()
        model.id = 1
        model.name = "Test"
        
        # Convert to dict
        model_dict = model.to_dict()
        
        # Verify conversion
        assert isinstance(model_dict, dict)
        assert "id" in model_dict
        assert model_dict["id"] == 1
        assert "name" in model_dict
        assert model_dict["name"] == "Test"
        assert "created_at" in model_dict
        assert "updated_at" in model_dict
    
    def test_from_dict(self):
        """
        Test from_dict method.
        """
        # Create test model class
        class TestModel(BaseModel):
            pass
        
        # Create from dict
        data = {
            "id": 1,
            "name": "Test",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        model = TestModel.from_dict(data)
        
        # Verify creation
        assert isinstance(model, TestModel)
        assert model.id == 1
        assert model.name == "Test"
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)
    
    def test_update(self):
        """
        Test update method.
        """
        # Create test model class
        class TestModel(BaseModel):
            pass
        
        # Create instance
        model = TestModel()
        model.id = 1
        model.name = "Test"
        
        # Update instance
        model.update({"name": "Updated", "description": "New field"})
        
        # Verify update
        assert model.name == "Updated"
        assert hasattr(model, "description")
        assert model.description == "New field"


class TestUserModel:
    """
    Test User model.
    """
    
    def test_create_user(self):
        """
        Test creating a user.
        """
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User",
            role=UserRole.ENGINEER
        )
        
        # Verify user
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashedpassword"
        assert user.full_name == "Test User"
        assert user.role == UserRole.ENGINEER
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_user_repr(self):
        """
        Test user string representation.
        """
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword"
        )
        
        # Verify string representation
        assert str(user) == "<User testuser (test@example.com)>"


class TestConversationModel:
    """
    Test Conversation model.
    """
    
    def test_create_conversation(self):
        """
        Test creating a conversation.
        """
        # Create conversation
        conversation = Conversation(
            user_id=1,
            agent_type=AgentType.DOCUMENTATION,
            title="Test Conversation"
        )
        
        # Verify conversation
        assert conversation.user_id == 1
        assert conversation.agent_type == AgentType.DOCUMENTATION
        assert conversation.title == "Test Conversation"
        assert conversation.is_active is True
        assert isinstance(conversation.conversation_id, uuid.UUID)
    
    def test_conversation_repr(self):
        """
        Test conversation string representation.
        """
        # Create conversation
        conversation = Conversation(
            user_id=1,
            agent_type=AgentType.DOCUMENTATION
        )
        
        # Verify string representation
        assert str(conversation) == f"<Conversation {conversation.conversation_id} (documentation)>"


class TestMessageModel:
    """
    Test Message model.
    """
    
    def test_create_message(self):
        """
        Test creating a message.
        """
        # Create message
        message = Message(
            conversation_id=1,
            role=MessageRole.USER,
            content="Hello, world!"
        )
        
        # Verify message
        assert message.conversation_id == 1
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
    
    def test_message_repr(self):
        """
        Test message string representation.
        """
        # Create message
        message = Message(
            conversation_id=1,
            role=MessageRole.USER,
            content="Hello, world!"
        )
        message.id = 42
        
        # Verify string representation
        assert str(message) == "<Message 42 (user)>"


class TestAgentConfigurationModel:
    """
    Test AgentConfiguration model.
    """
    
    def test_create_agent_configuration(self):
        """
        Test creating an agent configuration.
        """
        # Create agent configuration
        config = AgentConfiguration(
            name="Test Agent",
            description="Test agent configuration",
            agent_type=AgentType.DOCUMENTATION,
            model_size=ModelSize.MEDIUM,
            temperature=0.7,
            max_tokens=4000,
            system_prompt="You are a helpful assistant."
        )
        
        # Verify agent configuration
        assert config.name == "Test Agent"
        assert config.description == "Test agent configuration"
        assert config.agent_type == AgentType.DOCUMENTATION
        assert config.model_size == ModelSize.MEDIUM
        assert config.temperature == 0.7
        assert config.max_tokens == 4000
        assert config.system_prompt == "You are a helpful assistant."
        assert config.is_active is True
    
    def test_agent_configuration_repr(self):
        """
        Test agent configuration string representation.
        """
        # Create agent configuration
        config = AgentConfiguration(
            name="Test Agent",
            agent_type=AgentType.DOCUMENTATION
        )
        
        # Verify string representation
        assert str(config) == "<AgentConfiguration Test Agent (documentation)>"
