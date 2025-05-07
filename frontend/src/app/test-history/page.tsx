'use client';

import React, { useEffect, useState } from 'react';
import { ConversationHistoryProvider, useConversationHistory } from '../../contexts/ConversationHistoryContext';
import ConversationHistoryList from '../../components/conversation-history/ConversationHistoryList';
import ConversationDetail from '../../components/conversation-history/ConversationDetail';
import Button from '../../components/common/Button';
import { MessageContent } from '../../components/visualizations/shared/Message';

// Sample message content
const sampleMessageContents: MessageContent[] = [
  {
    type: 'text',
    content: 'How do I perform a 100-hour inspection on a Cessna 172 engine?'
  }
];

const sampleAgentContents: MessageContent[] = [
  {
    type: 'text',
    content: 'I\'ll help you with the 100-hour inspection procedure for a Cessna 172 engine. Here\'s a step-by-step guide:'
  },
  {
    type: 'code',
    language: 'markdown',
    content: `# 100-Hour Inspection Procedure for Cessna 172 Engine

## Required Tools
- Socket wrench set
- Torque wrench
- Inspection mirror
- Flashlight
- Digital multimeter
- Oil filter wrench

## Procedure
1. Prepare the aircraft for inspection
2. Remove engine cowling
3. Inspect engine mounts and vibration isolators
4. Check all fluid levels and condition
5. Inspect ignition system components
6. Check compression on all cylinders
7. Inspect exhaust system for cracks or leaks
8. Check all hoses and lines for condition
9. Inspect air intake system and air filter
10. Check all electrical connections`
  }
];

const sampleCodeContents: MessageContent[] = [
  {
    type: 'text',
    content: 'Here\'s an example of how to use the Aircraft Maintenance API to log your inspection:'
  },
  {
    type: 'code',
    language: 'javascript',
    content: `// Example API call to log maintenance
const logMaintenance = async (aircraftId, procedure) => {
  try {
    const response = await fetch('/api/maintenance/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        aircraftId,
        procedureType: '100-hour-inspection',
        components: ['engine', 'ignition-system', 'fuel-system'],
        technician: currentUser.id,
        notes: 'Completed all required inspection items',
        date: new Date().toISOString()
      }),
    });
    
    const data = await response.json();
    return data.maintenanceLogId;
  } catch (error) {
    console.error('Error logging maintenance:', error);
    throw error;
  }
};`,
    fileName: 'maintenanceLogger.js'
  }
];

function TestHistoryContent() {
  const { 
    createConversation, 
    addMessage, 
    conversationList, 
    currentConversation,
    loadConversation
  } = useConversationHistory();
  
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  
  // Create sample conversations on mount
  useEffect(() => {
    if (conversationList.length === 0) {
      // Create first conversation
      const conv1 = createConversation('Engine Maintenance Procedure');
      
      // Add messages to first conversation
      addMessage({
        id: 'msg1',
        source: 'user',
        timestamp: new Date(Date.now() - 1000 * 60 * 30),
        contents: sampleMessageContents
      });
      
      addMessage({
        id: 'msg2',
        source: 'agent',
        agentType: 'maintenance',
        timestamp: new Date(Date.now() - 1000 * 60 * 29),
        contents: sampleAgentContents
      });
      
      // Create second conversation
      const conv2 = createConversation('API Integration Example');
      
      // Add messages to second conversation
      addMessage({
        id: 'msg3',
        source: 'user',
        timestamp: new Date(Date.now() - 1000 * 60 * 15),
        contents: [{ type: 'text', content: 'How do I integrate with the Aircraft Maintenance API?' }]
      });
      
      addMessage({
        id: 'msg4',
        source: 'agent',
        agentType: 'documentation',
        timestamp: new Date(Date.now() - 1000 * 60 * 14),
        contents: sampleCodeContents
      });
      
      // Create third conversation
      const conv3 = createConversation('Troubleshooting Engine Start Issues');
      
      // Add messages to third conversation
      addMessage({
        id: 'msg5',
        source: 'user',
        timestamp: new Date(Date.now() - 1000 * 60 * 5),
        contents: [{ type: 'text', content: 'My Cessna 172 engine won\'t start. What could be the issue?' }]
      });
      
      addMessage({
        id: 'msg6',
        source: 'agent',
        agentType: 'troubleshooting',
        timestamp: new Date(Date.now() - 1000 * 60 * 4),
        contents: [{ 
          type: 'text', 
          content: 'There are several potential causes for engine start issues. Let\'s go through a troubleshooting process to identify the problem.' 
        }]
      });
    }
  }, [conversationList.length, createConversation, addMessage]);
  
  // Handle conversation selection
  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
    loadConversation(id);
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Conversation History Test
      </h1>
      
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
            onContinueConversation={() => alert('Continue conversation clicked')}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
}

export default function TestHistoryPage() {
  return (
    <ConversationHistoryProvider>
      <TestHistoryContent />
    </ConversationHistoryProvider>
  );
}
