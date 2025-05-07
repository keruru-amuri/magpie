/**
 * WebSocket Service for MAGPIE Platform
 *
 * This service handles real-time communication with the backend via WebSockets.
 */

import { WebSocketMessage } from '../types/api';

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined';

// WebSocket base URL - safely constructed to work in both server and client environments
const getWsBaseUrl = () => {
  if (!isBrowser) {
    // Default for server-side rendering
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  }

  // Client-side with access to window
  return process.env.NEXT_PUBLIC_WS_URL ||
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
    (process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000') +
    '/ws';
};

export class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageListeners: ((message: WebSocketMessage) => void)[] = [];
  private connectionListeners: ((status: 'connected' | 'disconnected' | 'reconnecting') => void)[] = [];
  private userId: string | null = null;
  private conversationId: string | null = null;

  /**
   * Connect to the WebSocket server
   * @param userId User ID for authentication
   * @param conversationId Optional conversation ID to join
   */
  connect(userId: string, conversationId?: string): void {
    // Check if we're in a browser environment
    if (!isBrowser) {
      console.warn('WebSocket connection attempted in non-browser environment');
      return;
    }

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.userId = userId;
    this.conversationId = conversationId || null;

    // Build the WebSocket URL with query parameters
    let wsUrl = `${getWsBaseUrl()}?user_id=${userId}`;
    if (conversationId) {
      wsUrl += `&conversation_id=${conversationId}`;
    }

    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      wsUrl += `&token=${token}`;
    }

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.notifyConnectionListeners('disconnected');
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.reconnectAttempts = 0;
    this.userId = null;
    this.conversationId = null;
  }

  /**
   * Send a message to the WebSocket server
   * @param type Message type
   * @param payload Message payload
   */
  send(type: string, payload: any): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    const message = {
      type,
      payload,
    };

    this.socket.send(JSON.stringify(message));
  }

  /**
   * Send a chat message to the WebSocket server
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
   * Send a typing indicator to the WebSocket server
   * @param isTyping Whether the user is typing
   */
  sendTypingIndicator(isTyping: boolean): void {
    if (this.conversationId) {
      this.send('typing', {
        is_typing: isTyping,
        conversation_id: this.conversationId
      });
    }
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

    if (this.socket && this.socket.readyState === WebSocket.OPEN && this.userId) {
      this.send('join_conversation', { conversation_id: conversationId });
    } else if (this.userId) {
      // Reconnect with the new conversation ID
      this.connect(this.userId, conversationId);
    }
  }

  /**
   * Leave the current conversation
   */
  leaveConversation(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN && this.conversationId) {
      this.send('leave_conversation', { conversation_id: this.conversationId });
      this.conversationId = null;
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
    this.notifyConnectionListeners('connected');
  }

  /**
   * Handle WebSocket message event
   * @param event WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;
      this.notifyMessageListeners(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(): void {
    console.log('WebSocket disconnected');
    this.notifyConnectionListeners('disconnected');
    this.attemptReconnect();
  }

  /**
   * Handle WebSocket error event
   * @param error WebSocket error event
   */
  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.notifyConnectionListeners('disconnected');
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.userId) {
      console.log('Max reconnect attempts reached or missing user ID');
      return;
    }

    this.notifyConnectionListeners('reconnecting');

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId, this.conversationId || undefined);
      }
    }, delay);
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
        console.error('Error in message listener:', error);
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
        console.error('Error in connection listener:', error);
      }
    });
  }
}

// Create a singleton instance
export const websocketService = new WebSocketService();

export default websocketService;
