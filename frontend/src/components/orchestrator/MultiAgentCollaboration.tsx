'use client';

import React from 'react';
import { UsersIcon } from '@heroicons/react/24/outline';
import AgentIndicator from './AgentIndicator';

interface Agent {
  type: 'documentation' | 'troubleshooting' | 'maintenance';
  role: string;
  contribution?: string;
}

interface MultiAgentCollaborationProps {
  agents: Agent[];
  primaryAgent?: 'documentation' | 'troubleshooting' | 'maintenance';
  description?: string;
  className?: string;
}

export default function MultiAgentCollaboration({
  agents,
  primaryAgent,
  description = 'Multiple agents are collaborating to provide a comprehensive response.',
  className = '',
}: MultiAgentCollaborationProps) {
  return (
    <div className={`bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 ${className}`}>
      <div className="flex items-center mb-3">
        <UsersIcon className="h-5 w-5 mr-2 text-primary-500" />
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
          Multi-Agent Collaboration
        </h3>
      </div>
      
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {description}
      </p>
      
      <div className="space-y-3">
        {agents.map((agent, index) => (
          <div 
            key={index} 
            className={`flex items-start p-3 rounded-md ${
              agent.type === primaryAgent 
                ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-100 dark:border-primary-800/30' 
                : 'bg-gray-100 dark:bg-gray-700'
            }`}
          >
            <div className="flex-shrink-0 mr-3">
              <AgentIndicator agentType={agent.type} size="sm" />
            </div>
            <div>
              <div className="flex items-center">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  {agent.role}
                </h4>
                {agent.type === primaryAgent && (
                  <span className="ml-2 text-xs bg-primary-100 dark:bg-primary-800 text-primary-800 dark:text-primary-200 px-2 py-0.5 rounded-full">
                    Primary
                  </span>
                )}
              </div>
              {agent.contribution && (
                <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                  {agent.contribution}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
