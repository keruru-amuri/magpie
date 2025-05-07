'use client';

import React from 'react';
import { DocumentTextIcon, WrenchScrewdriverIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';
import ConfidenceIndicator from './ConfidenceIndicator';

interface EnhancedAgentIndicatorProps {
  agentType: 'documentation' | 'troubleshooting' | 'maintenance';
  confidence?: number;
  isActive?: boolean;
  showDetails?: boolean;
  className?: string;
  onToggleDetails?: () => void;
}

export default function EnhancedAgentIndicator({
  agentType,
  confidence = 0.8,
  isActive = true,
  showDetails = false,
  className = '',
  onToggleDetails,
}: EnhancedAgentIndicatorProps) {
  // Define agent-specific configurations
  const agentConfig = {
    documentation: {
      name: 'Documentation Assistant',
      description: 'Helps you find and navigate technical documentation',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      textColor: 'text-blue-600 dark:text-blue-400',
      borderColor: 'border-blue-200 dark:border-blue-800',
      icon: <DocumentTextIcon className="h-5 w-5" />,
      capabilities: [
        'Search across technical documents',
        'Answer questions about aircraft systems',
        'Provide cross-references between documents',
      ],
    },
    troubleshooting: {
      name: 'Troubleshooting Advisor',
      description: 'Helps diagnose and resolve technical issues',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      textColor: 'text-amber-600 dark:text-amber-400',
      borderColor: 'border-amber-200 dark:border-amber-800',
      icon: <WrenchScrewdriverIcon className="h-5 w-5" />,
      capabilities: [
        'Analyze problem descriptions',
        'Provide diagnostic procedures',
        'Suggest potential solutions',
      ],
    },
    maintenance: {
      name: 'Maintenance Procedure Generator',
      description: 'Creates customized maintenance procedures',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-600 dark:text-green-400',
      borderColor: 'border-green-200 dark:border-green-800',
      icon: <ClipboardDocumentCheckIcon className="h-5 w-5" />,
      capabilities: [
        'Generate task-specific procedures',
        'Customize for equipment variants',
        'Include safety precautions and required tools',
      ],
    },
  };

  const { name, description, bgColor, textColor, borderColor, icon, capabilities } = agentConfig[agentType];

  // Handle click on the indicator
  const handleClick = () => {
    if (onToggleDetails) {
      onToggleDetails();
    }
  };

  return (
    <div className={`${className}`}>
      <button
        onClick={handleClick}
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${bgColor} ${textColor} border ${borderColor} ${
          isActive ? 'opacity-100' : 'opacity-60'
        } transition-all duration-200 hover:opacity-100`}
        aria-expanded={showDetails}
        aria-label={`${name} agent information`}
      >
        <span className="flex-shrink-0">{icon}</span>
        <span className="font-medium">{name}</span>
        {confidence !== undefined && (
          <ConfidenceIndicator confidence={confidence} size="sm" className="ml-2" />
        )}
      </button>

      {showDetails && (
        <div className={`mt-2 p-3 rounded-lg border ${borderColor} ${bgColor} transition-opacity duration-200`}>
          <p className="text-sm mb-2">{description}</p>

          <div className="mt-3">
            <h4 className={`text-xs font-semibold ${textColor} uppercase tracking-wider mb-1`}>
              Capabilities
            </h4>
            <ul className="text-xs space-y-1 text-gray-700 dark:text-gray-300">
              {capabilities.map((capability, index) => (
                <li key={index} className="flex items-start">
                  <span className="mr-1.5 mt-0.5 text-xs">•</span>
                  <span>{capability}</span>
                </li>
              ))}
            </ul>
          </div>

          {confidence !== undefined && (
            <div className="mt-3">
              <h4 className={`text-xs font-semibold ${textColor} uppercase tracking-wider mb-1`}>
                Confidence
              </h4>
              <ConfidenceIndicator confidence={confidence} showPercentage={true} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
