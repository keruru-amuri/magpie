"""Prompt templates for Azure OpenAI service."""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Message roles for chat completions."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class Message(BaseModel):
    """Message model for chat completions."""

    role: MessageRole
    content: str


class PromptTemplate(BaseModel):
    """Base prompt template model."""

    name: str
    description: str
    system_message: str = ""
    user_message_template: str = ""
    variables: List[str] = Field(default_factory=list)

    def format(self, **kwargs: Any) -> List[Dict[str, str]]:
        """
        Format the prompt template with the provided variables.

        Args:
            **kwargs: Variables to format the template with.

        Returns:
            List of messages for chat completion.

        Raises:
            ValueError: If a required variable is missing.
        """
        # Validate variables
        for var in self.variables:
            if var not in kwargs:
                raise ValueError(f"Missing required variable: {var}")

        # Create messages
        messages = []

        # Add system message if provided
        if self.system_message:
            system_content = self._format_message(self.system_message, **kwargs)
            messages.append({"role": MessageRole.SYSTEM, "content": system_content})

        # Add user message if provided
        if self.user_message_template:
            user_content = self._format_message(self.user_message_template, **kwargs)
            messages.append({"role": MessageRole.USER, "content": user_content})

        return messages

    def _format_message(self, template: str, **kwargs: Any) -> str:
        """
        Format a message template with the provided variables.

        Args:
            template: Message template.
            **kwargs: Variables to format the template with.

        Returns:
            Formatted message.
        """
        # Replace variables in the template
        formatted = template

        # Use regex to find all variables in the format {variable_name}
        variables = re.findall(r"\{([^}]+)\}", template)

        # Replace each variable with its value
        for var in variables:
            if var in kwargs:
                formatted = formatted.replace(f"{{{var}}}", str(kwargs[var]))

        return formatted


# Documentation Assistant Templates
DOCUMENTATION_SEARCH_TEMPLATE = PromptTemplate(
    name="documentation_search",
    description="Template for searching documentation",
    system_message=(
        "You are a Technical Documentation Assistant for aircraft maintenance. "
        "Your role is to help maintenance technicians find relevant information "
        "in technical documentation. Be precise, accurate, and safety-focused. "
        "Always cite your sources when providing information. "
        "If the documentation contains safety warnings or cautions, emphasize them in your response. "
        "If there are specific procedures or steps mentioned in the documentation, present them clearly and in order. "
        "If you're unsure about any information or if the documentation doesn't cover the query, acknowledge this clearly."
    ),
    user_message_template=(
        "I need to find information about {query} in our technical documentation. "
        "Below are the search results from our documentation database:\n\n"
        "{search_results}\n\n"
        "Please provide a comprehensive answer based on these sources. "
        "Cite specific sources when providing information (e.g., 'According to SOURCE 1...'). "
        "If the information from different sources conflicts, point this out and explain the differences. "
        "If the search results don't adequately address my query, please acknowledge this."
    ),
    variables=["query", "search_results"],
)

DOCUMENTATION_SUMMARY_TEMPLATE = PromptTemplate(
    name="documentation_summary",
    description="Template for summarizing documentation",
    system_message=(
        "You are a Technical Documentation Assistant for aircraft maintenance. "
        "Your role is to summarize technical documentation for maintenance technicians. "
        "Be precise, accurate, and safety-focused. "
        "Organize your summary by key sections and topics. "
        "Highlight safety warnings, cautions, and critical information. "
        "Emphasize maintenance procedures, inspection requirements, and regulatory compliance information. "
        "Use clear, concise language appropriate for aviation maintenance professionals."
    ),
    user_message_template=(
        "Please provide a comprehensive summary of the following technical documentation:\n\n"
        "Title: {document_title}\n\n"
        "Content: {document_content}\n\n"
        "{sections_info}"
        "Focus on the following in your summary:\n"
        "1. Document purpose and scope\n"
        "2. Key safety information and warnings\n"
        "3. Critical maintenance procedures and requirements\n"
        "4. Inspection and testing procedures\n"
        "5. Regulatory compliance information\n"
        "6. Cross-references to other documents (if mentioned)\n\n"
        "Organize your summary by major sections and provide a clear structure."
    ),
    variables=["document_title", "document_content", "sections_info"],
)

