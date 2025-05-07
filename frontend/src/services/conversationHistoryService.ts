import { MessageContent, MessageSource } from '../components/visualizations/shared/Message';

// Define conversation message structure
export interface ConversationMessage {
  id: string;
  source: MessageSource;
  agentType?: 'documentation' | 'troubleshooting' | 'maintenance' | null;
  timestamp: Date;
  contents: MessageContent[];
  metadata?: Record<string, any>;
}

// Define conversation structure
export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ConversationMessage[];
  agentTypes: ('documentation' | 'troubleshooting' | 'maintenance')[];
  metadata?: Record<string, any>;
}

// Define conversation list item (for displaying in history)
export interface ConversationListItem {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  agentTypes: ('documentation' | 'troubleshooting' | 'maintenance')[];
  snippet: string;
}

// Local storage keys
const CONVERSATIONS_KEY = 'magpie_conversations';
const CURRENT_CONVERSATION_KEY = 'magpie_current_conversation';

/**
 * Service for managing conversation history
 */
class ConversationHistoryService {
  /**
   * Get all conversations from local storage
   */
  getAllConversations(): Conversation[] {
    try {
      const conversationsJson = localStorage.getItem(CONVERSATIONS_KEY);
      if (!conversationsJson) return [];

      const conversations = JSON.parse(conversationsJson) as Conversation[];
      
      // Convert string dates to Date objects
      return conversations.map(conversation => ({
        ...conversation,
        createdAt: new Date(conversation.createdAt),
        updatedAt: new Date(conversation.updatedAt),
        messages: conversation.messages.map(message => ({
          ...message,
          timestamp: new Date(message.timestamp)
        }))
      }));
    } catch (error) {
      console.error('Error getting conversations:', error);
      return [];
    }
  }

  /**
   * Get conversation list items for display in history
   */
  getConversationList(): ConversationListItem[] {
    const conversations = this.getAllConversations();
    
    return conversations.map(conversation => {
      // Get the first message content as snippet
      const firstMessage = conversation.messages[0];
      const firstTextContent = firstMessage?.contents.find(c => c.type === 'text');
      const snippet = firstTextContent 
        ? this.truncateText(firstTextContent.content, 100) 
        : 'No content';

      return {
        id: conversation.id,
        title: conversation.title,
        createdAt: conversation.createdAt,
        updatedAt: conversation.updatedAt,
        messageCount: conversation.messages.length,
        agentTypes: conversation.agentTypes,
        snippet
      };
    });
  }

  /**
   * Get a conversation by ID
   */
  getConversation(id: string): Conversation | null {
    const conversations = this.getAllConversations();
    const conversation = conversations.find(c => c.id === id);
    
    if (!conversation) return null;
    
    return conversation;
  }

  /**
   * Create a new conversation
   */
  createConversation(title: string, initialMessage?: ConversationMessage): Conversation {
    const conversations = this.getAllConversations();
    
    const newConversation: Conversation = {
      id: this.generateId(),
      title,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: initialMessage ? [initialMessage] : [],
      agentTypes: []
    };
    
    // Save to local storage
    localStorage.setItem(
      CONVERSATIONS_KEY, 
      JSON.stringify([newConversation, ...conversations])
    );
    
    // Set as current conversation
    this.setCurrentConversation(newConversation.id);
    
    return newConversation;
  }

  /**
   * Add a message to a conversation
   */
  addMessage(conversationId: string, message: ConversationMessage): Conversation | null {
    const conversations = this.getAllConversations();
    const conversationIndex = conversations.findIndex(c => c.id === conversationId);
    
    if (conversationIndex === -1) return null;
    
    // Add message to conversation
    const updatedConversation = {
      ...conversations[conversationIndex],
      updatedAt: new Date(),
      messages: [...conversations[conversationIndex].messages, message]
    };
    
    // Update agent types if needed
    if (message.agentType && !updatedConversation.agentTypes.includes(message.agentType)) {
      updatedConversation.agentTypes = [...updatedConversation.agentTypes, message.agentType];
    }
    
    // Update conversation in list
    conversations[conversationIndex] = updatedConversation;
    
    // Save to local storage
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
    
    return updatedConversation;
  }

  /**
   * Delete a conversation
   */
  deleteConversation(id: string): boolean {
    const conversations = this.getAllConversations();
    const filteredConversations = conversations.filter(c => c.id !== id);
    
    if (filteredConversations.length === conversations.length) {
      return false; // Conversation not found
    }
    
    // Save to local storage
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(filteredConversations));
    
    // If current conversation is deleted, clear it
    const currentId = this.getCurrentConversationId();
    if (currentId === id) {
      this.clearCurrentConversation();
    }
    
    return true;
  }

  /**
   * Set the current conversation
   */
  setCurrentConversation(id: string): void {
    localStorage.setItem(CURRENT_CONVERSATION_KEY, id);
  }

  /**
   * Get the current conversation ID
   */
  getCurrentConversationId(): string | null {
    return localStorage.getItem(CURRENT_CONVERSATION_KEY);
  }

  /**
   * Get the current conversation
   */
  getCurrentConversation(): Conversation | null {
    const id = this.getCurrentConversationId();
    if (!id) return null;
    
    return this.getConversation(id);
  }

  /**
   * Clear the current conversation
   */
  clearCurrentConversation(): void {
    localStorage.removeItem(CURRENT_CONVERSATION_KEY);
  }

  /**
   * Search conversations
   */
  searchConversations(query: string): ConversationListItem[] {
    if (!query.trim()) return this.getConversationList();
    
    const conversations = this.getAllConversations();
    const normalizedQuery = query.toLowerCase();
    
    const matchingConversations = conversations.filter(conversation => {
      // Check title
      if (conversation.title.toLowerCase().includes(normalizedQuery)) {
        return true;
      }
      
      // Check message contents
      return conversation.messages.some(message => 
        message.contents.some(content => 
          content.type === 'text' && 
          content.content.toLowerCase().includes(normalizedQuery)
        )
      );
    });
    
    return matchingConversations.map(conversation => {
      // Get the first matching message content as snippet
      let snippet = '';
      
      // Find first message with matching content
      for (const message of conversation.messages) {
        for (const content of message.contents) {
          if (content.type === 'text' && 
              content.content.toLowerCase().includes(normalizedQuery)) {
            // Get context around the match
            const index = content.content.toLowerCase().indexOf(normalizedQuery);
            const start = Math.max(0, index - 40);
            const end = Math.min(content.content.length, index + normalizedQuery.length + 40);
            snippet = '...' + content.content.substring(start, end) + '...';
            break;
          }
        }
        if (snippet) break;
      }
      
      if (!snippet) {
        // If no matching content found, use first message
        const firstMessage = conversation.messages[0];
        const firstTextContent = firstMessage?.contents.find(c => c.type === 'text');
        snippet = firstTextContent 
          ? this.truncateText(firstTextContent.content, 100) 
          : 'No content';
      }

      return {
        id: conversation.id,
        title: conversation.title,
        createdAt: conversation.createdAt,
        updatedAt: conversation.updatedAt,
        messageCount: conversation.messages.length,
        agentTypes: conversation.agentTypes,
        snippet
      };
    });
  }

  /**
   * Generate a unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  }

  /**
   * Truncate text to a specified length
   */
  private truncateText(text: string, maxLength: number): string {
    // Remove HTML tags
    const plainText = text.replace(/<[^>]*>/g, '');
    
    if (plainText.length <= maxLength) {
      return plainText;
    }
    
    return plainText.substring(0, maxLength) + '...';
  }
}

// Export singleton instance
export const conversationHistoryService = new ConversationHistoryService();
