# MAGPIE Platform Frontend Redevelopment Plan

## Overview

This document outlines the comprehensive plan for rebuilding the MAGPIE (MAG Platform for Intelligent Execution) frontend with a focus on creating an intuitive, user-friendly interface for interacting with AI agents. The design principles and UI patterns are specifically tailored for AI agent platforms, ensuring users can effectively collaborate with the system while maintaining control and understanding of the AI's capabilities and limitations.

The plan adopts an **orchestrator-first approach**, where users interact with a unified interface that intelligently routes their queries to the appropriate specialized agents behind the scenes, rather than requiring users to explicitly choose which agent to use. This approach reduces cognitive load, provides a more natural interaction model, and better leverages the platform's orchestration capabilities.

## 1. Frontend Technology Stack Selection

Based on research, we recommend the following technology stack:

- **Framework**: Next.js (React-based framework)
  - Provides server-side rendering for better performance
  - Built-in routing and API routes
  - Strong TypeScript support
  - Excellent developer experience

- **Styling**: Tailwind CSS
  - Utility-first approach for rapid development
  - Highly customizable
  - Great for responsive design
  - Already used in the current frontend

- **State Management**:
  - React Context API for global state
  - React Query for server state management

- **UI Components**:
  - Headless UI (for accessible, unstyled components)
  - Heroicons (for consistent iconography)

- **Testing**:
  - Jest for unit testing
  - React Testing Library for component testing
  - Cypress for end-to-end testing

## 2. Design Principles for AI Agent Platform

Based on research, our design should follow these principles:

1. **Transparency**: Make the AI decision-making process visible to users
2. **User Control**: Allow users to guide and override AI decisions
3. **Feedback Mechanisms**: Provide ways for users to give feedback to improve AI
4. **Confidence Indicators**: Show how confident the AI is in its responses
5. **Clear AI Content Regions**: Visually distinguish AI-generated content
6. **Explainability**: Provide "Why" insights for AI decisions
7. **Risk Alerts**: Warn users about potential limitations or risks
8. **Opt-in/out Controls**: Let users choose when to use AI features

## 3. Orchestrator-First Approach

The MAGPIE platform will adopt an orchestrator-first approach to user interaction, which offers several key advantages:

1. **Lower Cognitive Load**: Users don't need to understand the underlying agent architecture or capabilities - they just need to express their problem.

2. **More Natural Interaction**: It mirrors how humans naturally ask for help ("I need to fix this issue" rather than "I need to speak to the troubleshooting department").

3. **Intelligent Routing**: The system can intelligently route queries to the most appropriate agent or even combine multiple agents for complex queries.

4. **Unified Experience**: Provides a consistent interface regardless of the underlying agent being used.

5. **Future-Proof**: Makes it easier to add new agents without changing the user experience.

### Implementation Strategy

The orchestrator-first approach will be implemented through:

1. **Unified Chat Interface**: A single, powerful chat interface where users can ask any question.

2. **Behind-the-Scenes Routing**: The orchestrator analyzes the query and routes it to the appropriate agent(s) without the user needing to know which agent is handling their request.

3. **Context-Aware UI Elements**: The interface dynamically adapts based on the detected intent - for example, showing document browsers for documentation queries or step-by-step troubleshooting guides for maintenance issues.

4. **Transparent Agent Selection**: While the system automatically selects agents, it still indicates which specialist agent is handling the query (for transparency) and allows manual override if needed.

5. **Specialized Tools When Needed**: For very specific workflows (like generating a complete maintenance procedure), specialized interfaces are accessible from the main chat when appropriate.

## 4. UI Patterns to Implement

We'll incorporate these specific UI patterns for our AI agent interface:

1. **Criteria Controls**: Allow users to adjust parameters for agent behavior
2. **Like/Dislike Feedback**: Simple feedback mechanisms for agent responses
3. **Confidence Status**: Show how confident the agent is in its responses
4. **"How it Works" Documentation**: Explain the agent's capabilities and limitations
5. **AI Content Regions**: Clearly distinguish AI-generated content
6. **The "Why" Insight**: Explain why certain recommendations are made
7. **Risk Alerts**: Warn about potential limitations in complex scenarios
8. **Opt-in/out Controls**: Let users choose when to use AI features

