/**
 * Conversation Service for MAGPIE Platform
 * 
 * This service provides functionality for managing conversations and messages.
 */

import { api } from './api';
import { Message, Conversation } from '../types/api';
import analyticsService from './analyticsService';
import cacheService from './cacheService';

// Cache keys
const CONVERSATIONS_CACHE_KEY = 'conversations';
const CONVERSATION_CACHE_PREFIX = 'conversation_';

/**
 * Get all conversations
 * @returns Conversations
 */
export async function getConversations(): Promise<Conversation[]> {
  try {
    // Try to get from cache first
    const cachedConversations = cacheService.get<Conversation[]>(CONVERSATIONS_CACHE_KEY);
    if (cachedConversations) {
      return cachedConversations;
    }

    // Get from API
    const conversations = await api.chat.getConversations();

    // Cache conversations
    cacheService.set(CONVERSATIONS_CACHE_KEY, conversations, 5 * 60 * 1000); // 5 minutes

    return conversations;
  } catch (error) {
    console.error('Error getting conversations:', error);
    throw error;
  }
}

/**
 * Get conversation by ID
 * @param id Conversation ID
 * @returns Conversation
 */
export async function getConversation(id: string): Promise<Conversation> {
  try {
    // Try to get from cache first
    const cacheKey = `${CONVERSATION_CACHE_PREFIX}${id}`;
    const cachedConversation = cacheService.get<Conversation>(cacheKey);
    if (cachedConversation) {
      return cachedConversation;
    }

    // Get from API
    const conversation = await api.chat.getConversation(id);

    // Cache conversation
    cacheService.set(cacheKey, conversation, 5 * 60 * 1000); // 5 minutes

    // Track conversation view
    analyticsService.trackEvent('conversation_view', { conversationId: id });

    return conversation;
  } catch (error) {
    console.error(`Error getting conversation ${id}:`, error);
    throw error;
  }
}

/**
 * Create a new conversation
 * @param title Conversation title
 * @returns New conversation
 */
export async function createConversation(title?: string): Promise<Conversation> {
  try {
    // Create conversation
    const conversation = await api.chat.createConversation(title);

    // Invalidate conversations cache
    cacheService.remove(CONVERSATIONS_CACHE_KEY);

    // Track conversation creation
    analyticsService.trackEvent('conversation_create', { 
      conversationId: conversation.id,
      title: conversation.title
    });

    return conversation;
  } catch (error) {
    console.error('Error creating conversation:', error);
    throw error;
  }
}

/**
 * Update conversation
 * @param id Conversation ID
 * @param title New title
 * @returns Updated conversation
 */
export async function updateConversation(id: string, title: string): Promise<Conversation> {
  try {
    // Update conversation
    const conversation = await api.chat.updateConversation(id, title);

    // Invalidate caches
    cacheService.remove(CONVERSATIONS_CACHE_KEY);
    cacheService.remove(`${CONVERSATION_CACHE_PREFIX}${id}`);

    // Track conversation update
    analyticsService.trackEvent('conversation_update', { 
      conversationId: id,
      title
    });

    return conversation;
  } catch (error) {
    console.error(`Error updating conversation ${id}:`, error);
    throw error;
  }
}

/**
 * Delete conversation
 * @param id Conversation ID
 */
export async function deleteConversation(id: string): Promise<void> {
  try {
    // Delete conversation
    await api.chat.deleteConversation(id);

    // Invalidate caches
    cacheService.remove(CONVERSATIONS_CACHE_KEY);
    cacheService.remove(`${CONVERSATION_CACHE_PREFIX}${id}`);

    // Track conversation deletion
    analyticsService.trackEvent('conversation_delete', { conversationId: id });
  } catch (error) {
    console.error(`Error deleting conversation ${id}:`, error);
    throw error;
  }
}

/**
 * Send message
 * @param message Message text
 * @param conversationId Conversation ID
 * @returns Message response
 */
export async function sendMessage(message: string, conversationId?: string): Promise<any> {
  try {
    // Track message sent
    analyticsService.trackEvent('message_sent', { 
      conversationId,
      messageLength: message.length
    });

    // Send message
    const response = await api.chat.sendMessage(message, conversationId);

    // Invalidate conversation cache
    if (conversationId) {
      cacheService.remove(`${CONVERSATION_CACHE_PREFIX}${conversationId}`);
    }

    return response;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

/**
 * Generate a default conversation title based on first message
 * @param message First message
 * @returns Generated title
 */
export function generateConversationTitle(message: string): string {
  // Truncate message if too long
  const truncatedMessage = message.length > 30
    ? `${message.substring(0, 27)}...`
    : message;

  // Generate title with timestamp
  const timestamp = new Date().toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
  });

  return `${truncatedMessage} - ${timestamp}`;
}

// Export conversation service
const conversationService = {
  getAll: getConversations,
  get: getConversation,
  create: createConversation,
  update: updateConversation,
  delete: deleteConversation,
  sendMessage,
  generateTitle: generateConversationTitle
};

export default conversationService;
