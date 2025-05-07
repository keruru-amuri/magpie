'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ConversationHistoryProvider, useConversationHistory } from '../../contexts/ConversationHistoryContext';
import ConversationHistoryList from '../../components/conversation-history/ConversationHistoryList';
import ConversationDetail from '../../components/conversation-history/ConversationDetail';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import Button from '../../components/common/Button';

function HistoryPageContent() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const { currentConversation } = useConversationHistory();
  const router = useRouter();
  
  // Handle conversation selection
  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
  };
  
  // Handle continue conversation
  const handleContinueConversation = () => {
    if (currentConversation) {
      router.push(`/chat?conversation=${currentConversation.id}`);
    }
  };
  
  // Handle new conversation
  const handleNewConversation = () => {
    router.push('/chat');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Conversation History
        </h1>
        
        <Button
          variant="primary"
          onClick={handleNewConversation}
          className="flex items-center"
        >
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          New Conversation
        </Button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <ConversationHistoryList
            onSelectConversation={handleSelectConversation}
            className="h-full"
          />
        </div>
        
        <div className="lg:col-span-2">
          <ConversationDetail
            conversationId={selectedConversationId || undefined}
            onContinueConversation={handleContinueConversation}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
}

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <ConversationHistoryProvider>
        <HistoryPageContent />
      </ConversationHistoryProvider>
    </ProtectedRoute>
  );
}
