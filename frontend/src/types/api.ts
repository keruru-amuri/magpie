/**
 * API Types for MAGPIE Platform
 * 
 * This file contains TypeScript interfaces for API requests and responses.
 */

// Agent Types
export type AgentType = 'documentation' | 'troubleshooting' | 'maintenance';

// User Types
export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  firstName?: string;
  lastName?: string;
  createdAt: string;
  updatedAt: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: User;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  description: string;
  type: AgentType;
  capabilities: string[];
  metadata?: Record<string, any>;
}

// Message Types
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  agentType?: AgentType;
  confidence?: number;
  metadata?: Record<string, any>;
}

// Conversation Types
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  agentType?: AgentType;
  metadata?: Record<string, any>;
}

// Orchestrator Types
export interface OrchestratorRequest {
  query: string;
  userId: string;
  conversationId?: string;
  context?: Record<string, any>;
  metadata?: Record<string, any>;
  forceAgentType?: AgentType;
  enableMultiAgent?: boolean;
}

export interface OrchestratorResponse {
  response: string;
  agentType: AgentType;
  agentName: string;
  confidence: number;
  conversationId: string;
  metadata?: Record<string, any>;
  followupQuestions?: string[];
}

export interface RoutingInfo {
  agentType: AgentType;
  confidence: number;
  reasoning: string;
  alternativeAgents?: {
    agentType: AgentType;
    confidence: number;
  }[];
}

// Documentation Agent Types
export interface DocumentSearchRequest {
  query: string;
  filters?: {
    documentType?: string[];
    aircraftModel?: string[];
    system?: string[];
    date?: {
      from?: string;
      to?: string;
    };
  };
  limit?: number;
  offset?: number;
}

export interface DocumentSearchResult {
  id: string;
  title: string;
  documentType: string;
  aircraftModel: string;
  system: string;
  relevanceScore: number;
  snippet: string;
  url?: string;
  metadata?: Record<string, any>;
}

export interface DocumentSearchResponse {
  results: DocumentSearchResult[];
  total: number;
  query: string;
}

export interface Document {
  id: string;
  title: string;
  content: string;
  documentType: string;
  aircraftModel: string;
  system: string;
  sections: DocumentSection[];
  metadata?: Record<string, any>;
}

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  subsections?: DocumentSection[];
}

// Troubleshooting Agent Types
export interface TroubleshootingRequest {
  problem: string;
  aircraftModel?: string;
  system?: string;
  component?: string;
  symptoms?: string[];
  context?: Record<string, any>;
}

export interface TroubleshootingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  substeps?: TroubleshootingStep[];
  tools?: string[];
  parts?: { name: string; partNumber: string }[];
  warnings?: string[];
}

export interface TroubleshootingResponse {
  id: string;
  problem: string;
  diagnosis: string;
  steps: TroubleshootingStep[];
  potentialCauses: string[];
  metadata?: Record<string, any>;
}

// Maintenance Agent Types
export interface MaintenanceProcedureRequest {
  equipment: string;
  task: string;
  customizations?: Record<string, any>;
}

export interface MaintenanceStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  warnings?: string[];
  tools?: string[];
  parts?: { name: string; partNumber: string }[];
}

export interface MaintenanceProcedure {
  id: string;
  title: string;
  description: string;
  aircraftType: string;
  estimatedTime: string;
  steps: MaintenanceStep[];
  metadata?: Record<string, any>;
}

// Error Types
export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, any>;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'message' | 'typing' | 'error' | 'connection' | 'agent_change';
  payload: any;
}

export interface MessageEvent extends WebSocketMessage {
  type: 'message';
  payload: {
    message: Message;
    conversationId: string;
  };
}

export interface TypingEvent extends WebSocketMessage {
  type: 'typing';
  payload: {
    isTyping: boolean;
    conversationId: string;
    agentType?: AgentType;
  };
}

export interface AgentChangeEvent extends WebSocketMessage {
  type: 'agent_change';
  payload: {
    fromAgent: AgentType;
    toAgent: AgentType;
    reason: string;
    conversationId: string;
  };
}

export interface ErrorEvent extends WebSocketMessage {
  type: 'error';
  payload: {
    error: ApiError;
    conversationId?: string;
  };
}

export interface ConnectionEvent extends WebSocketMessage {
  type: 'connection';
  payload: {
    status: 'connected' | 'disconnected' | 'reconnecting';
    timestamp: string;
  };
}
