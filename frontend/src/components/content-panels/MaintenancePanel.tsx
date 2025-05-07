'use client';

import React, { useState } from 'react';
import { ClipboardDocumentCheckIcon, CheckCircleIcon, PrinterIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from '@heroicons/react/24/solid';

interface MaintenanceStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  warnings?: string[];
  tools?: string[];
  parts?: { name: string; partNumber: string }[];
}

interface MaintenanceProcedureProps {
  procedure?: {
    id: string;
    title: string;
    description: string;
    aircraftType: string;
    estimatedTime: string;
    steps: MaintenanceStep[];
  };
  onStepToggle?: (stepId: string, completed: boolean) => void;
  onPrint?: () => void;
  onDownload?: () => void;
  className?: string;
}

export default function MaintenancePanel({
  procedure,
  onStepToggle,
  onPrint,
  onDownload,
  className = '',
}: MaintenanceProcedureProps) {
  const [activeStepId, setActiveStepId] = useState<string | null>(null);
  
  // Mock procedure if none provided
  const displayProcedure = procedure || {
    id: 'procedure-1',
    title: 'APU Maintenance Procedure',
    description: 'Routine maintenance procedure for the Auxiliary Power Unit (APU).',
    aircraftType: 'Boeing 737 MAX',
    estimatedTime: '4 hours',
    steps: [
      {
        id: 'step-1',
        title: 'Preparation and Safety Measures',
        description: 'Ensure aircraft is properly grounded and power is disconnected before beginning maintenance.',
        completed: true,
        warnings: [
          'Ensure all electrical power is disconnected',
          'Verify APU has cooled down completely before servicing'
        ],
        tools: [
          'Safety gloves',
          'Safety glasses',
          'Grounding equipment'
        ],
        parts: []
      },
      {
        id: 'step-2',
        title: 'APU Access Panel Removal',
        description: 'Remove the APU access panel to gain entry to the APU compartment.',
        completed: false,
        warnings: [
          'Support panel during removal to prevent damage'
        ],
        tools: [
          'Socket wrench set',
          'Torque wrench',
          'Panel support stand'
        ],
        parts: []
      },
      {
        id: 'step-3',
        title: 'Oil Level Inspection',
        description: 'Check the APU oil level and refill if necessary.',
        completed: false,
        warnings: [
          'Use only approved oil type as specified in the maintenance manual'
        ],
        tools: [
          'Oil dipstick',
          'Funnel',
          'Cleaning cloths'
        ],
        parts: [
          { name: 'APU Oil', partNumber: 'MIL-PRF-23699F' }
        ]
      },
      {
        id: 'step-4',
        title: 'Air Filter Replacement',
        description: 'Remove and replace the APU air filter.',
        completed: false,
        warnings: [
          'Inspect filter housing for damage before installing new filter'
        ],
        tools: [
          'Filter removal tool',
          'Inspection light',
          'Torque wrench'
        ],
        parts: [
          { name: 'APU Air Filter', partNumber: 'AF-737-APU-101' }
        ]
      },
      {
        id: 'step-5',
        title: 'Reassembly and Testing',
        description: 'Reinstall the APU access panel and perform operational test.',
        completed: false,
        warnings: [
          'Ensure all connections are secure before testing',
          'Monitor APU during initial startup for any abnormalities'
        ],
        tools: [
          'Torque wrench',
          'Diagnostic equipment'
        ],
        parts: []
      }
    ],
  };

  const completedSteps = displayProcedure.steps.filter(step => step.completed).length;
  const totalSteps = displayProcedure.steps.length;
  const progressPercentage = Math.round((completedSteps / totalSteps) * 100);

  const handleStepClick = (stepId: string) => {
    setActiveStepId(activeStepId === stepId ? null : stepId);
  };

  const handleStepToggle = (stepId: string, completed: boolean) => {
    if (onStepToggle) {
      onStepToggle(stepId, completed);
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <ClipboardDocumentCheckIcon className="h-5 w-5 mr-2 text-green-500" />
              {displayProcedure.title}
            </h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {displayProcedure.description}
            </p>
          </div>
          <div className="flex space-x-2">
            <button 
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg"
              onClick={onPrint}
              title="Print procedure"
            >
              <PrinterIcon className="h-5 w-5" />
            </button>
            <button 
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg"
              onClick={onDownload}
              title="Download procedure"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded-md">
            <span className="text-gray-500 dark:text-gray-400">Aircraft Type:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">{displayProcedure.aircraftType}</span>
          </div>
          <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded-md">
            <span className="text-gray-500 dark:text-gray-400">Est. Time:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">{displayProcedure.estimatedTime}</span>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-700 dark:text-gray-300">Progress</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{progressPercentage}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
            <div 
              className="bg-green-600 h-2.5 rounded-full" 
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 text-right">
            {completedSteps} of {totalSteps} steps completed
          </div>
        </div>
      </div>
      
      <div className="p-4 max-h-[500px] overflow-y-auto">
        <div className="space-y-4">
          {displayProcedure.steps.map((step, index) => (
            <div 
              key={step.id} 
              className={`border ${
                step.completed 
                  ? 'border-green-200 dark:border-green-900' 
                  : 'border-gray-200 dark:border-gray-700'
              } rounded-lg overflow-hidden`}
            >
              <div 
                className={`p-4 flex items-start cursor-pointer ${
                  step.completed 
                    ? 'bg-green-50 dark:bg-green-900/20' 
                    : activeStepId === step.id 
                    ? 'bg-gray-50 dark:bg-gray-800' 
                    : 'bg-white dark:bg-gray-900'
                }`}
                onClick={() => handleStepClick(step.id)}
              >
                <div className="flex-shrink-0 mr-3">
                  <div 
                    className={`h-6 w-6 rounded-full flex items-center justify-center ${
                      step.completed 
                        ? 'bg-green-500 text-white' 
                        : 'border-2 border-gray-300 dark:border-gray-600'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStepToggle(step.id, !step.completed);
                    }}
                  >
                    {step.completed && <CheckIcon className="h-4 w-4" />}
                  </div>
                </div>
                <div className="flex-grow">
                  <h4 className={`text-base font-medium ${
                    step.completed 
                      ? 'text-green-700 dark:text-green-400 line-through' 
                      : 'text-gray-900 dark:text-white'
                  }`}>
                    {index + 1}. {step.title}
                  </h4>
                  <p className={`mt-1 text-sm ${
                    step.completed 
                      ? 'text-green-600 dark:text-green-500' 
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                    {step.description}
                  </p>
                </div>
              </div>
              
              {activeStepId === step.id && (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                  {step.warnings && step.warnings.length > 0 && (
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">Warnings:</h5>
                      <ul className="list-disc pl-5 space-y-1">
                        {step.warnings.map((warning, i) => (
                          <li key={i} className="text-xs text-red-600 dark:text-red-400">{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {step.tools && step.tools.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Required Tools:</h5>
                        <ul className="list-disc pl-5 space-y-1">
                          {step.tools.map((tool, i) => (
                            <li key={i} className="text-xs text-gray-600 dark:text-gray-400">{tool}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {step.parts && step.parts.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Required Parts:</h5>
                        <ul className="list-disc pl-5 space-y-1">
                          {step.parts.map((part, i) => (
                            <li key={i} className="text-xs text-gray-600 dark:text-gray-400">
                              {part.name} <span className="text-gray-500 dark:text-gray-500">({part.partNumber})</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <button 
                      className={`px-4 py-2 rounded-md flex items-center ${
                        step.completed 
                          ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' 
                          : 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                      }`}
                      onClick={() => handleStepToggle(step.id, !step.completed)}
                    >
                      {step.completed ? (
                        <>
                          <span className="mr-2">Mark as Incomplete</span>
                        </>
                      ) : (
                        <>
                          <CheckCircleIcon className="h-5 w-5 mr-2" />
                          <span>Mark as Complete</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
