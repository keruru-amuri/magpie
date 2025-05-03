# MAGPIE Platform Architecture

## Overview

MAGPIE (MAG Platform for Intelligent Execution) is a multiagent LLM platform designed for aircraft MRO (Maintenance, Repair, and Overhaul) organizations to augment their work with AI capabilities. The platform uses a centralized orchestration approach with intelligent model selection to optimize for both capability and cost.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MAGPIE Platform Architecture                      │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                │
│                                                                         │
│  ┌───────────────┐        ┌───────────────┐       ┌───────────────┐    │
│  │  Web Frontend │        │ Mobile Client  │       │   API Client   │    │
│  └───────────────┘        └───────────────┘       └───────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                   │
│                                                                         │
│  ┌───────────────┐        ┌───────────────┐       ┌───────────────┐    │
│  │   FastAPI     │        │ Authentication │       │  Rate Limiting │    │
│  └───────────────┘        └───────────────┘       └───────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Orchestration Layer                              │
│                                                                         │
│  ┌───────────────┐        ┌───────────────┐       ┌───────────────┐    │
│  │  Orchestrator │        │ Model Selector │       │Context Manager│    │
│  └───────────────┘        └───────────────┘       └───────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Agent Layer                                    │
│                                                                         │
│  ┌───────────────┐        ┌───────────────┐       ┌───────────────┐    │
│  │  Documentation│        │ Troubleshooting│       │  Maintenance  │    │
│  │   Assistant   │        │    Advisor     │       │Procedure Gen. │    │
│  └───────────────┘        └───────────────┘       └───────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                  │
│                                                                         │
│  ┌───────────────┐        ┌───────────────┐       ┌───────────────┐    │
│  │ Azure OpenAI  │        │   PostgreSQL  │       │     Redis     │    │
│  │     API       │        │   (Supabase)  │       │    Cache      │    │
│  └───────────────┘        └───────────────┘       └───────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Backend**: Python with FastAPI
  - Asynchronous request handling
  - Automatic OpenAPI documentation
  - Type hints for better code quality

- **Database**: PostgreSQL with Supabase
  - Structured data storage
  - Real-time capabilities
  - Authentication and authorization

- **Caching**: Redis
  - Conversation context storage
  - Reduce API calls to OpenAI
  - Session management

- **AI Integration**: Azure OpenAI API
  - Primary model: GPT-4.1
  - Additional models for cost optimization
  - Secure API key management

- **Deployment**: Docker containers on Azure
  - Consistent environments
  - Scalability
  - Integration with Azure services

- **CI/CD**: GitHub Actions
  - Automated testing
  - Continuous deployment
  - Quality assurance

## Core Components

### 1. API Layer

- RESTful endpoints for client communication
- Authentication and authorization
- Request validation and error handling
- Rate limiting and usage tracking

### 2. Orchestrator

- Central component for request routing
- Task analysis and classification
- Agent selection and coordination
- Conversation context management

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           Orchestrator Architecture                        │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           Request Classifier                               │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ Intent Analysis │      │ Content Analysis │     │Confidence Scoring│    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                             Agent Router                                   │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ Agent Registry  │      │Capability Matcher│     │ Fallback Handler│    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Response Formatter                                 │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Output Standardize│      │ Result Aggregator│     │ Context Updater │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

### 3. Model Selection System

- Rule-based approach for determining appropriate model size
- Task complexity analysis
- Cost optimization logic
- Performance monitoring and adjustment

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       Model Selection System                               │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        Task Complexity Analyzer                            │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ Token Counter   │      │ Pattern Detector │     │Reasoning Estimator   │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Model Selector                                    │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ Model Registry  │      │ Cost Calculator  │     │Performance Tracker    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Optimization Engine                                │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ Prompt Optimizer│      │ Fallback Strategy│     │ Usage Analytics │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4. Agent Framework

- Abstract base class for all agents
- Common utilities and helpers
- Standardized input/output formats
- Context management utilities

### 5. Specialized Agents

- Technical Documentation Assistant
- Troubleshooting Advisor
- Maintenance Procedure Generator
- Additional agents as needed

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Specialized Agents                                 │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    Technical Documentation Assistant                       │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Document Processor│      │ Query Engine    │     │ Summarizer      │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Cross-Referencer │      │Safety Highlighter│     │ Section Retriever│    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                       Troubleshooting Advisor                              │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Symptom Analyzer │      │ Cause Identifier │     │Decision Tree Gen.│    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │History Integrator│      │Solution Recommender   │Safety Precaution │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    Maintenance Procedure Generator                         │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Template Manager │      │Config Customizer │     │Regulatory Integrator│ │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Tools Identifier │      │Safety Warning Gen│     │Step Sequencer   │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6. Context Management

- Conversation history storage
- User preference tracking
- Session management
- Context window optimization

### 7. Monitoring and Logging

- Request/response logging
- Performance metrics
- Error tracking
- Usage analytics

## Data Flow

