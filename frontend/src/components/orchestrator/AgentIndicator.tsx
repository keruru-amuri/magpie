'use client';

import React from 'react';
import { DocumentTextIcon, WrenchScrewdriverIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';

interface AgentIndicatorProps {
  agentType: 'documentation' | 'troubleshooting' | 'maintenance';
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function AgentIndicator({ 
  agentType, 
  showLabel = false, 
  size = 'sm' 
}: AgentIndicatorProps) {
  // Define colors and icons based on agent type
  const config = {
    documentation: {
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      textColor: 'text-blue-600 dark:text-blue-400',
      borderColor: 'border-blue-200 dark:border-blue-800',
      label: 'Documentation',
      icon: <DocumentTextIcon className={size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'} />
    },
    troubleshooting: {
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      textColor: 'text-amber-600 dark:text-amber-400',
      borderColor: 'border-amber-200 dark:border-amber-800',
      label: 'Troubleshooting',
      icon: <WrenchScrewdriverIcon className={size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'} />
    },
    maintenance: {
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-600 dark:text-green-400',
      borderColor: 'border-green-200 dark:border-green-800',
      label: 'Maintenance',
      icon: <ClipboardDocumentCheckIcon className={size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'} />
    }
  };

  const { bgColor, textColor, borderColor, label, icon } = config[agentType];

  return (
    <div className={`inline-flex items-center ${showLabel ? 'px-2 py-1' : 'p-1'} rounded-full ${bgColor} ${textColor} border ${borderColor}`}>
      {icon}
      {showLabel && <span className={`ml-1 ${size === 'sm' ? 'text-xs' : size === 'md' ? 'text-sm' : 'text-base'} font-medium`}>{label}</span>}
    </div>
  );
}
