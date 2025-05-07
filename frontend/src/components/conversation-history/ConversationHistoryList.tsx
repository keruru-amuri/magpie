'use client';

import React, { useState } from 'react';
import { format } from 'date-fns';
import { useConversationHistory } from '../../contexts/ConversationHistoryContext';
import { ConversationListItem } from '../../services/conversationHistoryService';
import AgentIndicator from '../orchestrator/AgentIndicator';
import LoadingSpinner from '../common/LoadingSpinner';

interface ConversationHistoryListProps {
  onSelectConversation?: (id: string) => void;
  className?: string;
}

export default function ConversationHistoryList({
  onSelectConversation,
  className = '',
}: ConversationHistoryListProps) {
  const { 
    conversationList, 
    currentConversation, 
    loadConversation, 
    deleteConversation,
    searchConversations,
    isLoading
  } = useConversationHistory();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  
  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  // Handle search submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
    
    // Reset searching state after a short delay
    setTimeout(() => {
      setIsSearching(false);
    }, 300);
  };
  
  // Get filtered conversations
  const filteredConversations = searchQuery.trim() 
    ? searchConversations(searchQuery) 
    : conversationList;
  
  // Handle conversation selection
  const handleSelectConversation = (id: string) => {
    loadConversation(id);
    
    if (onSelectConversation) {
      onSelectConversation(id);
    }
  };
  
  // Handle conversation deletion
  const handleDeleteConversation = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      deleteConversation(id);
    }
  };
  
  // Format date for display
  const formatConversationDate = (date: Date) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const conversationDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    // If conversation is from today, show time
    if (conversationDate.getTime() === today.getTime()) {
      return `Today at ${format(date, 'h:mm a')}`;
    }
    
    // If conversation is from yesterday, show "Yesterday"
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (conversationDate.getTime() === yesterday.getTime()) {
      return `Yesterday at ${format(date, 'h:mm a')}`;
    }
    
    // Otherwise, show date
    return format(date, 'MMM d, yyyy');
  };
  
  // Render agent indicators
  const renderAgentIndicators = (agentTypes: ('documentation' | 'troubleshooting' | 'maintenance')[]) => {
    return (
      <div className="flex -space-x-2">
        {agentTypes.map((type) => (
          <AgentIndicator
            key={type}
            agentType={type}
            showLabel={false}
            size="xs"
            className="border-2 border-white dark:border-gray-800 rounded-full"
          />
        ))}
      </div>
    );
  };
  
  // Render conversation item
  const renderConversationItem = (conversation: ConversationListItem) => {
    const isActive = currentConversation?.id === conversation.id;
    
    return (
      <div
        key={conversation.id}
        onClick={() => handleSelectConversation(conversation.id)}
        className={`p-3 border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors ${
          isActive 
            ? 'bg-blue-50 dark:bg-blue-900/20' 
            : 'hover:bg-gray-50 dark:hover:bg-gray-800'
        }`}
      >
        <div className="flex justify-between items-start">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {conversation.title}
            </h3>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
              {conversation.snippet}
            </p>
          </div>
          
          <button
            onClick={(e) => handleDeleteConversation(e, conversation.id)}
            className="ml-2 p-1 text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Delete conversation"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        
        <div className="mt-2 flex justify-between items-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {formatConversationDate(conversation.updatedAt)}
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {conversation.messageCount} message{conversation.messageCount !== 1 ? 's' : ''}
            </span>
            
            {conversation.agentTypes.length > 0 && renderAgentIndicators(conversation.agentTypes)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Conversation History
        </h2>
        
        <form onSubmit={handleSearchSubmit} className="mt-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={handleSearch}
              className="w-full px-3 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-800 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </form>
      </div>
      
      <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[500px] overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center">
            <LoadingSpinner size="md" />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Loading conversations...
            </p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-4 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              {searchQuery 
                ? 'No conversations match your search' 
                : 'No conversations yet'}
            </p>
          </div>
        ) : (
          <>
            {isSearching ? (
              <div className="p-4 text-center">
                <LoadingSpinner size="sm" />
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Searching...
                </p>
              </div>
            ) : (
              filteredConversations.map(renderConversationItem)
            )}
          </>
        )}
      </div>
    </div>
  );
}
