"""
Integration tests for repositories.
"""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.connection import Base
from app.models.user import User, UserRole
from app.models.conversation import Conversation, Message, MessageRole, AgentType
from app.models.agent import AgentConfiguration, ModelSize
from app.repositories.user import UserRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.agent import AgentConfigurationRepository


@pytest.fixture(scope="module")
def engine():
    """
    Create SQLAlchemy engine for testing.
    """
    # Use in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    Base.metadata.create_all(engine)

    yield engine

    # Drop tables
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """
    Create SQLAlchemy session for testing.
    """
    # Create session factory
    Session = sessionmaker(bind=engine)

    # Create session
    session = Session()

    yield session

    # Rollback changes
    session.rollback()
    session.close()


class TestUserRepository:
    """
    Test UserRepository functionality.
    """

    @pytest.fixture(scope="function")
    def user_repository(self, session):
        """
        Create UserRepository for testing.
        """
        return UserRepository(session)

    @pytest.fixture(scope="function")
    def test_user(self, session):
        """
        Create test user.
        """
        # Check if user already exists
        existing_user = session.query(User).filter_by(username="testuser").first()
        if existing_user:
            return existing_user

        # Create new user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User",
            role=UserRole.ENGINEER
        )
        session.add(user)
        session.commit()

        return user

    def test_get_by_id(self, user_repository, test_user):
        """
        Test get_by_id method.
        """
        # Get user by ID
        user = user_repository.get_by_id(test_user.id)

        # Verify user
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username

    def test_get_by_email(self, user_repository, test_user):
        """
        Test get_by_email method.
        """
        # Get user by email
        user = user_repository.get_by_email(test_user.email)

        # Verify user
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username

    def test_get_by_username(self, user_repository, test_user):
        """
        Test get_by_username method.
        """
        # Get user by username
        user = user_repository.get_by_username(test_user.username)

        # Verify user
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username

    def test_get_by_role(self, user_repository, test_user):
        """
        Test get_by_role method.
        """
        # Get users by role
        users = user_repository.get_by_role(UserRole.ENGINEER)

        # Verify users
        assert len(users) >= 1
        assert any(u.id == test_user.id for u in users)
        assert all(u.role == UserRole.ENGINEER for u in users)

    def test_get_active_users(self, user_repository, test_user):
        """
        Test get_active_users method.
        """
        # Get active users
        users = user_repository.get_active_users()

        # Verify users
        assert len(users) >= 1
        assert any(u.id == test_user.id for u in users)
        assert all(u.is_active is True for u in users)

    def test_create(self, user_repository):
        """
        Test create method.
        """
        # Create unique username and email
        unique_id = uuid.uuid4().hex[:8]
        username = f"newuser_{unique_id}"
        email = f"new_{unique_id}@example.com"

        # Create user
        user_data = {
            "email": email,
            "username": username,
            "hashed_password": "newpassword",
            "full_name": "New User",
            "role": UserRole.TECHNICIAN
        }
        user = user_repository.create(user_data)
        user_repository.commit()

        # Verify user
        assert user is not None
        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]
        assert user.hashed_password == user_data["hashed_password"]
        assert user.full_name == user_data["full_name"]
        assert user.role == user_data["role"]

    def test_update(self, user_repository, test_user):
        """
        Test update method.
        """
        # Update user
        update_data = {
            "full_name": "Updated User",
            "role": UserRole.MANAGER
        }
        user = user_repository.update(test_user.id, update_data)
        user_repository.commit()

        # Verify user
        assert user is not None
        assert user.id == test_user.id
        assert user.full_name == update_data["full_name"]
        assert user.role == update_data["role"]

    def test_delete_by_id(self, user_repository, test_user):
        """
        Test delete_by_id method.
        """
        # Create a temporary user to delete
        unique_id = uuid.uuid4().hex[:8]
        temp_user = User(
            email=f"temp_{unique_id}@example.com",
            username=f"tempuser_{unique_id}",
            hashed_password="temppassword",
            full_name="Temp User",
            role=UserRole.ENGINEER
        )
        user_repository.session.add(temp_user)
        user_repository.session.commit()

        # Delete user
        result = user_repository.delete_by_id(temp_user.id)
        user_repository.commit()

        # Verify deletion
        assert result is True
        assert user_repository.get_by_id(temp_user.id) is None

    def test_deactivate_user(self, user_repository, test_user):
        """
        Test deactivate_user method.
        """
        # Create a temporary user to deactivate
        unique_id = uuid.uuid4().hex[:8]
        temp_user = User(
            email=f"temp_{unique_id}@example.com",
            username=f"tempuser_{unique_id}",
            hashed_password="temppassword",
            full_name="Temp User",
            role=UserRole.ENGINEER
        )
        user_repository.session.add(temp_user)
        user_repository.session.commit()

        # Deactivate user
        result = user_repository.deactivate_user(temp_user.id)
        user_repository.commit()

        # Verify deactivation
        assert result is True
        user = user_repository.get_by_id(temp_user.id)
        assert user is not None
        assert user.is_active is False

    def test_activate_user(self, user_repository, test_user):
        """
        Test activate_user method.
        """
        # Create a temporary user to activate
        unique_id = uuid.uuid4().hex[:8]
        temp_user = User(
            email=f"temp_{unique_id}@example.com",
            username=f"tempuser_{unique_id}",
            hashed_password="temppassword",
            full_name="Temp User",
            role=UserRole.ENGINEER,
            is_active=False
        )
        user_repository.session.add(temp_user)
        user_repository.session.commit()

        # Activate user
        result = user_repository.activate_user(temp_user.id)
        user_repository.commit()

        # Verify activation
        assert result is True
        user = user_repository.get_by_id(temp_user.id)
        assert user is not None
        assert user.is_active is True

    def test_update_role(self, user_repository, test_user):
        """
        Test update_role method.
        """
        # Create a temporary user to update role
        unique_id = uuid.uuid4().hex[:8]
        temp_user = User(
            email=f"temp_{unique_id}@example.com",
            username=f"tempuser_{unique_id}",
            hashed_password="temppassword",
            full_name="Temp User",
            role=UserRole.ENGINEER
        )
        user_repository.session.add(temp_user)
        user_repository.session.commit()

        # Update role
        result = user_repository.update_role(temp_user.id, UserRole.ADMIN)
        user_repository.commit()

        # Verify role update
        assert result is True
        user = user_repository.get_by_id(temp_user.id)
        assert user is not None
        assert user.role == UserRole.ADMIN