# Document Comparison Template
DOCUMENT_COMPARISON_TEMPLATE = PromptTemplate(
    name="document_comparison",
    description="Template for comparing documents",
    system_message=(
        "You are a Technical Documentation Assistant for aircraft maintenance. "
        "Your role is to compare technical documentation and highlight key similarities and differences. "
        "Be precise, accurate, and safety-focused. "
        "When comparing documents, focus on technical details, procedures, safety information, and regulatory requirements. "
        "Highlight important differences that could impact maintenance procedures or safety. "
        "Organize your comparison in a clear, structured format that makes it easy to understand the key points."
    ),
    user_message_template=(
        "I need to compare the following documents:\n\n"
        "{documents}\n\n"
        "Please provide a detailed comparison{aspect_prompt}, highlighting key similarities and differences. "
        "Focus on technical details, procedures, safety information, and regulatory requirements. "
        "Organize your comparison as follows:\n"
        "1. Overview of the documents being compared\n"
        "2. Key similarities\n"
        "3. Important differences\n"
        "4. Implications for maintenance procedures\n"
        "5. Safety considerations\n"
        "6. Recommendation on which document to follow in which circumstances (if applicable)"
    ),
    variables=["documents", "aspect_prompt"],
)

# Troubleshooting Advisor Templates
TROUBLESHOOTING_ANALYSIS_TEMPLATE = PromptTemplate(
    name="troubleshooting_analysis",
    description="Template for analyzing troubleshooting cases",
    system_message=(
        "You are a Troubleshooting Advisor for aircraft maintenance. "
        "Your role is to help maintenance technicians diagnose and resolve issues. "
        "Be methodical, precise, and safety-focused."
    ),
    user_message_template=(
        "I'm experiencing the following issue with {system_name}:\n\n"
        "Symptoms: {symptoms}\n\n"
        "Aircraft Type: {aircraft_type}\n"
        "System: {system_name}\n"
        "Previous Maintenance: {previous_maintenance}\n\n"
        "Please analyze the issue and provide a step-by-step troubleshooting guide."
    ),
    variables=["system_name", "symptoms", "aircraft_type", "previous_maintenance"],
)

TROUBLESHOOTING_PROCEDURE_TEMPLATE = PromptTemplate(
    name="troubleshooting_procedure",
    description="Template for generating detailed troubleshooting procedures",
    system_message=(
        "You are a Troubleshooting Advisor for aircraft maintenance. "
        "Your role is to enhance troubleshooting procedures with detailed steps, "
        "additional notes, and troubleshooting tips. "
        "Be methodical, precise, and safety-focused. "
        "Your output should be in JSON format with the following structure:\n"
        "{\n"
        "  \"detailed_steps\": [array of detailed step-by-step instructions],\n"
        "  \"additional_notes\": [array of important notes and warnings],\n"
        "  \"troubleshooting_tips\": [array of expert tips for this procedure]\n"
        "}"
    ),
    user_message_template=(
        "I need to enhance the following troubleshooting procedure for {system_id}, "
        "specifically addressing cause {cause_id}:\n\n"
        "{procedure}\n\n"
        "Please provide detailed steps, additional notes, and troubleshooting tips "
        "that would help a maintenance technician successfully complete this procedure. "
        "Include specific details about potential challenges, common mistakes, and "
        "how to verify that each step has been completed correctly. "
        "Your response should be in JSON format as specified in the system message."
    ),
    variables=["procedure", "system_id", "cause_id"],
)

# Maintenance Procedure Generator Templates
MAINTENANCE_PROCEDURE_TEMPLATE = PromptTemplate(
    name="maintenance_procedure",
    description="Template for generating maintenance procedures",
    system_message=(
        "You are a Maintenance Procedure Generator for aircraft maintenance. "
        "Your role is to generate customized maintenance procedures based on "
        "aircraft configuration and regulatory requirements. "
        "Be precise, detailed, and safety-focused."
    ),
    user_message_template=(
        "I need a maintenance procedure for {procedure_type} on {aircraft_type}, "
        "specifically for the {system_name} system.\n\n"
        "Configuration: {configuration}\n"
        "Regulatory Requirements: {regulatory_requirements}\n\n"
        "Please generate a step-by-step maintenance procedure with safety precautions, "
        "required tools, and estimated time."
    ),
    variables=[
        "procedure_type",
        "aircraft_type",
        "system_name",
        "configuration",
        "regulatory_requirements",
    ],
)

