'use client';

import React from 'react';
import { KeyIcon, ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { useOrchestrator } from '../orchestrator/OrchestratorContext';
import AgentIndicator from '../orchestrator/AgentIndicator';

interface PreservedContextPanelProps {
  className?: string;
}

export default function PreservedContextPanel({ className = '' }: PreservedContextPanelProps) {
  const { preservedContext } = useOrchestrator();

  // Format date for context items
  const formatContextDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date);
  };

  // Format value for display
  const formatValue = (value: any): string => {
    if (typeof value === 'string') {
      return value;
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    } else if (value === null) {
      return 'null';
    } else if (value === undefined) {
      return 'undefined';
    } else if (Array.isArray(value)) {
      return `Array(${value.length})`;
    } else if (typeof value === 'object') {
      return 'Object';
    } else {
      return String(value);
    }
  };

  // Group context items by agent type
  const groupedContext = preservedContext.reduce((acc, item) => {
    const agentType = item.agentType || 'unknown';
    if (!acc[agentType]) {
      acc[agentType] = [];
    }
    acc[agentType].push(item);
    return acc;
  }, {} as Record<string, typeof preservedContext>);

  if (preservedContext.length === 0) {
    return (
      <div className={`p-4 text-center text-gray-500 dark:text-gray-400 ${className}`}>
        <KeyIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No preserved context available.</p>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <KeyIcon className="h-5 w-5 mr-2 text-primary-500" />
          Preserved Context
        </h3>
      </div>

      <div className="p-4">
        <div className="space-y-4 max-h-[500px] overflow-y-auto">
          {Object.entries(groupedContext).map(([agentType, items]) => (
            <div key={agentType} className="mb-4">
              <div className="flex items-center mb-2">
                {agentType !== 'unknown' && agentType !== 'null' ? (
                  <AgentIndicator agentType={agentType as any} showLabel={true} />
                ) : (
                  <span className="text-sm text-gray-500 dark:text-gray-400">Shared Context</span>
                )}
              </div>
              
              <div className="space-y-2">
                {items.map((item, index) => (
                  <div 
                    key={`${agentType}-${index}`} 
                    className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex justify-between items-start">
                      <div className="font-medium text-gray-700 dark:text-gray-300 text-sm">{item.key}</div>
                      <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                        <ClockIcon className="h-3 w-3 mr-1" />
                        {formatContextDate(item.timestamp)}
                      </div>
                    </div>
                    
                    <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 break-words">
                      {typeof item.value === 'string' ? (
                        item.value.length > 200 ? (
                          <div>
                            <p>{item.value.substring(0, 200)}...</p>
                            <button 
                              className="mt-1 text-xs text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
                              onClick={() => alert(item.value)}
                            >
                              Show full content
                            </button>
                          </div>
                        ) : (
                          <p>{item.value}</p>
                        )
                      ) : (
                        <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                          {formatValue(item.value)}
                        </pre>
                      )}
                    </div>
                    
                    <div className="mt-2 flex justify-end">
                      <span className={`text-xs px-1.5 py-0.5 rounded-full ${item.isShared ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'}`}>
                        {item.isShared ? 'Shared' : 'Private'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
