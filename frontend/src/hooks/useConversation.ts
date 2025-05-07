/**
 * Custom hook for managing conversations
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  conversationService,
  orchestratorService,
  analyticsService
} from '../services';
import { useNotifications } from './useNotifications';
import {
  Message,
  Conversation,
  ApiError,
  AgentType,
  WebSocketMessage
} from '../types/api';

interface UseConversationOptions {
  initialConversationId?: string;
  userId: string;
  onError?: (error: ApiError) => void;
}

export function useConversation(options: UseConversationOptions) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingQuery, setIsLoadingQuery] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(options.initialConversationId || null);

  // Get notifications hook
  const notifications = useNotifications();

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'message':
        if (message.payload.message) {
          // Add the message to the current conversation
          setMessages(prev => [...prev, message.payload.message]);

          // Track message received
          analyticsService.trackEvent('message_received', {
            conversationId: message.payload.conversationId,
            messageId: message.payload.message.id,
            agentType: message.payload.message.agentType
          });
        }
        break;
      case 'typing':
        setIsTyping(message.payload.isTyping);
        break;
      case 'error':
        if (message.payload.error) {
          setError(message.payload.error);

          // Show error notification
          notifications.showError(
            'Error',
            message.payload.error.message || 'An error occurred'
          );

          if (options.onError) {
            options.onError(message.payload.error);
          }
        }
        break;
      case 'agent_change':
        // This will be handled by the orchestrator context
        // But we can show a notification
        if (message.payload.fromAgent && message.payload.toAgent) {
          notifications.showInfo(
            'Agent Changed',
            `Switched from ${message.payload.fromAgent} to ${message.payload.toAgent}`
          );
        }
        break;
    }
  }, [options, notifications]);

  // Track previous connection status to prevent duplicate notifications
  const prevConnectionStatusRef = useRef<'connected' | 'disconnected' | 'reconnecting' | null>(null);

  // Track if we've already shown a connection notification
  const hasShownConnectionNotificationRef = useRef<boolean>(false);

  // Handle WebSocket connection status changes
  const handleConnectionStatus = useCallback((status: 'connected' | 'disconnected' | 'reconnecting') => {
    console.log('WebSocket connection status:', status);

    // Skip if status hasn't changed
    if (prevConnectionStatusRef.current === status) {
      console.log('Skipping duplicate connection status:', status);
      return;
    }

    // Update previous status
    prevConnectionStatusRef.current = status;

    // If disconnected, show error
    if (status === 'disconnected') {
      setError({
        status: 0,
        message: 'Lost connection to server. Please check your internet connection.'
      });

      // Show error notification
      notifications.showError(
        'Connection Lost',
        'Lost connection to server. Please check your internet connection.',
        { autoClose: false }
      );
    }

    // If reconnecting, clear error
    if (status === 'reconnecting') {
      setError(null);

      // Show info notification
      notifications.showInfo(
        'Reconnecting',
        'Attempting to reconnect to server...'
      );
    }

    // If connected, clear error
    if (status === 'connected') {
      setError(null);

      // Join conversation if available
      if (conversationId) {
        orchestratorService.joinConversation(conversationId);
      }

      // Only show the connection notification once per session
      if (!hasShownConnectionNotificationRef.current) {
        // Show success notification
        notifications.showSuccess(
          'Connected',
          'Successfully connected to server'
        );

        // Mark that we've shown the notification
        hasShownConnectionNotificationRef.current = true;
      }
    }
  }, [conversationId, notifications]);

  // Connect to WebSocket on mount
  useEffect(() => {
    if (options.userId) {
      // Add message listener
      const removeMessageListener = orchestratorService.addMessageListener(handleWebSocketMessage);

      // Add connection listener
      const removeConnectionListener = orchestratorService.addConnectionListener(handleConnectionStatus);

      // Connect to WebSocket
      orchestratorService.connectWebSocket(options.userId, options.initialConversationId);

      // Load conversation if provided
      if (options.initialConversationId) {
        loadConversation(options.initialConversationId);
      }

      // Cleanup on unmount
      return () => {
        removeMessageListener();
        removeConnectionListener();
      };
    }
  }, [
    options.userId,
    options.initialConversationId,
    handleWebSocketMessage,
    handleConnectionStatus
  ]);

  // Fetch all conversations
  const fetchConversations = useCallback(async () => {
    setIsLoadingConversations(true);
    setError(null);

    try {
      const response = await conversationService.getAll();
      setConversations(response);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Show error notification
      notifications.showError(
        'Error Loading Conversations',
        apiError.message || 'Failed to load conversations'
      );

      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoadingConversations(false);
    }
  }, [options, notifications]);

  // Load a specific conversation
  const loadConversation = useCallback(async (conversationId: string) => {
    setIsLoadingConversations(true);
    setError(null);

    try {
      const conversation = await conversationService.get(conversationId);
      setCurrentConversation(conversation);
      setMessages(conversation.messages);
      setConversationId(conversationId);

      // Join the conversation in WebSocket
      orchestratorService.joinConversation(conversationId);

      // Track conversation loaded
      analyticsService.trackEvent('conversation_load', { conversationId });

      return conversation;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Show error notification
      notifications.showError(
        'Error Loading Conversation',
        apiError.message || `Failed to load conversation ${conversationId}`
      );

      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoadingConversations(false);
    }
  }, [options, notifications]);

  // Create a new conversation
  const createConversation = useCallback(async (title?: string) => {
    setIsLoadingConversations(true);
    setError(null);

    try {
      const conversation = await conversationService.create(title);
      setCurrentConversation(conversation);
      setMessages([]);
      setConversationId(conversation.id);

      // Update conversations list
      setConversations(prev => [conversation, ...prev]);

      // Join the conversation in WebSocket
      orchestratorService.joinConversation(conversation.id);

      // Track conversation created
      analyticsService.trackEvent('conversation_create', {
        conversationId: conversation.id,
        title: conversation.title
      });

      // Show success notification
      notifications.showSuccess(
        'Conversation Created',
        'New conversation started'
      );

      return conversation;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Show error notification
      notifications.showError(
        'Error Creating Conversation',
        apiError.message || 'Failed to create new conversation'
      );

      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoadingConversations(false);
    }
  }, [options, notifications]);

  // Send a message in the current conversation
  const sendMessage = useCallback(async (
    message: string,
    forceAgentType?: AgentType
  ) => {
    setError(null);
    setIsLoadingQuery(true);

    try {
      // Add user message to the UI immediately
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        content: message,
        role: 'user',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMessage]);

      // Send typing indicator
      orchestratorService.sendTypingIndicator(true);

      // Track message sent
      analyticsService.trackEvent('message_sent', {
        conversationId,
        messageLength: message.length,
        hasForceAgentType: !!forceAgentType
      });

      // If no conversation ID yet, create one
      if (!conversationId) {
        try {
          // Generate title from first message
          const title = conversationService.generateTitle(message);

          // Create conversation
          const conversation = await conversationService.create(title);
          setConversationId(conversation.id);
          setCurrentConversation(conversation);

          // Join the conversation in WebSocket
          orchestratorService.joinConversation(conversation.id);

          // Send the message via WebSocket
          orchestratorService.sendChatMessage(
            message,
            conversation.id,
            forceAgentType
          );
        } catch (err) {
          console.error('Error creating conversation:', err);

          // Show error notification
          notifications.showError(
            'Error Creating Conversation',
            'Failed to create new conversation, but your message will still be processed'
          );

          // Continue anyway, send message without conversation ID
          orchestratorService.sendChatMessage(message, undefined, forceAgentType);
        }
      } else {
        // Send the message via WebSocket with existing conversation ID
        orchestratorService.sendChatMessage(message, conversationId, forceAgentType);
      }

      return userMessage;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Show error notification
      notifications.showError(
        'Error Sending Message',
        apiError.message || 'Failed to send message'
      );

      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoadingQuery(false);
      orchestratorService.sendTypingIndicator(false);
    }
  }, [options, conversationId, notifications]);

  // Delete a conversation
  const deleteConversation = useCallback(async (conversationId: string) => {
    setError(null);

    try {
      await conversationService.delete(conversationId);

      // Remove from conversations list
      setConversations(prev => prev.filter(c => c.id !== conversationId));

      // Clear current conversation if it's the one being deleted
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
        setConversationId(null);
      }

      // Track conversation deleted
      analyticsService.trackEvent('conversation_delete', { conversationId });

      // Show success notification
      notifications.showSuccess(
        'Conversation Deleted',
        'The conversation has been deleted'
      );
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Show error notification
      notifications.showError(
        'Error Deleting Conversation',
        apiError.message || `Failed to delete conversation ${conversationId}`
      );

      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    }
  }, [currentConversation, options, notifications]);

  // Send message feedback
  const sendMessageFeedback = useCallback((
    messageId: string,
    feedback: 'positive' | 'negative',
    comments?: string
  ) => {
    // Send feedback via WebSocket
    orchestratorService.sendMessageFeedback(messageId, feedback, comments);

    // Track feedback event
    analyticsService.trackEvent('message_feedback', {
      messageId,
      feedback,
      hasComments: !!comments,
      conversationId
    });

    // Show success notification
    notifications.showSuccess(
      'Feedback Submitted',
      'Thank you for your feedback'
    );
  }, [notifications, conversationId]);

  return {
    // State
    conversations,
    currentConversation,
    messages,
    isTyping,
    isLoadingConversations,
    isLoadingQuery,
    error,
    conversationId,

    // Conversation methods
    fetchConversations,
    loadConversation,
    createConversation,
    deleteConversation,

    // Message methods
    sendMessage,
    sendMessageFeedback,

    // Utility methods
    clearError: () => setError(null),
    clearMessages: () => setMessages([]),
    updateConversationTitle: async (id: string, title: string) => {
      try {
        const updated = await conversationService.update(id, title);

        // Update conversations list
        setConversations(prev =>
          prev.map(c => c.id === id ? updated : c)
        );

        // Update current conversation if it's the one being updated
        if (currentConversation?.id === id) {
          setCurrentConversation(updated);
        }

        // Show success notification
        notifications.showSuccess(
          'Conversation Updated',
          'The conversation title has been updated'
        );

        return updated;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);

        // Show error notification
        notifications.showError(
          'Error Updating Conversation',
          apiError.message || `Failed to update conversation ${id}`
        );

        if (options.onError) {
          options.onError(apiError);
        }
        throw apiError;
      }
    }
  };
}
