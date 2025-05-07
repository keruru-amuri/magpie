'use client';

import React, { useRef, useEffect } from 'react';
import { useConversationHistory } from '../../contexts/ConversationHistoryContext';
import Message from '../visualizations/shared/Message';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';

interface ConversationDetailProps {
  conversationId?: string;
  onContinueConversation?: () => void;
  className?: string;
}

export default function ConversationDetail({
  conversationId,
  onContinueConversation,
  className = '',
}: ConversationDetailProps) {
  const { currentConversation, loadConversation, isLoading } = useConversationHistory();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Load conversation if ID is provided and different from current
  useEffect(() => {
    if (conversationId && (!currentConversation || currentConversation.id !== conversationId)) {
      loadConversation(conversationId);
    }
  }, [conversationId, currentConversation, loadConversation]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentConversation?.messages]);
  
  // Handle continue conversation
  const handleContinue = () => {
    if (onContinueConversation) {
      onContinueConversation();
    }
  };
  
  // If loading, show spinner
  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-500 dark:text-gray-400">
          Loading conversation...
        </p>
      </div>
    );
  }
  
  // If no conversation selected, show empty state
  if (!currentConversation) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
        <svg className="h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
          No conversation selected
        </h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Select a conversation from the history or start a new one.
        </p>
      </div>
    );
  }
  
  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Conversation header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
            {currentConversation.title}
          </h2>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="primary"
              size="sm"
              onClick={handleContinue}
              className="flex items-center"
            >
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m-8 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Continue Conversation
            </Button>
          </div>
        </div>
        
        <div className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
          <span>
            {currentConversation.messages.length} message{currentConversation.messages.length !== 1 ? 's' : ''}
          </span>
          <span className="mx-2">•</span>
          <span>
            Created {new Date(currentConversation.createdAt).toLocaleDateString()}
          </span>
          {currentConversation.updatedAt !== currentConversation.createdAt && (
            <>
              <span className="mx-2">•</span>
              <span>
                Updated {new Date(currentConversation.updatedAt).toLocaleDateString()}
              </span>
            </>
          )}
        </div>
      </div>
      
      {/* Conversation messages */}
      <div className="flex-1 p-4 overflow-y-auto bg-gray-50 dark:bg-gray-900">
        {currentConversation.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-gray-500 dark:text-gray-400">
              This conversation has no messages.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {currentConversation.messages.map((message) => (
              <Message
                key={message.id}
                id={message.id}
                source={message.source}
                agentType={message.agentType}
                timestamp={new Date(message.timestamp)}
                contents={message.contents}
                metadata={message.metadata}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
