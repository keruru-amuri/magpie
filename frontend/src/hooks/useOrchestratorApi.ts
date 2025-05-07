/**
 * Custom hook for interacting with the orchestrator API
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { websocketService } from '../services/websocketService';
import { 
  OrchestratorRequest, 
  OrchestratorResponse, 
  RoutingInfo, 
  Message,
  ApiError,
  AgentType
} from '../types/api';
import { useOrchestrator } from '../components/orchestrator/OrchestratorContext';

interface UseOrchestratorApiOptions {
  onMessageReceived?: (message: Message) => void;
  onTypingStatusChange?: (isTyping: boolean, agentType?: AgentType) => void;
  onAgentChange?: (fromAgent: AgentType, toAgent: AgentType, reason: string) => void;
  onError?: (error: ApiError) => void;
}

export function useOrchestratorApi(options: UseOrchestratorApiOptions = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [routingInfo, setRoutingInfo] = useState<RoutingInfo | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  const { 
    setAgent, 
    currentAgent,
    startMultiAgentCollaboration,
    endMultiAgentCollaboration
  } = useOrchestrator();

  // Connect to WebSocket
  const connectWebSocket = useCallback((userId: string, convId?: string) => {
    websocketService.connect(userId, convId);
    
    // Add message listener
    websocketService.addMessageListener((message) => {
      switch (message.type) {
        case 'message':
          if (options.onMessageReceived && message.payload.message) {
            options.onMessageReceived(message.payload.message);
          }
          break;
        case 'typing':
          if (options.onTypingStatusChange) {
            options.onTypingStatusChange(
              message.payload.isTyping, 
              message.payload.agentType
            );
          }
          break;
        case 'agent_change':
          if (options.onAgentChange) {
            options.onAgentChange(
              message.payload.fromAgent,
              message.payload.toAgent,
              message.payload.reason
            );
          }
          
          // Update the current agent in the orchestrator context
          if (message.payload.toAgent) {
            setAgent(message.payload.toAgent, 0.9); // Default confidence
          }
          break;
        case 'error':
          if (options.onError && message.payload.error) {
            options.onError(message.payload.error);
          }
          setError(message.payload.error);
          break;
      }
    });
    
    return () => {
      websocketService.disconnect();
    };
  }, [options, setAgent]);

  // Join a conversation
  const joinConversation = useCallback((convId: string) => {
    if (convId) {
      setConversationId(convId);
      websocketService.joinConversation(convId);
    }
  }, []);

  // Send a query to the orchestrator
  const sendQuery = useCallback(async (
    query: string, 
    userId: string,
    context?: Record<string, any>,
    forceAgentType?: AgentType
  ): Promise<OrchestratorResponse> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const request: OrchestratorRequest = {
        query,
        userId,
        conversationId: conversationId || undefined,
        context,
        forceAgentType
      };
      
      const response = await api.orchestrator.query(request);
      
      // Update conversation ID if not set
      if (!conversationId && response.conversationId) {
        setConversationId(response.conversationId);
        websocketService.joinConversation(response.conversationId);
      }
      
      // Update agent in orchestrator context
      if (response.agentType) {
        setAgent(response.agentType, response.confidence);
      }
      
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, options, setAgent]);

  // Get routing information for a query
  const getRoutingInfo = useCallback(async (
    query: string
  ): Promise<RoutingInfo> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.orchestrator.getRoutingInfo(query, conversationId || undefined);
      setRoutingInfo(response);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, options]);

  // Get conversation history
  const getConversationHistory = useCallback(async (
    convId: string
  ): Promise<Message[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.orchestrator.getConversationHistory(convId);
      return response.messages;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Delete a conversation
  const deleteConversation = useCallback(async (
    convId: string
  ): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await api.orchestrator.deleteConversation(convId);
      
      // Clear conversation ID if it's the current one
      if (conversationId === convId) {
        setConversationId(null);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, options]);

  return {
    isLoading,
    error,
    routingInfo,
    conversationId,
    connectWebSocket,
    joinConversation,
    sendQuery,
    getRoutingInfo,
    getConversationHistory,
    deleteConversation,
  };
}