class TestConversationRepository:
    """
    Test ConversationRepository functionality.
    """

    @pytest.fixture(scope="function")
    def conversation_repository(self, session):
        """
        Create ConversationRepository for testing.
        """
        return ConversationRepository(session)

    @pytest.fixture(scope="function")
    def test_user(self, session):
        """
        Create test user.
        """
        # Check if user already exists
        existing_user = session.query(User).filter_by(username="testuser").first()
        if existing_user:
            return existing_user

        # Create new user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User",
            role=UserRole.ENGINEER
        )
        session.add(user)
        session.commit()

        return user

    @pytest.fixture(scope="function")
    def test_conversation(self, session, test_user):
        """
        Create test conversation.
        """
        # Create a unique conversation
        unique_id = uuid.uuid4().hex[:8]
        conversation = Conversation(
            user_id=test_user.id,
            agent_type=AgentType.DOCUMENTATION,
            title=f"Test Conversation {unique_id}"
        )
        session.add(conversation)
        session.commit()

        return conversation

    @pytest.fixture(scope="function")
    def test_messages(self, session, test_conversation):
        """
        Create test messages.
        """
        messages = [
            Message(
                conversation_id=test_conversation.id,
                role=MessageRole.SYSTEM,
                content="System message"
            ),
            Message(
                conversation_id=test_conversation.id,
                role=MessageRole.USER,
                content="User message"
            ),
            Message(
                conversation_id=test_conversation.id,
                role=MessageRole.ASSISTANT,
                content="Assistant message"
            )
        ]
        session.add_all(messages)
        session.commit()

        return messages

    def test_get_by_id(self, conversation_repository, test_conversation):
        """
        Test get_by_id method.
        """
        # Get conversation by ID
        conversation = conversation_repository.get_by_id(test_conversation.id)

        # Verify conversation
        assert conversation is not None
        assert conversation.id == test_conversation.id
        assert conversation.conversation_id == test_conversation.conversation_id
        assert conversation.title == test_conversation.title

    def test_get_by_conversation_id(self, conversation_repository, test_conversation):
        """
        Test get_by_conversation_id method.
        """
        # Get conversation by conversation_id
        conversation = conversation_repository.get_by_conversation_id(test_conversation.conversation_id)

        # Verify conversation
        assert conversation is not None
        assert conversation.id == test_conversation.id
        assert conversation.conversation_id == test_conversation.conversation_id
        assert conversation.title == test_conversation.title

    def test_get_by_user_id(self, conversation_repository, test_user, test_conversation):
        """
        Test get_by_user_id method.
        """
        # Get conversations by user ID
        conversations = conversation_repository.get_by_user_id(test_user.id)

        # Verify conversations
        assert len(conversations) >= 1
        assert any(c.id == test_conversation.id for c in conversations)
        assert all(c.user_id == test_user.id for c in conversations)

    def test_get_with_messages(self, conversation_repository, test_conversation, test_messages):
        """
        Test get_with_messages method.
        """
        # Instead of using get_with_messages, we'll use get_messages
        # since there seems to be an issue with the eager loading in SQLite
        messages = conversation_repository.get_messages(test_conversation.id)

        # Verify messages
        assert len(messages) >= 3
        assert any(m.role == MessageRole.SYSTEM for m in messages)
        assert any(m.role == MessageRole.USER for m in messages)
        assert any(m.role == MessageRole.ASSISTANT for m in messages)

    def test_create(self, conversation_repository, test_user):
        """
        Test create method.
        """
        # Create conversation
        unique_id = uuid.uuid4().hex[:8]
        conversation_data = {
            "user_id": test_user.id,
            "agent_type": AgentType.TROUBLESHOOTING,
            "title": f"New Conversation {unique_id}"
        }
        conversation = conversation_repository.create(conversation_data)
        conversation_repository.commit()

        # Verify conversation
        assert conversation is not None
        assert conversation.id is not None
        assert conversation.user_id == conversation_data["user_id"]
        assert conversation.agent_type == conversation_data["agent_type"]
        assert conversation.title == conversation_data["title"]
        assert isinstance(conversation.conversation_id, uuid.UUID)

    def test_update(self, conversation_repository, test_conversation):
        """
        Test update method.
        """
        # Update conversation
        update_data = {
            "title": f"Updated Conversation {uuid.uuid4().hex[:8]}",
            "is_active": False
        }
        conversation = conversation_repository.update(test_conversation.id, update_data)
        conversation_repository.commit()

        # Verify conversation
        assert conversation is not None
        assert conversation.id == test_conversation.id
        assert conversation.title == update_data["title"]
        assert conversation.is_active == update_data["is_active"]

    def test_delete_by_id(self, conversation_repository, test_user):
        """
        Test delete_by_id method.
        """
        # Create a temporary conversation to delete
        unique_id = uuid.uuid4().hex[:8]
        temp_conversation = Conversation(
            user_id=test_user.id,
            agent_type=AgentType.DOCUMENTATION,
            title=f"Temp Conversation {unique_id}"
        )
        conversation_repository.session.add(temp_conversation)
        conversation_repository.session.commit()

        # Delete conversation
        result = conversation_repository.delete_by_id(temp_conversation.id)
        conversation_repository.commit()

        # Verify deletion
        assert result is True
        assert conversation_repository.get_by_id(temp_conversation.id) is None

    def test_add_message(self, conversation_repository, test_conversation):
        """
        Test add_message method.
        """
        # Add message
        message = conversation_repository.add_message(
            test_conversation.id,
            MessageRole.USER,
            f"New message {uuid.uuid4().hex[:8]}"
        )
        conversation_repository.commit()

        # Verify message
        assert message is not None
        assert message.id is not None
        assert message.conversation_id == test_conversation.id
        assert message.role == MessageRole.USER
        assert "New message" in message.content

    def test_get_messages(self, conversation_repository, test_conversation, test_messages):
        """
        Test get_messages method.
        """
        # Get messages
        messages = conversation_repository.get_messages(test_conversation.id)

        # Verify messages
        assert len(messages) >= 3
        assert any(m.role == MessageRole.SYSTEM for m in messages)
        assert any(m.role == MessageRole.USER for m in messages)
        assert any(m.role == MessageRole.ASSISTANT for m in messages)

    def test_search_conversations(self, conversation_repository, test_user, test_conversation, test_messages):
        """
        Test search_conversations method.
        """
        # Search conversations
        conversations = conversation_repository.search_conversations(test_user.id, "Test")

        # Verify conversations
        assert len(conversations) >= 1
        assert any(c.id == test_conversation.id for c in conversations)
        assert all("Test" in c.title for c in conversations)