MAINTENANCE_PROCEDURE_GENERATION_TEMPLATE = PromptTemplate(
    name="maintenance_procedure_generation",
    description="Template for generating detailed maintenance procedures from scratch using LLM",
    system_message=(
        "You are an expert aircraft maintenance engineer with extensive experience in creating "
        "detailed maintenance procedures for various aircraft systems. Your task is to generate "
        "a comprehensive, safety-focused maintenance procedure based on the provided information. "
        "Your procedures must adhere to aviation industry standards, regulatory requirements, and "
        "best practices.\n\n"
        "Your procedures should include:\n"
        "1. Clear title and description\n"
        "2. Required qualifications and certifications\n"
        "3. Estimated duration\n"
        "4. Comprehensive safety precautions\n"
        "5. Required tools and materials with specifications\n"
        "6. Detailed step-by-step instructions with warnings and cautions where appropriate\n"
        "7. Testing and verification steps\n"
        "8. Documentation and sign-off requirements\n"
        "9. References to relevant manuals and regulations\n\n"
        "Format your response as a structured JSON object that can be parsed by the system."
    ),
    user_message_template=(
        "I need a detailed maintenance procedure for {procedure_type} on {aircraft_type}, "
        "specifically for the {system} system.\n\n"
        "Aircraft details:\n"
        "- Type: {aircraft_type}\n"
        "- Model: {aircraft_model}\n"
        "- Configuration: {configuration}\n\n"
        "System details:\n"
        "- System: {system}\n"
        "- Components: {components}\n\n"
        "Procedure requirements:\n"
        "- Type: {procedure_type}\n"
        "- Regulatory framework: {regulatory_requirements}\n"
        "- Special considerations: {special_considerations}\n\n"
        "Please generate a comprehensive maintenance procedure in JSON format with the following structure:\n"
        "```json\n"
        "{\n"
        "  \"id\": \"unique-id\",\n"
        "  \"title\": \"Procedure Title\",\n"
        "  \"description\": \"Detailed description\",\n"
        "  \"aircraft_type\": \"Aircraft type\",\n"
        "  \"system\": \"System name\",\n"
        "  \"estimated_time\": \"Estimated time in hours\",\n"
        "  \"skill_level\": \"Required skill level\",\n"
        "  \"safety_precautions\": [\"List of safety precautions\"],\n"
        "  \"tools_required\": [{\"id\": \"tool-id\", \"name\": \"Tool name\", \"specification\": \"Tool specs\"}],\n"
        "  \"parts_required\": [{\"id\": \"part-id\", \"name\": \"Part name\", \"part_number\": \"Part number\", \"quantity\": 1}],\n"
        "  \"steps\": [\n"
        "    {\n"
        "      \"step_number\": 1,\n"
        "      \"title\": \"Step title\",\n"
        "      \"description\": \"Step description\",\n"
        "      \"cautions\": [\"List of cautions\"],\n"
        "      \"images\": []\n"
        "    }\n"
        "  ],\n"
        "  \"references\": [{\"id\": \"ref-id\", \"type\": \"reference type\", \"title\": \"Reference title\", \"section\": \"Section\"}]\n"
        "}\n"
        "```"
    ),
    variables=[
        "procedure_type",
        "aircraft_type",
        "aircraft_model",
        "system",
        "components",
        "configuration",
        "regulatory_requirements",
        "special_considerations",
    ],
)

MAINTENANCE_PROCEDURE_ENHANCEMENT_TEMPLATE = PromptTemplate(
    name="maintenance_procedure_enhancement",
    description="Template for enhancing template-based maintenance procedures with LLM",
    system_message=(
        "You are an expert aircraft maintenance engineer specializing in enhancing and customizing "
        "maintenance procedures for specific aircraft configurations. Your task is to take a base "
        "maintenance procedure template and enhance it with additional details, safety considerations, "
        "and configuration-specific steps based on the provided aircraft information.\n\n"
        "Your enhancements should:\n"
        "1. Preserve the core structure and steps of the original procedure\n"
        "2. Add configuration-specific details and steps\n"
        "3. Include additional safety precautions relevant to the specific aircraft\n"
        "4. Provide more detailed instructions where the template is generic\n"
        "5. Add relevant troubleshooting guidance where appropriate\n"
        "6. Ensure all regulatory requirements are addressed\n\n"
        "Format your response as a structured JSON object that matches the structure of the input template "
        "but with your enhancements incorporated."
    ),
    user_message_template=(
        "I need to enhance the following maintenance procedure template for a specific aircraft configuration.\n\n"
        "Base procedure template:\n"
        "{base_procedure}\n\n"
        "Aircraft details:\n"
        "- Type: {aircraft_type}\n"
        "- Model: {aircraft_model}\n"
        "- Configuration: {configuration}\n\n"
        "System details:\n"
        "- System: {system}\n"
        "- Components: {components}\n\n"
        "Additional requirements:\n"
        "- Regulatory framework: {regulatory_requirements}\n"
        "- Special considerations: {special_considerations}\n\n"
        "Please enhance the procedure with configuration-specific details, additional safety precautions, "
        "and more detailed instructions where needed. Maintain the same JSON structure as the base template."
    ),
    variables=[
        "base_procedure",
        "aircraft_type",
        "aircraft_model",
        "system",
        "components",
        "configuration",
        "regulatory_requirements",
        "special_considerations",
    ],
)

