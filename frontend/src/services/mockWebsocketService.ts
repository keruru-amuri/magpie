/**
 * Mock WebSocket Service for MAGPIE Platform
 *
 * This service provides a mock implementation of the WebSocket service for development and testing.
 */

import { WebSocketMessage, AgentType, Message } from '../types/api';

// Import environment configuration
import { API_CONFIG } from '../config/environment';

// Sample agent responses for different query types
const DOCUMENTATION_RESPONSES = [
  "I've found some relevant documentation for you. The maintenance manual section 5.3.2 covers this topic in detail.",
  "According to the aircraft manual, this procedure requires special tooling. Would you like me to list the required tools?",
  "The technical documentation indicates that this component has a service life of 5,000 flight hours or 3 years, whichever comes first."
];

const TROUBLESHOOTING_RESPONSES = [
  "Based on the symptoms you've described, this could be related to the hydraulic pressure sensor. Let me suggest some diagnostic steps.",
  "I've analyzed similar issues and found that this problem is often caused by electrical interference. Have you checked the shielding on the wiring harness?",
  "This appears to be a known issue documented in Service Bulletin SB-2023-42. The recommended fix involves replacing the control module."
];

const MAINTENANCE_RESPONSES = [
  "I'll generate a maintenance procedure for this task. First, ensure you have all required safety equipment and the aircraft is properly secured.",
  "For this maintenance procedure, you'll need to follow these steps: 1. Power down the system, 2. Remove access panel A-42, 3. Disconnect the electrical connectors...",
  "This maintenance task requires calibration after completion. Make sure you have the appropriate calibration equipment available."
];

// Mock implementation of the WebSocket service
export class MockWebSocketService {
  private messageListeners: ((message: WebSocketMessage) => void)[] = [];
  private connectionListeners: ((status: 'connected' | 'disconnected' | 'reconnecting') => void)[] = [];
  private connected = false;
  private userId: string | null = null;
  private conversationId: string | null = null;
  private messageCounter = 0;
  private hasWelcomed = false;