```
┌──────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│              │     │               │     │               │     │               │
│    Client    │────▶│   API Layer   │────▶│  Orchestrator │────▶│ Model Selector│
│              │     │               │     │               │     │               │
└──────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
       ▲                                           │                     │
       │                                           ▼                     ▼
       │                                    ┌───────────────┐     ┌───────────────┐
       │                                    │               │     │               │
       │                                    │ Agent Registry│◀────│  Azure OpenAI │
       │                                    │               │     │     API       │
       │                                    └───────────────┘     └───────────────┘
       │                                           │                     ▲
       │                                           ▼                     │
┌──────────────┐     ┌───────────────┐     ┌───────────────┐            │
│              │     │               │     │  Specialized  │            │
│   Response   │◀────│Context Manager│◀────│    Agent      │────────────┘
│              │     │               │     │               │
└──────────────┘     └───────────────┘     └───────────────┘
                            │                     │
                            ▼                     ▼
                     ┌───────────────┐     ┌───────────────┐
                     │               │     │               │
                     │     Redis     │     │  PostgreSQL   │
                     │    Cache      │     │  (Supabase)   │
                     │               │     │               │
                     └───────────────┘     └───────────────┘
```

### Request Flow

1. **Client to API Layer**:
   - Client sends request to API
   - API authenticates and validates request
   - Request is logged and rate limits are checked

2. **API Layer to Orchestrator**:
   - Validated request is passed to orchestrator
   - Orchestrator analyzes request content and intent
   - Request is classified based on required agent capabilities

3. **Orchestrator to Model Selector**:
   - Request complexity is analyzed
   - Optimal model size is determined (GPT-4.1-nano, GPT-4.1-mini, or GPT-4.1)
   - Cost and performance considerations are applied

4. **Orchestrator to Agent Registry**:
   - Appropriate specialized agent is selected based on request classification
   - Agent capabilities are matched to request requirements
   - Fallback options are identified if needed

5. **Agent to Azure OpenAI API**:
   - Selected agent formulates prompt for the LLM
   - Request is sent to Azure OpenAI API with appropriate model
   - Response is received and processed by agent

6. **Agent to Context Manager**:
   - Agent processes LLM response
   - Conversation context is updated with new information
   - Context is stored in Redis cache for active sessions and PostgreSQL for persistence

7. **Context Manager to Response**:
   - Final response is formatted according to client requirements
   - Response is enriched with additional context if needed
   - Response is returned to client

### Data Storage

- **Redis Cache**: Stores active conversation contexts, frequently accessed data, and session information
- **PostgreSQL (Supabase)**: Stores user data, conversation history, agent configurations, and persistent application data

## Model Selection Strategy

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Model Selection Strategy                           │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  ┌─────────────────────────┐  ┌─────────────────────┐  ┌───────────────┐ │
│  │     GPT-4.1-nano        │  │    GPT-4.1-mini     │  │    GPT-4.1    │ │
│  │    (Small Model)        │  │   (Medium Model)    │  │ (Large Model) │ │
│  └─────────────────────────┘  └─────────────────────┘  └───────────────┘ │
│                                                                           │
│  • Classification            │  • Content generation   │  • Complex      │ │
│  • Basic Q&A                 │  • Summarization        │    reasoning    │ │
│  • Routine information       │  • Moderate reasoning   │  • Specialized  │ │
│    retrieval                 │  • Most everyday queries│    knowledge    │ │
│  • Well-defined, narrow tasks│  • Balance of capability│  • Multi-step   │ │
│  • Lower cost, lower latency │    and cost            │    tasks        │ │
│                              │                        │  • Higher cost,  │ │
│                              │                        │    higher       │ │
│                              │                        │    capability   │ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

- **Small Model (GPT-4.1-nano)**: Used for simple tasks like classification, basic Q&A, and routine information retrieval
  - Lower cost, lower latency
  - Suitable for well-defined, narrow tasks

- **Medium Model (GPT-4.1-mini)**: Used for content generation, summarization, and moderate reasoning tasks
  - Balance of capability and cost
  - Handles most everyday queries

- **Large Model (GPT-4.1)**: Used for complex reasoning, specialized knowledge, and multi-step tasks
  - Higher capability, higher cost
  - Reserved for tasks that truly need the additional capabilities

## Security Considerations

- Secure storage of API keys
- Authentication for all API endpoints
- Authorization based on user roles
- Data encryption in transit and at rest
- Compliance with aviation industry standards

## Scalability

- Horizontal scaling of API and agent components
- Database connection pooling
- Caching for frequently accessed data
- Asynchronous processing where appropriate

## Monitoring and Analytics

- Request volume and patterns
- Model usage and costs
- Error rates and types
- Performance metrics by agent and model

## Mock Data Infrastructure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Mock Data Infrastructure                           │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           Data Schema Layer                                │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │ JSON Schemas    │      │Entity Relationships    │Schema Validation │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           Mock Content                                     │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Technical Docs   │      │Troubleshooting DB│     │Maintenance Procs│    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       Storage & Retrieval Layer                            │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │File-based Store │      │ API Endpoints   │     │ Caching System  │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           Utility Layer                                    │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Data Loaders     │      │Data Manipulation │     │Data Generation  │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Integration Layer                                  │
│                                                                           │
│  ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐    │
│  │Toggle Mechanism │      │ Feature Flags   │     │ Documentation   │    │
│  └─────────────────┘      └─────────────────┘     └─────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

The mock data infrastructure provides realistic test data for all three specialized agents during development, with the ability to easily switch between mock and real data sources.

## Future Extensions

- ML-based model selection
- Additional specialized agents
- Integration with MRO systems
- Mobile client applications
- Offline capabilities
