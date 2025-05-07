'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  conversationHistoryService, 
  Conversation, 
  ConversationListItem, 
  ConversationMessage 
} from '../services/conversationHistoryService';
import { useAnalytics } from '../hooks/useAnalytics';

interface ConversationHistoryContextType {
  currentConversation: Conversation | null;
  conversationList: ConversationListItem[];
  isLoading: boolean;
  createConversation: (title: string, initialMessage?: ConversationMessage) => Conversation;
  loadConversation: (id: string) => Conversation | null;
  addMessage: (message: ConversationMessage) => Conversation | null;
  deleteConversation: (id: string) => boolean;
  searchConversations: (query: string) => ConversationListItem[];
  clearCurrentConversation: () => void;
}

const ConversationHistoryContext = createContext<ConversationHistoryContextType | undefined>(undefined);

export function ConversationHistoryProvider({ children }: { children: ReactNode }) {
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [conversationList, setConversationList] = useState<ConversationListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const analytics = useAnalytics();

  // Load conversation list and current conversation on mount
  useEffect(() => {
    const loadData = () => {
      setIsLoading(true);
      
      try {
        // Load conversation list
        const list = conversationHistoryService.getConversationList();
        setConversationList(list);
        
        // Load current conversation if exists
        const current = conversationHistoryService.getCurrentConversation();
        setCurrentConversation(current);
      } catch (error) {
        console.error('Error loading conversation data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Create a new conversation
  const createConversation = (title: string, initialMessage?: ConversationMessage) => {
    const newConversation = conversationHistoryService.createConversation(title, initialMessage);
    
    // Update state
    setCurrentConversation(newConversation);
    setConversationList(conversationHistoryService.getConversationList());
    
    // Track analytics
    analytics.trackEvent('conversation_created', { 
      conversationId: newConversation.id,
      title
    });
    
    return newConversation;
  };

  // Load a conversation by ID
  const loadConversation = (id: string) => {
    const conversation = conversationHistoryService.getConversation(id);
    
    if (conversation) {
      // Set as current conversation
      conversationHistoryService.setCurrentConversation(id);
      setCurrentConversation(conversation);
      
      // Track analytics
      analytics.trackEvent('conversation_loaded', { 
        conversationId: id,
        messageCount: conversation.messages.length
      });
    }
    
    return conversation;
  };

  // Add a message to the current conversation
  const addMessage = (message: ConversationMessage) => {
    if (!currentConversation) return null;
    
    const updatedConversation = conversationHistoryService.addMessage(
      currentConversation.id, 
      message
    );
    
    if (updatedConversation) {
      // Update state
      setCurrentConversation(updatedConversation);
      setConversationList(conversationHistoryService.getConversationList());
      
      // Track analytics
      analytics.trackEvent('message_added', { 
        conversationId: currentConversation.id,
        messageSource: message.source,
        agentType: message.agentType || 'none'
      });
    }
    
    return updatedConversation;
  };

  // Delete a conversation
  const deleteConversation = (id: string) => {
    const success = conversationHistoryService.deleteConversation(id);
    
    if (success) {
      // Update state
      if (currentConversation?.id === id) {
        setCurrentConversation(null);
      }
      
      setConversationList(conversationHistoryService.getConversationList());
      
      // Track analytics
      analytics.trackEvent('conversation_deleted', { conversationId: id });
    }
    
    return success;
  };

  // Search conversations
  const searchConversations = (query: string) => {
    return conversationHistoryService.searchConversations(query);
  };

  // Clear current conversation
  const clearCurrentConversation = () => {
    conversationHistoryService.clearCurrentConversation();
    setCurrentConversation(null);
  };

  const value = {
    currentConversation,
    conversationList,
    isLoading,
    createConversation,
    loadConversation,
    addMessage,
    deleteConversation,
    searchConversations,
    clearCurrentConversation
  };

  return (
    <ConversationHistoryContext.Provider value={value}>
      {children}
    </ConversationHistoryContext.Provider>
  );
}

export function useConversationHistory() {
  const context = useContext(ConversationHistoryContext);
  
  if (context === undefined) {
    throw new Error('useConversationHistory must be used within a ConversationHistoryProvider');
  }
  
  return context;
}