  /**
   * Connect to the mock WebSocket server
   * @param userId User ID for authentication
   * @param conversationId Optional conversation ID to join
   */
  connect(userId: string, conversationId?: string): void {
    this.userId = userId;
    this.conversationId = conversationId || `mock-conversation-${Date.now()}`;
    this.connected = true;

    // Simulate connection delay
    setTimeout(() => {
      this.notifyConnectionListeners('connected');

      // Send welcome message only if we haven't sent one before
      if (!this.hasWelcomed) {
        this.hasWelcomed = true;
        const uniqueId = `welcome-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        this.simulateIncomingMessage({
          type: 'message',
          payload: {
            message: {
              id: uniqueId,
              content: 'Welcome to MAGPIE! I can help with documentation, troubleshooting, or maintenance procedures. How can I assist you today?',
              role: 'assistant',
              timestamp: new Date().toISOString(),
              confidence: 0.95
            },
            conversationId: this.conversationId
          }
        });
      }
    }, 500);
  }

  /**
   * Disconnect from the mock WebSocket server
   */
  disconnect(): void {
    this.connected = false;
    this.userId = null;
    this.conversationId = null;
    this.hasWelcomed = false; // Reset the welcome flag
    this.notifyConnectionListeners('disconnected');
  }

  /**
   * Send a message to the mock WebSocket server
   * @param type Message type
   * @param payload Message payload
   */
  send(type: string, payload: any): void {
    if (!this.connected) {
      console.error('Mock WebSocket not connected');
      return;
    }

    console.log('Mock WebSocket sending message:', { type, payload });

    // Handle different message types
    switch (type) {
      case 'message':
        this.handleChatMessage(payload);
        break;
      case 'typing':
        // No response needed for typing indicators
        break;
      case 'join_conversation':
        this.conversationId = payload.conversation_id;
        break;
      case 'leave_conversation':
        if (this.conversationId === payload.conversation_id) {
          this.conversationId = null;
        }
        break;
      case 'feedback':
        // Acknowledge feedback
        this.simulateIncomingMessage({
          type: 'feedback_received',
          payload: {
            message_id: payload.message_id,
            status: 'success'
          }
        });
        break;
      default:
        console.warn('Unhandled mock WebSocket message type:', type);
    }
  }

  /**
   * Send a chat message to the mock WebSocket server
   * @param message Message text
   * @param conversationId Optional conversation ID
   * @param forceAgentType Optional agent type to force
   */
  sendChatMessage(message: string, conversationId?: string, forceAgentType?: string): void {
    this.send('message', {
      message,
      conversation_id: conversationId || this.conversationId,
      force_agent_type: forceAgentType
    });
  }

  /**
   * Send a typing indicator to the mock WebSocket server
   * @param isTyping Whether the user is typing
   */
  sendTypingIndicator(isTyping: boolean): void {
    this.send('typing', {
      is_typing: isTyping,
      conversation_id: this.conversationId
    });
  }

  /**
   * Send feedback for a message
   * @param messageId Message ID
   * @param feedback Feedback (positive or negative)
   * @param comments Optional comments
   */
  sendMessageFeedback(messageId: string, feedback: 'positive' | 'negative', comments?: string): void {
    this.send('feedback', {
      message_id: messageId,
      feedback,
      comments
    });
  }

  /**
   * Add a message listener
   * @param listener Function to call when a message is received
   */
  addMessageListener(listener: (message: WebSocketMessage) => void): void {
    this.messageListeners.push(listener);
  }

  /**
   * Remove a message listener
   * @param listener Function to remove
   */
  removeMessageListener(listener: (message: WebSocketMessage) => void): void {
    this.messageListeners = this.messageListeners.filter(l => l !== listener);
  }

  /**
   * Add a connection status listener
   * @param listener Function to call when connection status changes
   */
  addConnectionListener(listener: (status: 'connected' | 'disconnected' | 'reconnecting') => void): void {
    this.connectionListeners.push(listener);
  }

  /**
   * Remove a connection status listener
   * @param listener Function to remove
   */
  removeConnectionListener(listener: (status: 'connected' | 'disconnected' | 'reconnecting') => void): void {
    this.connectionListeners = this.connectionListeners.filter(l => l !== listener);
  }

  /**
   * Join a conversation
   * @param conversationId Conversation ID to join
   */
  joinConversation(conversationId: string): void {
    this.conversationId = conversationId;
    this.send('join_conversation', { conversation_id: conversationId });
  }

  /**
   * Leave the current conversation
   */
  leaveConversation(): void {
    if (this.conversationId) {
      this.send('leave_conversation', { conversation_id: this.conversationId });
      this.conversationId = null;
    }
  }

  /**
   * Handle a chat message
   * @param payload Message payload
   */
  private handleChatMessage(payload: any): void {
    const { message, conversation_id, force_agent_type } = payload;

    // Determine agent type based on message content or forced type
    const agentType = this.determineAgentType(message, force_agent_type);

    // Simulate typing indicator
    this.simulateIncomingMessage({
      type: 'typing',
      payload: {
        isTyping: true,
        conversationId: conversation_id || this.conversationId,
        agentType
      }
    });

    // Simulate agent response after delay
    setTimeout(() => {
      // Stop typing
      this.simulateIncomingMessage({
        type: 'typing',
        payload: {
          isTyping: false,
          conversationId: conversation_id || this.conversationId,
          agentType
        }
      });

      // Send response
      this.simulateIncomingMessage({
        type: 'message',
        payload: {
          message: this.generateResponse(message, agentType),
          conversationId: conversation_id || this.conversationId
        }
      });
    }, 1500 + Math.random() * 1000);
  }

  /**
   * Determine agent type based on message content
   * @param message Message text
   * @param forceAgentType Optional agent type to force
   * @returns Agent type
   */
  private determineAgentType(message: string, forceAgentType?: string): AgentType {
    if (forceAgentType) {
      return forceAgentType as AgentType;
    }

    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('manual') ||
        lowerMessage.includes('document') ||
        lowerMessage.includes('information') ||
        lowerMessage.includes('guide')) {
      return 'documentation';
    } else if (lowerMessage.includes('problem') ||
               lowerMessage.includes('issue') ||
               lowerMessage.includes('troubleshoot') ||
               lowerMessage.includes('error') ||
               lowerMessage.includes('not working')) {
      return 'troubleshooting';
    } else if (lowerMessage.includes('procedure') ||
               lowerMessage.includes('maintenance') ||
               lowerMessage.includes('repair') ||
               lowerMessage.includes('replace') ||
               lowerMessage.includes('install')) {
      return 'maintenance';
    }

    // Default to documentation
    return 'documentation';
  }

  /**
   * Generate a response based on agent type
   * @param message Original message
   * @param agentType Agent type
   * @returns Response message
   */
  private generateResponse(message: string, agentType: AgentType): Message {
    this.messageCounter++;
    let content = '';
    let confidence = 0;

    switch (agentType) {
      case 'documentation':
        content = DOCUMENTATION_RESPONSES[this.messageCounter % DOCUMENTATION_RESPONSES.length];
        confidence = 0.85 + Math.random() * 0.1;
        break;
      case 'troubleshooting':
        content = TROUBLESHOOTING_RESPONSES[this.messageCounter % TROUBLESHOOTING_RESPONSES.length];
        confidence = 0.75 + Math.random() * 0.15;
        break;
      case 'maintenance':
        content = MAINTENANCE_RESPONSES[this.messageCounter % MAINTENANCE_RESPONSES.length];
        confidence = 0.9 + Math.random() * 0.08;
        break;
      default:
        content = "I'm not sure how to help with that. Could you provide more details?";
        confidence = 0.6 + Math.random() * 0.1;
    }

    return {
      id: `mock-${Date.now()}-${this.messageCounter}-${Math.random().toString(36).substring(2, 9)}`,
      content,
      role: 'assistant',
      timestamp: new Date().toISOString(),
      agentType,
      confidence
    };
  }

  /**
   * Simulate an incoming message
   * @param message WebSocket message
   */
  private simulateIncomingMessage(message: WebSocketMessage): void {
    this.notifyMessageListeners(message);
  }

  /**
   * Notify all message listeners of a new message
   * @param message WebSocket message
   */
  private notifyMessageListeners(message: WebSocketMessage): void {
    this.messageListeners.forEach(listener => {
      try {
        listener(message);
      } catch (error) {
        console.error('Error in mock message listener:', error);
      }
    });
  }

  /**
   * Notify all connection listeners of a connection status change
   * @param status Connection status
   */
  private notifyConnectionListeners(status: 'connected' | 'disconnected' | 'reconnecting'): void {
    this.connectionListeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in mock connection listener:', error);
      }
    });
  }
}

// Create a singleton instance
export const mockWebsocketService = new MockWebSocketService();

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined';

// Lazy import to avoid circular dependencies and server-side issues
let websocketServiceInstance: any = null;

// Export a factory function to get the appropriate service based on environment
export const getWebSocketService = () => {
  // Return mock service in non-browser environments
  if (!isBrowser) {
    return mockWebsocketService;
  }

  // Use mock service if configured or in development
  if (API_CONFIG.USE_MOCK_WEBSOCKET) {
    console.log('Using mock WebSocket service');
    return mockWebsocketService;
  }

  // Lazy load the real websocket service to avoid circular dependencies
  if (!websocketServiceInstance) {
    // Dynamic import only on client side
    const { websocketService } = require('./websocketService');
    websocketServiceInstance = websocketService;
  }

  // Use real service in production
  return websocketServiceInstance;
};

export default getWebSocketService;
