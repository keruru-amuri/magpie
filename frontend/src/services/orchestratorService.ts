/**
 * Orchestrator Service for MAGPIE Platform
 *
 * This service provides functionality for interacting with the orchestrator API
 * and managing agent routing and coordination.
 */

import { api } from './api';
import {
  OrchestratorRequest,
  OrchestratorResponse,
  RoutingInfo,
  AgentType
} from '../types/api';
import analyticsService from './analyticsService';
import { getWebSocketService } from './mockWebsocketService';

// Get WebSocket service - only create one instance
// Use a lazy-loaded singleton pattern to avoid multiple instances
let websocketServiceInstance: any = null;
const getWebSocketServiceInstance = () => {
  if (!websocketServiceInstance) {
    // Only create one instance of the WebSocket service
    websocketServiceInstance = getWebSocketService();

    // Log that we're creating a new instance (for debugging)
    console.log('Created new WebSocket service instance');
  } else {
    // Log that we're reusing an existing instance (for debugging)
    console.log('Reusing existing WebSocket service instance');
  }
  return websocketServiceInstance;
};

// Access the singleton instance
const websocketService = getWebSocketServiceInstance();

/**
 * Query the orchestrator
 * @param query User query
 * @param userId User ID
 * @param conversationId Conversation ID
 * @param context Additional context
 * @param forceAgentType Force specific agent type
 * @returns Orchestrator response
 */
export async function queryOrchestrator(
  query: string,
  userId: string,
  conversationId?: string,
  context?: Record<string, any>,
  forceAgentType?: AgentType
): Promise<OrchestratorResponse> {
  try {
    // Track query event
    analyticsService.trackEvent('orchestrator_query', {
      query,
      userId,
      conversationId,
      forceAgentType
    });

    // Create request
    const request: OrchestratorRequest = {
      query,
      userId,
      conversationId,
      context,
      forceAgentType
    };

    // Send query to orchestrator
    const response = await api.orchestrator.query(request);

    // Track response
    analyticsService.trackEvent('orchestrator_response', {
      query,
      userId,
      conversationId,
      agentType: response.agentType,
      confidence: response.confidence
    });

    return response;
  } catch (error) {
    console.error('Error querying orchestrator:', error);
    throw error;
  }
}

/**
 * Get routing information for a query
 * @param query User query
 * @param conversationId Conversation ID
 * @returns Routing information
 */
export async function getRoutingInfo(
  query: string,
  conversationId?: string
): Promise<RoutingInfo> {
  try {
    return await api.orchestrator.getRoutingInfo(query, conversationId);
  } catch (error) {
    console.error('Error getting routing info:', error);
    throw error;
  }
}

/**
 * Get conversation history
 * @param conversationId Conversation ID
 * @returns Conversation history
 */
export async function getConversationHistory(
  conversationId: string
): Promise<any> {
  try {
    return await api.orchestrator.getConversationHistory(conversationId);
  } catch (error) {
    console.error(`Error getting conversation history for ${conversationId}:`, error);
    throw error;
  }
}

/**
 * Delete conversation
 * @param conversationId Conversation ID
 */
export async function deleteConversation(
  conversationId: string
): Promise<void> {
  try {
    await api.orchestrator.deleteConversation(conversationId);
  } catch (error) {
    console.error(`Error deleting conversation ${conversationId}:`, error);
    throw error;
  }
}

/**
 * Connect to WebSocket
 * @param userId User ID
 * @param conversationId Conversation ID
 * @returns Cleanup function
 */
export function connectWebSocket(
  userId: string,
  conversationId?: string
): () => void {
  websocketService.connect(userId, conversationId);

  return () => {
    websocketService.disconnect();
  };
}

/**
 * Join conversation
 * @param conversationId Conversation ID
 */
export function joinConversation(
  conversationId: string
): void {
  websocketService.joinConversation(conversationId);
}

/**
 * Leave conversation
 */
export function leaveConversation(): void {
  websocketService.leaveConversation();
}

/**
 * Send chat message
 * @param message Message text
 * @param conversationId Conversation ID
 * @param forceAgentType Force specific agent type
 */
export function sendChatMessage(
  message: string,
  conversationId?: string,
  forceAgentType?: string
): void {
  websocketService.sendChatMessage(message, conversationId, forceAgentType);
}

/**
 * Send typing indicator
 * @param isTyping Whether user is typing
 */
export function sendTypingIndicator(
  isTyping: boolean
): void {
  websocketService.sendTypingIndicator(isTyping);
}

/**
 * Send message feedback
 * @param messageId Message ID
 * @param feedback Feedback (positive or negative)
 * @param comments Optional comments
 */
export function sendMessageFeedback(
  messageId: string,
  feedback: 'positive' | 'negative',
  comments?: string
): void {
  websocketService.sendMessageFeedback(messageId, feedback, comments);

  // Track feedback event
  analyticsService.trackEvent('message_feedback', {
    messageId,
    feedback,
    comments
  });
}

/**
 * Add message listener
 * @param listener Message listener
 * @returns Cleanup function
 */
export function addMessageListener(
  listener: (message: any) => void
): () => void {
  websocketService.addMessageListener(listener);

  return () => {
    websocketService.removeMessageListener(listener);
  };
}

/**
 * Add connection listener
 * @param listener Connection listener
 * @returns Cleanup function
 */
export function addConnectionListener(
  listener: (status: 'connected' | 'disconnected' | 'reconnecting') => void
): () => void {
  websocketService.addConnectionListener(listener);

  return () => {
    websocketService.removeConnectionListener(listener);
  };
}

// Export orchestrator service
const orchestratorService = {
  query: queryOrchestrator,
  getRoutingInfo,
  getConversationHistory,
  deleteConversation,
  connectWebSocket,
  joinConversation,
  leaveConversation,
  sendChatMessage,
  sendTypingIndicator,
  sendMessageFeedback,
  addMessageListener,
  addConnectionListener
};

export default orchestratorService;
