'use client';

import React, { useEffect, useState } from 'react';
import DocumentPanel from './DocumentPanel';
import TroubleshootingPanel from './TroubleshootingPanel';
import MaintenancePanel from './MaintenancePanel';
import PreservedContextPanel from './PreservedContextPanel';
import { useOrchestrator } from '../orchestrator/OrchestratorContext';

interface ContextPanelProps {
  agentType?: 'documentation' | 'troubleshooting' | 'maintenance' | null;
  isVisible?: boolean;
  className?: string;
  showPreservedContext?: boolean;
}

export default function ContextPanel({
  agentType,
  isVisible = true,
  className = '',
  showPreservedContext = true,
}: ContextPanelProps) {
  const { preservedContext } = useOrchestrator();
  // Render the appropriate panel based on agent type
  const renderPanel = () => {
    switch (agentType) {
      case 'documentation':
        return <DocumentPanel />;
      case 'troubleshooting':
        return <TroubleshootingPanel />;
      case 'maintenance':
        return <MaintenancePanel />;
      default:
        return (
          <div className="flex items-center justify-center h-full p-8 text-center text-gray-500 dark:text-gray-400">
            <p>Select a topic or ask a question to see relevant information here.</p>
          </div>
        );
    }
  };

  const [isShowing, setIsShowing] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setIsShowing(true);
    } else {
      const timer = setTimeout(() => {
        setIsShowing(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  if (!isVisible && !isShowing) {
    return null;
  }

  return (
    <div className={`h-full ${className} transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      {/* Agent-specific panel */}
      <div className="mb-4">
        {renderPanel()}
      </div>

      {/* Preserved context panel (if enabled and has content) */}
      {showPreservedContext && preservedContext.length > 0 && (
        <div className="mt-4">
          <PreservedContextPanel />
        </div>
      )}
    </div>
  );
}