# Context Management Templates
CONVERSATION_SUMMARY_TEMPLATE = PromptTemplate(
    name="conversation_summary",
    description="Template for summarizing conversation history",
    system_message=(
        "You are a Conversation Summarizer for an aircraft maintenance AI assistant. "
        "Your role is to create concise, accurate summaries of conversation history "
        "between users and the assistant. Focus on capturing key information, questions, "
        "and decisions made during the conversation. Be objective and factual."
    ),
    user_message_template=(
        "Please summarize the following conversation between a user and an AI assistant "
        "focused on aircraft maintenance. Capture the main topics, questions, and key information "
        "exchanged. Be concise but comprehensive.\n\n"
        "Conversation:\n{conversation}\n\n"
        "Create a summary that could be used to quickly understand the context of this conversation."
    ),
    variables=["conversation"],
)

# Model Selection Templates
COMPLEXITY_ANALYSIS_TEMPLATE = PromptTemplate(
    name="complexity_analysis",
    description="Template for analyzing request complexity",
    system_message=(
        "You are a Request Complexity Analyzer for an AI assistant. "
        "Your role is to analyze user requests and determine their complexity "
        "across multiple dimensions. Be objective and analytical."
    ),
    user_message_template=(
        "Analyze the complexity of the following user request across these dimensions:\n\n"
        "1. Reasoning depth (0-10): How much reasoning or analysis is required?\n"
        "2. Specialized knowledge (0-10): How much domain-specific knowledge is needed?\n"
        "3. Context dependency (0-10): How much does this depend on previous context?\n"
        "4. Output structure (0-10): How structured or formatted should the output be?\n\n"
        "User request: {query}\n\n"
        "Previous conversation context (if any):\n{conversation_history}\n\n"
        "Provide scores for each dimension and a brief reasoning for your assessment. "
        "Format your response as follows:\n"
        "token_count: [approximate token count]\n"
        "reasoning_depth: [score]\n"
        "specialized_knowledge: [score]\n"
        "context_dependency: [score]\n"
        "output_structure: [score]\n"
        "reasoning: [brief explanation of your assessment]"
    ),
    variables=["query", "conversation_history"],
)

# Dictionary of all templates
TEMPLATES = {
    "documentation_search": DOCUMENTATION_SEARCH_TEMPLATE,
    "documentation_summary": DOCUMENTATION_SUMMARY_TEMPLATE,
    "document_comparison": DOCUMENT_COMPARISON_TEMPLATE,
    "troubleshooting_analysis": TROUBLESHOOTING_ANALYSIS_TEMPLATE,
    "troubleshooting_procedure": TROUBLESHOOTING_PROCEDURE_TEMPLATE,
    "maintenance_procedure": MAINTENANCE_PROCEDURE_TEMPLATE,
    "maintenance_procedure_generation": MAINTENANCE_PROCEDURE_GENERATION_TEMPLATE,
    "maintenance_procedure_enhancement": MAINTENANCE_PROCEDURE_ENHANCEMENT_TEMPLATE,
    "conversation_summary": CONVERSATION_SUMMARY_TEMPLATE,
    "complexity_analysis": COMPLEXITY_ANALYSIS_TEMPLATE,
}


def get_template(template_name: str) -> PromptTemplate:
    """
    Get a prompt template by name.

    Args:
        template_name: Name of the template.

    Returns:
        Prompt template.

    Raises:
        ValueError: If the template is not found.
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template not found: {template_name}")
    return TEMPLATES[template_name]
