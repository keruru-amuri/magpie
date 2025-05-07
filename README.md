# MAGPIE Platform

MAGPIE (MAG Platform for Intelligent Execution) is a multiagent LLM platform designed for aircraft MRO (Maintenance, Repair, and Overhaul) organizations to augment their work with AI capabilities.

## Features

- **Technical Documentation Assistant**: Helps users find, understand, and extract information from technical documentation.
- **Troubleshooting Advisor**: Assists in diagnosing issues and recommending solutions based on symptoms and maintenance history.
- **Maintenance Procedure Generator**: Creates customized maintenance procedures based on aircraft configuration and regulatory requirements.

## Technology Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with Supabase
- **Caching**: Redis
- **AI Integration**: Azure OpenAI API (GPT-4.1)
  - Small model: GPT-4.1-nano
  - Medium model: GPT-4.1-mini
  - Large model: GPT-4.1
- **Deployment**: Docker containers on Azure
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- Azure OpenAI API access

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/keruru-amuri/magpie.git
   cd magpie
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

```bash
docker-compose up -d
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. To check your code:

```bash
flake8 app tests
```

### Examples

Check out the `examples` directory for sample code demonstrating how to use various features of the MAGPIE platform:

- **Azure OpenAI Integration**: See `examples/azure_openai_example.py` for examples of using the Azure OpenAI API integration.

## License

This project is proprietary and confidential.

## Acknowledgments

- MAB Engineering Services for project sponsorship
- Azure OpenAI for AI capabilities
