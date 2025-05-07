'use client';

import React from 'react';
import AgentIndicator from '../../orchestrator/AgentIndicator';

interface TypingIndicatorProps {
  agentType?: 'documentation' | 'troubleshooting' | 'maintenance' | null;
  message?: string;
  className?: string;
}

/**
 * A component that shows a typing indicator for agent responses
 */
export default function TypingIndicator({
  agentType,
  message = 'Thinking...',
  className = '',
}: TypingIndicatorProps) {
  // Get agent-specific styling
  const getAgentColor = () => {
    switch (agentType) {
      case 'documentation':
        return 'bg-blue-500';
      case 'troubleshooting':
        return 'bg-amber-500';
      case 'maintenance':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className={`flex items-center p-3 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 ${className}`}>
      <div className="flex items-center">
        {agentType ? (
          <AgentIndicator 
            agentType={agentType} 
            showLabel={false} 
            size="sm" 
            className="mr-3"
          />
        ) : (
          <div className="w-6 h-6 rounded-full bg-gray-300 dark:bg-gray-600 mr-3 flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        )}
        
        <span className="text-sm text-gray-700 dark:text-gray-300 mr-2">
          {message}
        </span>
        
        <div className="flex space-x-1">
          <div className={`w-2 h-2 rounded-full ${getAgentColor()} animate-bounce`} style={{ animationDelay: '0ms' }}></div>
          <div className={`w-2 h-2 rounded-full ${getAgentColor()} animate-bounce`} style={{ animationDelay: '150ms' }}></div>
          <div className={`w-2 h-2 rounded-full ${getAgentColor()} animate-bounce`} style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
}