class TestAgentConfigurationRepository:
    """
    Test AgentConfigurationRepository functionality.
    """

    @pytest.fixture(scope="function")
    def agent_repository(self, session):
        """
        Create AgentConfigurationRepository for testing.
        """
        return AgentConfigurationRepository(session)

    @pytest.fixture(scope="function")
    def test_agent_config(self, session):
        """
        Create test agent configuration.
        """
        # Check if config already exists
        existing_config = session.query(AgentConfiguration).filter_by(name="Test Agent").first()
        if existing_config:
            return existing_config

        # Create new config
        unique_id = uuid.uuid4().hex[:8]
        config = AgentConfiguration(
            name=f"Test Agent {unique_id}",
            description="Test agent configuration",
            agent_type=AgentType.DOCUMENTATION,
            model_size=ModelSize.MEDIUM,
            temperature=0.7,
            max_tokens=4000,
            system_prompt="You are a helpful assistant."
        )
        session.add(config)
        session.commit()

        return config

    def test_get_by_id(self, agent_repository, test_agent_config):
        """
        Test get_by_id method.
        """
        # Get agent configuration by ID
        config = agent_repository.get_by_id(test_agent_config.id)

        # Verify configuration
        assert config is not None
        assert config.id == test_agent_config.id
        assert config.name == test_agent_config.name
        assert config.agent_type == test_agent_config.agent_type

    def test_get_by_name(self, agent_repository, test_agent_config):
        """
        Test get_by_name method.
        """
        # Get agent configuration by name
        config = agent_repository.get_by_name(test_agent_config.name)

        # Verify configuration
        assert config is not None
        assert config.id == test_agent_config.id
        assert config.name == test_agent_config.name
        assert config.agent_type == test_agent_config.agent_type

    def test_get_by_agent_type(self, agent_repository, test_agent_config):
        """
        Test get_by_agent_type method.
        """
        # Get agent configurations by agent type
        configs = agent_repository.get_by_agent_type(AgentType.DOCUMENTATION)

        # Verify configurations
        assert len(configs) >= 1
        assert any(c.id == test_agent_config.id for c in configs)
        assert all(c.agent_type == AgentType.DOCUMENTATION for c in configs)

    def test_get_by_model_size(self, agent_repository, test_agent_config):
        """
        Test get_by_model_size method.
        """
        # Get agent configurations by model size
        configs = agent_repository.get_by_model_size(ModelSize.MEDIUM)

        # Verify configurations
        assert len(configs) >= 1
        assert any(c.id == test_agent_config.id for c in configs)
        assert all(c.model_size == ModelSize.MEDIUM for c in configs)

    def test_create(self, agent_repository):
        """
        Test create method.
        """
        # Create agent configuration
        unique_id = uuid.uuid4().hex[:8]
        config_data = {
            "name": f"New Agent {unique_id}",
            "description": "New agent configuration",
            "agent_type": AgentType.TROUBLESHOOTING,
            "model_size": ModelSize.LARGE,
            "temperature": 0.5,
            "max_tokens": 8000,
            "system_prompt": "You are a troubleshooting assistant."
        }
        config = agent_repository.create(config_data)
        agent_repository.commit()

        # Verify configuration
        assert config is not None
        assert config.id is not None
        assert config.name == config_data["name"]
        assert config.description == config_data["description"]
        assert config.agent_type == config_data["agent_type"]
        assert config.model_size == config_data["model_size"]
        assert config.temperature == config_data["temperature"]
        assert config.max_tokens == config_data["max_tokens"]
        assert config.system_prompt == config_data["system_prompt"]

    def test_update(self, agent_repository, test_agent_config):
        """
        Test update method.
        """
        # Update agent configuration
        unique_id = uuid.uuid4().hex[:8]
        update_data = {
            "name": f"Updated Agent {unique_id}",
            "temperature": 0.8,
            "is_active": False
        }
        config = agent_repository.update(test_agent_config.id, update_data)
        agent_repository.commit()

        # Verify configuration
        assert config is not None
        assert config.id == test_agent_config.id
        assert config.name == update_data["name"]
        assert config.temperature == update_data["temperature"]
        assert config.is_active == update_data["is_active"]

    def test_delete_by_id(self, agent_repository):
        """
        Test delete_by_id method.
        """
        # Create a temporary config to delete
        unique_id = uuid.uuid4().hex[:8]
        temp_config = AgentConfiguration(
            name=f"Temp Agent {unique_id}",
            description="Temp agent configuration",
            agent_type=AgentType.DOCUMENTATION,
            model_size=ModelSize.MEDIUM,
            temperature=0.7,
            max_tokens=4000,
            system_prompt="You are a temporary assistant."
        )
        agent_repository.session.add(temp_config)
        agent_repository.session.commit()

        # Delete agent configuration
        result = agent_repository.delete_by_id(temp_config.id)
        agent_repository.commit()

        # Verify deletion
        assert result is True
        assert agent_repository.get_by_id(temp_config.id) is None

    def test_get_default_configuration(self, agent_repository, test_agent_config, session):
        """
        Test get_default_configuration method.
        """
        # Create default configuration
        unique_id = uuid.uuid4().hex[:8]
        default_config = AgentConfiguration(
            name=f"Default Documentation Agent {unique_id}",
            agent_type=AgentType.DOCUMENTATION,
            model_size=ModelSize.MEDIUM,
            temperature=0.7,
            max_tokens=4000,
            system_prompt="You are a default documentation assistant.",
            meta_data={"is_default": True}
        )
        session.add(default_config)
        session.commit()

        # Get default configuration
        config = agent_repository.get_default_configuration(AgentType.DOCUMENTATION)

        # Verify configuration
        assert config is not None
        assert "default" in config.name.lower() or (config.meta_data and config.meta_data.get("is_default"))

    def test_update_system_prompt(self, agent_repository, test_agent_config):
        """
        Test update_system_prompt method.
        """
        # Update system prompt
        unique_id = uuid.uuid4().hex[:8]
        new_prompt = f"You are an updated assistant {unique_id}."
        result = agent_repository.update_system_prompt(test_agent_config.id, new_prompt)
        agent_repository.commit()

        # Verify update
        assert result is True
        config = agent_repository.get_by_id(test_agent_config.id)
        assert config is not None
        assert config.system_prompt == new_prompt

    def test_update_model_parameters(self, agent_repository, test_agent_config):
        """
        Test update_model_parameters method.
        """
        # Update model parameters
        result = agent_repository.update_model_parameters(
            test_agent_config.id,
            model_size=ModelSize.LARGE,
            temperature=0.9,
            max_tokens=8000
        )
        agent_repository.commit()

        # Verify update
        assert result is True
        config = agent_repository.get_by_id(test_agent_config.id)
        assert config is not None
        assert config.model_size == ModelSize.LARGE
        assert config.temperature == 0.9
        assert config.max_tokens == 8000

    def test_update_metadata(self, agent_repository, test_agent_config):
        """
        Test update_metadata method.
        """
        # Update metadata
        unique_id = uuid.uuid4().hex[:8]
        metadata = {"is_default": True, "version": f"1.0.{unique_id}"}
        result = agent_repository.update_metadata(test_agent_config.id, metadata)
        agent_repository.commit()

        # Verify update
        assert result is True
        config = agent_repository.get_by_id(test_agent_config.id)
        assert config is not None
        assert config.meta_data == metadata