## 5. Project Structure

```
magpie-frontend/
├── public/
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── ...
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   └── ...
│   │   ├── orchestrator/
│   │   │   ├── AgentIndicator.tsx
│   │   │   ├── ConfidenceDisplay.tsx
│   │   │   ├── ContextPanel.tsx
│   │   │   └── ...
│   │   └── content-panels/
│   │       ├── DocumentPanel.tsx
│   │       ├── TroubleshootingPanel.tsx
│   │       ├── MaintenancePanel.tsx
│   │       └── ...
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   ├── ChatContext.tsx
│   │   └── OrchestratorContext.tsx
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useOrchestrator.ts
│   │   └── ...
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   ├── history/
│   │   ├── settings/
│   │   └── profile/
│   ├── services/
│   │   ├── api.ts
│   │   ├── orchestratorService.ts
│   │   └── ...
│   ├── styles/
│   │   └── globals.css
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── ...
├── .eslintrc.js
├── .gitignore
├── next.config.js
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── tsconfig.json
```

The updated structure reflects the orchestrator-first approach with a unified chat interface and contextual panels that adapt based on the type of query being handled.

## 6. Implementation Plan

### Phase 1: Setup and Foundation (1-2 weeks)
1. Initialize Next.js project with TypeScript
2. Configure Tailwind CSS, ESLint, and Prettier
3. Set up project structure and folder organization
4. Create basic layout components (Header, Footer, Layout)
5. Implement responsive design system
6. Set up authentication context and API service

### Phase 2: Core Components (2-3 weeks)
1. Develop reusable UI components
   - Button, Card, Input, Modal, etc.
   - Agent-specific components (AgentCard, AgentChat, etc.)
2. Implement state management with Context API
3. Create agent interaction interface
4. Develop feedback mechanisms for agent responses
5. Implement confidence indicators and explanations

### Phase 3: Unified Chat Interface and Context Panels (2-3 weeks)
1. Develop main chat interface with orchestrator integration
2. Implement dynamic context panels that adapt to query types
3. Create agent indicator system to show which agent is responding
4. Implement document viewer panel for documentation queries
5. Implement troubleshooting panel with step visualization
6. Implement maintenance procedure panel with checklists
7. Create user profile and settings pages

### Phase 4: Testing and Refinement (1-2 weeks)
1. Write unit tests for components and utilities
2. Perform integration testing
3. Conduct accessibility testing
4. Optimize performance
5. Refine UI/UX based on testing results

### Phase 5: Deployment and Documentation (1 week)
1. Set up CI/CD pipeline
2. Deploy to production
3. Document codebase and components
4. Create user documentation

## 7. Key Features to Implement

1. **Unified Chat Interface**
   - Central chat interface for all user queries
   - Intelligent routing to appropriate agents via orchestrator
   - Real-time conversation with context preservation
   - File upload and sharing capabilities
   - Transparent agent switching when needed

2. **Dynamic Context Panels**
   - Context-aware panels that appear based on query type
   - Document viewer for documentation queries
   - Step-by-step troubleshooting guides for technical issues
   - Procedure generator interface for maintenance tasks
   - Seamless transitions between different contexts

3. **Agent Transparency System**
   - Subtle indicators showing which agent is currently engaged
   - Confidence level displays for responses
   - Explanations of why particular agents were selected
   - Option to manually override agent selection if needed

4. **Specialized Capabilities**
   - Document navigation and search with syntax highlighting
   - Troubleshooting decision trees and solution verification
   - Maintenance procedure generation with customization
   - Cross-referencing between different information sources

5. **Conversation Management**
   - History of all conversations across agents
   - Ability to continue previous conversations
   - Saved responses and generated content
   - Export functionality for documentation and procedures

6. **User Management**
   - Authentication and authorization
   - User profiles and preferences
   - Role-based access control
   - Team collaboration features

7. **Settings and Configuration**
   - Orchestrator behavior customization
   - Interface preferences and accessibility options
   - Notification settings
   - API integration options
