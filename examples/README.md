# MAGPIE Examples

This directory contains example scripts demonstrating how to use various features of the MAGPIE platform.

## Azure OpenAI Integration

The `azure_openai_example.py` script demonstrates how to use the Azure OpenAI integration in the MAGPIE platform.

### Prerequisites

Before running the examples, make sure you have:

1. Set up your Azure OpenAI API credentials in the `.env` file:
   ```
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   ```

2. Configured your model deployment names in the `.env` file:
   ```
   GPT_4_1_DEPLOYMENT_NAME=gpt-4.1
   GPT_4_1_MINI_DEPLOYMENT_NAME=gpt-4.1-mini
   GPT_4_1_NANO_DEPLOYMENT_NAME=gpt-4.1-nano
   ```

### Running the Examples

To run the Azure OpenAI examples:

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the example script
python examples/azure_openai_example.py
```

### Example Features

The Azure OpenAI example script demonstrates:

1. **Direct Chat Completion**: Using the Azure OpenAI client directly for chat completion.
2. **Template-Based Generation**: Using the LLM service with predefined templates.
3. **Custom Message Generation**: Using the LLM service with custom messages.
4. **Asynchronous Chat Completion**: Using the Azure OpenAI client asynchronously.

## Other Examples

More examples will be added as the MAGPIE platform evolves.
