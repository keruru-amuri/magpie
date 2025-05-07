'use client';

import React, { useState } from 'react';
import { WrenchScrewdriverIcon, CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from '@heroicons/react/24/solid';

interface TroubleshootingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  substeps?: TroubleshootingStep[];
}

interface TroubleshootingPanelProps {
  issue?: {
    id: string;
    title: string;
    description: string;
    steps: TroubleshootingStep[];
  };
  onStepComplete?: (stepId: string, status: 'completed' | 'failed') => void;
  onReset?: () => void;
  className?: string;
}

export default function TroubleshootingPanel({
  issue,
  onStepComplete,
  onReset,
  className = '',
}: TroubleshootingPanelProps) {
  const [activeStepId, setActiveStepId] = useState<string | null>(null);
  
  // Mock issue if none provided
  const displayIssue = issue || {
    id: 'issue-1',
    title: 'Hydraulic System Pressure Loss',
    description: 'Aircraft experiencing intermittent hydraulic pressure loss during flight operations.',
    steps: [
      {
        id: 'step-1',
        title: 'Check Hydraulic Fluid Level',
        description: 'Verify that the hydraulic fluid reservoir is filled to the appropriate level.',
        status: 'completed',
      },
      {
        id: 'step-2',
        title: 'Inspect for Leaks',
        description: 'Perform a visual inspection of hydraulic lines, fittings, and components for signs of leakage.',
        status: 'in-progress',
        substeps: [
          {
            id: 'substep-2-1',
            title: 'Check Main Hydraulic Lines',
            description: 'Inspect the main hydraulic lines for cracks, abrasions, or leaks.',
            status: 'completed',
          },
          {
            id: 'substep-2-2',
            title: 'Inspect Pump Connections',
            description: 'Check all connections at the hydraulic pump for proper torque and signs of leakage.',
            status: 'in-progress',
          },
          {
            id: 'substep-2-3',
            title: 'Examine Actuator Seals',
            description: 'Inspect hydraulic actuator seals for damage or deterioration.',
            status: 'pending',
          },
        ],
      },
      {
        id: 'step-3',
        title: 'Test Hydraulic Pump',
        description: 'Perform operational test of the hydraulic pump to verify proper pressure output.',
        status: 'pending',
      },
      {
        id: 'step-4',
        title: 'Check Relief Valve',
        description: 'Inspect and test the pressure relief valve for proper operation.',
        status: 'pending',
      },
    ],
  };

  const handleStepClick = (stepId: string) => {
    setActiveStepId(activeStepId === stepId ? null : stepId);
  };

  const handleStepComplete = (stepId: string, status: 'completed' | 'failed') => {
    if (onStepComplete) {
      onStepComplete(stepId, status);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'in-progress':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-gray-300 dark:border-gray-600" />;
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <WrenchScrewdriverIcon className="h-5 w-5 mr-2 text-amber-500" />
          Troubleshooting: {displayIssue.title}
        </h3>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {displayIssue.description}
        </p>
      </div>
      
      <div className="p-4 max-h-[500px] overflow-y-auto">
        <div className="space-y-4">
          {displayIssue.steps.map((step, index) => (
            <div 
              key={step.id} 
              className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              <div 
                className={`p-4 flex items-start cursor-pointer ${
                  activeStepId === step.id 
                    ? 'bg-gray-50 dark:bg-gray-800' 
                    : 'bg-white dark:bg-gray-900'
                }`}
                onClick={() => handleStepClick(step.id)}
              >
                <div className="flex-shrink-0 mr-3 mt-0.5">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-grow">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-medium text-gray-900 dark:text-white">
                      {index + 1}. {step.title}
                    </h4>
                    {step.substeps && (
                      <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded-full">
                        {step.substeps.filter(s => s.status === 'completed').length}/{step.substeps.length}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>
              </div>
              
              {activeStepId === step.id && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                  {step.substeps && step.substeps.length > 0 ? (
                    <div className="space-y-3">
                      {step.substeps.map((substep, subIndex) => (
                        <div key={substep.id} className="flex items-start">
                          <div className="flex-shrink-0 mr-3 mt-0.5">
                            {getStatusIcon(substep.status)}
                          </div>
                          <div className="flex-grow">
                            <h5 className="text-sm font-medium text-gray-900 dark:text-white">
                              {index + 1}.{subIndex + 1} {substep.title}
                            </h5>
                            <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                              {substep.description}
                            </p>
                          </div>
                          {substep.status === 'in-progress' && (
                            <div className="flex-shrink-0 ml-2 space-x-2">
                              <button 
                                className="p-1 rounded-full bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-800"
                                onClick={() => handleStepComplete(substep.id, 'completed')}
                                title="Mark as completed"
                              >
                                <CheckIcon className="h-4 w-4" />
                              </button>
                              <button 
                                className="p-1 rounded-full bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-800"
                                onClick={() => handleStepComplete(substep.id, 'failed')}
                                title="Mark as failed"
                              >
                                <XCircleIcon className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex justify-center space-x-4">
                      <button 
                        className="px-4 py-2 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-md hover:bg-green-200 dark:hover:bg-green-800 flex items-center"
                        onClick={() => handleStepComplete(step.id, 'completed')}
                      >
                        <CheckCircleIcon className="h-5 w-5 mr-2" />
                        Mark as Completed
                      </button>
                      <button 
                        className="px-4 py-2 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-md hover:bg-red-200 dark:hover:bg-red-800 flex items-center"
                        onClick={() => handleStepComplete(step.id, 'failed')}
                      >
                        <XCircleIcon className="h-5 w-5 mr-2" />
                        Mark as Failed
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="mt-6 flex justify-center">
          <button 
            className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 flex items-center"
            onClick={onReset}
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" />
            Reset Troubleshooting
          </button>
        </div>
      </div>
    </div>
  );
}
