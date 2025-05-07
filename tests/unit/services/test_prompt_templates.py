"""Tests for prompt templates."""

import pytest

from app.services.prompt_templates import (
    Message,
    MessageRole,
    PromptTemplate,
    get_template,
    DOCUMENTATION_SEARCH_TEMPLATE,
)


class TestPromptTemplates:
    """Tests for prompt templates."""

    def test_message_role_enum(self):
        """Test MessageRole enum."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.FUNCTION == "function"

    def test_message_model(self):
        """Test Message model."""
        message = Message(role=MessageRole.SYSTEM, content="Test content")
        assert message.role == MessageRole.SYSTEM
        assert message.content == "Test content"

    def test_prompt_template_format(self):
        """Test PromptTemplate.format."""
        template = PromptTemplate(
            name="test",
            description="Test template",
            system_message="System message with {variable1}",
            user_message_template="User message with {variable2}",
            variables=["variable1", "variable2"],
        )

        messages = template.format(variable1="value1", variable2="value2")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System message with value1"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User message with value2"

    def test_prompt_template_format_missing_variable(self):
        """Test PromptTemplate.format with missing variable."""
        template = PromptTemplate(
            name="test",
            description="Test template",
            system_message="System message with {variable1}",
            user_message_template="User message with {variable2}",
            variables=["variable1", "variable2"],
        )

        with pytest.raises(ValueError, match="Missing required variable: variable2"):
            template.format(variable1="value1")

    def test_prompt_template_format_extra_variable(self):
        """Test PromptTemplate.format with extra variable."""
        template = PromptTemplate(
            name="test",
            description="Test template",
            system_message="System message with {variable1}",
            user_message_template="User message with {variable2}",
            variables=["variable1", "variable2"],
        )

        messages = template.format(variable1="value1", variable2="value2", variable3="value3")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System message with value1"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User message with value2"

    def test_get_template(self):
        """Test get_template."""
        template = get_template("documentation_search")
        assert template.name == "documentation_search"
        assert template.description == "Template for searching documentation"

    def test_get_template_not_found(self):
        """Test get_template with non-existent template."""
        with pytest.raises(ValueError, match="Template not found: non_existent"):
            get_template("non_existent")

    def test_documentation_search_template(self):
        """Test DOCUMENTATION_SEARCH_TEMPLATE."""
        messages = DOCUMENTATION_SEARCH_TEMPLATE.format(query="test query")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Technical Documentation Assistant" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert "test query" in messages[1]["content"]
