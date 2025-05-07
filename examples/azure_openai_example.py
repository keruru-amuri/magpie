"""Example script for using the Azure OpenAI integration."""

import asyncio
import logging
import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.azure_openai import get_azure_openai_client
from app.services.llm_service import LLMService, ModelSize
from app.services.prompt_templates import get_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def example_chat_completion():
    """Example of using the Azure OpenAI client directly for chat completion."""
    logger.info("Running example_chat_completion")

    # Get the Azure OpenAI client
    client = get_azure_openai_client()

    # Create a simple conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant for aircraft maintenance."},
        {"role": "user", "content": "What are the key safety procedures for aircraft maintenance?"},
    ]

    # Generate a response
    response = client.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )

    # Print the response
    logger.info(f"Response: {response.choices[0].message.content}")
    logger.info(f"Token usage: {response.usage}")


def example_llm_service_with_template():
    """Example of using the LLM service with a template."""
    logger.info("Running example_llm_service_with_template")

    # Create an LLM service
    service = LLMService()

    # Generate a response using a template
    response = service.generate_response(
        template_name="documentation_search",
        variables={"query": "Boeing 737 landing gear maintenance"},
        model_size=ModelSize.MEDIUM,
        temperature=0.7,
        max_tokens=500,
    )

    # Print the response
    logger.info(f"Response: {response['content']}")
    logger.info(f"Token usage: {response['usage']}")


def example_llm_service_with_custom_messages():
    """Example of using the LLM service with custom messages."""
    logger.info("Running example_llm_service_with_custom_messages")

    # Create an LLM service
    service = LLMService()

    # Create custom messages
    messages = [
        {"role": "system", "content": "You are a Troubleshooting Advisor for aircraft maintenance."},
        {"role": "user", "content": "I'm experiencing an issue with the hydraulic system on an Airbus A320. The pressure gauge is fluctuating during operation. What could be the cause?"},
    ]

    # Generate a response
    response = service.generate_custom_response(
        messages=messages,
        model_size=ModelSize.LARGE,
        temperature=0.5,
        max_tokens=800,
    )

    # Print the response
    logger.info(f"Response: {response['content']}")
    logger.info(f"Token usage: {response['usage']}")


async def example_async_chat_completion():
    """Example of using the Azure OpenAI client asynchronously for chat completion."""
    logger.info("Running example_async_chat_completion")

    # Get the Azure OpenAI client
    client = get_azure_openai_client()

    # Create a simple conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant for aircraft maintenance."},
        {"role": "user", "content": "What are the common maintenance issues for Airbus A320 engines?"},
    ]

    # Generate a response asynchronously
    response = await client.async_chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )

    # Print the response
    logger.info(f"Response: {response.choices[0].message.content}")
    logger.info(f"Token usage: {response.usage}")


async def run_async_examples():
    """Run all async examples."""
    await example_async_chat_completion()


def main():
    """Run all examples."""
    logger.info("Starting Azure OpenAI examples")

    # Check if we have valid Azure OpenAI credentials
    from app.core.config import settings

    # Print the current settings for debugging
    logger.info(f"Azure OpenAI API Key: {'Set (hidden)' if settings.AZURE_OPENAI_API_KEY else 'Not set'}")
    logger.info(f"Azure OpenAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Azure OpenAI API Version: {settings.AZURE_OPENAI_API_VERSION}")
    logger.info(f"GPT-4.1 Deployment Name: {settings.GPT_4_1_DEPLOYMENT_NAME}")
    logger.info(f"GPT-4.1-mini Deployment Name: {settings.GPT_4_1_MINI_DEPLOYMENT_NAME}")
    logger.info(f"GPT-4.1-nano Deployment Name: {settings.GPT_4_1_NANO_DEPLOYMENT_NAME}")

    # Check if the endpoint is a placeholder
    is_placeholder_endpoint = "your-resource-name" in settings.AZURE_OPENAI_ENDPOINT.lower()
    if is_placeholder_endpoint:
        logger.warning(f"Azure OpenAI endpoint appears to be a placeholder: {settings.AZURE_OPENAI_ENDPOINT}")
        logger.info("Please update the AZURE_OPENAI_ENDPOINT in your .env file with your actual endpoint URL.")

    if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT or is_placeholder_endpoint:
        logger.warning("Azure OpenAI API key or endpoint not set. Using mock values for demonstration purposes.")
        logger.info("To run this example with real values, set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file.")

        # Print example messages and responses instead
        logger.info("\nExample chat completion response:")
        logger.info("Response: Aircraft maintenance safety procedures include proper tool control, FOD prevention, following technical documentation, using appropriate PPE, and adhering to lockout/tagout procedures for equipment safety.")
        logger.info("Token usage: {'prompt_tokens': 45, 'completion_tokens': 35, 'total_tokens': 80}")

        logger.info("\nExample LLM service with template response:")
        logger.info("Response: The Boeing 737 landing gear maintenance includes regular inspection of shock struts, lubrication of moving parts, checking tire pressure and wear, and testing the retraction system.")
        logger.info("Token usage: {'prompt_tokens': 60, 'completion_tokens': 40, 'total_tokens': 100}")

        logger.info("\nExample LLM service with custom messages response:")
        logger.info("Response: Fluctuating hydraulic pressure on an A320 could indicate air in the system, a failing pump, leaking seals, or a faulty pressure regulator. Check for visible leaks, inspect the reservoir level, and test the pump operation.")
        logger.info("Token usage: {'prompt_tokens': 75, 'completion_tokens': 50, 'total_tokens': 125}")

        logger.info("\nExample async chat completion response:")
        logger.info("Response: Common maintenance issues for A320 engines include fan blade damage, combustion chamber hot spots, fuel nozzle clogs, and EGT sensor failures. Regular borescope inspections help identify these issues early.")
        logger.info("Token usage: {'prompt_tokens': 55, 'completion_tokens': 45, 'total_tokens': 100}")
    else:
        try:
            # Try to initialize the client directly to test the connection
            from openai import AzureOpenAI

            logger.info("Testing direct connection to Azure OpenAI API...")
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )

            # Try a simple API call to check connectivity
            try:
                logger.info(f"Testing deployment: {settings.GPT_4_1_DEPLOYMENT_NAME}")
                response = client.chat.completions.create(
                    model=settings.GPT_4_1_DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello, are you working?"},
                    ],
                    max_tokens=10,
                )
                logger.info(f"Connection test successful! Response: {response.choices[0].message.content}")

                # If we get here, the connection is working, so run the examples
                logger.info("Running examples...")

                # Run synchronous examples
                example_chat_completion()
                example_llm_service_with_template()
                example_llm_service_with_custom_messages()

                # Run asynchronous examples
                asyncio.run(run_async_examples())
            except Exception as e:
                logger.error(f"Error testing deployment: {str(e)}")
                logger.info("This could be due to an invalid deployment name or other API configuration issues.")

                # Try with a different deployment name as a fallback
                try:
                    logger.info("Trying with a generic deployment name 'gpt-4'...")
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "Hello, are you working?"},
                        ],
                        max_tokens=10,
                    )
                    logger.info(f"Fallback test successful! Response: {response.choices[0].message.content}")
                except Exception as e:
                    logger.error(f"Fallback test also failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {str(e)}")
            logger.info("This is likely due to invalid Azure OpenAI credentials or network issues.")

            import traceback
            logger.debug(f"Detailed error: {traceback.format_exc()}")

    logger.info("Finished Azure OpenAI examples")


if __name__ == "__main__":
    main()
