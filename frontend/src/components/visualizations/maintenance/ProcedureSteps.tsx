'use client';

import React, { useState } from 'react';
import { 
  CheckIcon, 
  ClockIcon, 
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentTextIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

// Define step status
export type StepStatus = 'pending' | 'in-progress' | 'completed' | 'skipped' | 'failed';

// Define step type
export type StepType = 'action' | 'inspection' | 'decision' | 'caution' | 'information';

// Define step
export interface ProcedureStep {
  id: string;
  title: string;
  description: string;
  type: StepType;
  status: StepStatus;
  estimatedTime?: number; // in minutes
  requiredTools?: string[];
  requiredParts?: string[];
  notes?: string;
  images?: string[];
  substeps?: ProcedureStep[];
  dependencies?: string[]; // IDs of steps that must be completed before this one
}

// Define procedure
export interface Procedure {
  id: string;
  title: string;
  description: string;
  aircraft: string;
  system: string;
  estimatedTotalTime: number; // in minutes
  steps: ProcedureStep[];
  createdAt: Date;
  updatedAt: Date;
  author?: string;
  references?: string[];
}

interface ProcedureStepsProps {
  procedure: Procedure;
  onStepStatusChange?: (stepId: string, status: StepStatus) => void;
  onStepClick?: (step: ProcedureStep) => void;
  className?: string;
}

/**
 * A component for displaying maintenance procedure steps
 */
export default function ProcedureSteps({
  procedure,
  onStepStatusChange,
  onStepClick,
  className = '',
}: ProcedureStepsProps) {
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});
  
  // Toggle step expansion
  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepId]: !prev[stepId],
    }));
  };
  
  // Handle step status change
  const handleStatusChange = (stepId: string, status: StepStatus) => {
    if (onStepStatusChange) {
      onStepStatusChange(stepId, status);
    }
  };
  
  // Handle step click
  const handleStepClick = (step: ProcedureStep) => {
    if (onStepClick) {
      onStepClick(step);
    }
  };
  
  // Get step type icon
  const getStepTypeIcon = (type: StepType) => {
    switch (type) {
      case 'action':
        return (
          <svg className="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'inspection':
        return (
          <svg className="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        );
      case 'decision':
        return (
          <svg className="h-5 w-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
          </svg>
        );
      case 'caution':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'information':
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    }
  };
  
  // Get step status icon
  const getStepStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'completed':
        return <CheckIcon className="h-5 w-5 text-green-500" />;
      case 'in-progress':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'skipped':
        return (
          <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        );
      case 'pending':
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };
  
  // Render a step
  const renderStep = (step: ProcedureStep, index: number, level = 0) => {
    const isExpanded = expandedSteps[step.id] || false;
    const hasSubsteps = step.substeps && step.substeps.length > 0;
    
    return (
      <div key={step.id} className="mb-2">
        <div 
          className={`border rounded-md overflow-hidden ${
            step.status === 'completed' 
              ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20' 
              : step.status === 'in-progress'
              ? 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20'
              : step.status === 'failed'
              ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
          }`}
          style={{ marginLeft: `${level * 20}px` }}
        >
          {/* Step header */}
          <div 
            className="flex items-center p-3 cursor-pointer"
            onClick={() => handleStepClick(step)}
          >
            <div className="flex-shrink-0 mr-3">
              {getStepTypeIcon(step.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center">
                <span className="text-gray-500 dark:text-gray-400 mr-2">
                  {index + 1}.
                </span>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {step.title}
                </h3>
              </div>
              
              {!isExpanded && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
                  {step.description}
                </p>
              )}
            </div>
            
            <div className="flex items-center ml-4 space-x-2">
              {step.estimatedTime && (
                <div className="flex items-center text-xs text-gray-500 dark:text-gray-400" title="Estimated time">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  <span>{step.estimatedTime} min</span>
                </div>
              )}
              
              <div className="flex-shrink-0" title={`Status: ${step.status}`}>
                {getStepStatusIcon(step.status)}
              </div>
              
              {hasSubsteps && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleStep(step.id);
                  }}
                  className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
                >
                  {isExpanded ? (
                    <ChevronUpIcon className="h-4 w-4" />
                  ) : (
                    <ChevronDownIcon className="h-4 w-4" />
                  )}
                </button>
              )}
            </div>
          </div>
          
          {/* Step details (when expanded) */}
          {isExpanded && (
            <div className="px-4 pb-3 pt-0">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                {step.description}
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                {step.requiredTools && step.requiredTools.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Required Tools
                    </h4>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 list-disc list-inside">
                      {step.requiredTools.map((tool, i) => (
                        <li key={i}>{tool}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {step.requiredParts && step.requiredParts.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Required Parts
                    </h4>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 list-disc list-inside">
                      {step.requiredParts.map((part, i) => (
                        <li key={i}>{part}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              
              {step.notes && (
                <div className="mb-3">
                  <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                    Notes
                  </h4>
                  <p className="text-xs text-gray-700 dark:text-gray-300">
                    {step.notes}
                  </p>
                </div>
              )}
              
              {step.images && step.images.length > 0 && (
                <div className="mb-3">
                  <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                    Images
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {step.images.map((image, i) => (
                      <img
                        key={i}
                        src={image}
                        alt={`Step ${index + 1} image ${i + 1}`}
                        className="h-20 w-auto rounded-md object-cover"
                      />
                    ))}
                  </div>
                </div>
              )}
              
              {/* Status change buttons */}
              <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => handleStatusChange(step.id, 'pending')}
                  className={`px-2 py-1 text-xs rounded-md ${
                    step.status === 'pending'
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  Pending
                </button>
                <button
                  onClick={() => handleStatusChange(step.id, 'in-progress')}
                  className={`px-2 py-1 text-xs rounded-md ${
                    step.status === 'in-progress'
                      ? 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                      : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-800'
                  }`}
                >
                  In Progress
                </button>
                <button
                  onClick={() => handleStatusChange(step.id, 'completed')}
                  className={`px-2 py-1 text-xs rounded-md ${
                    step.status === 'completed'
                      ? 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
                      : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-800'
                  }`}
                >
                  Completed
                </button>
                <button
                  onClick={() => handleStatusChange(step.id, 'skipped')}
                  className={`px-2 py-1 text-xs rounded-md ${
                    step.status === 'skipped'
                      ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                      : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-200 dark:hover:bg-yellow-800'
                  }`}
                >
                  Skipped
                </button>
                <button
                  onClick={() => handleStatusChange(step.id, 'failed')}
                  className={`px-2 py-1 text-xs rounded-md ${
                    step.status === 'failed'
                      ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200'
                      : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-800'
                  }`}
                >
                  Failed
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Render substeps if expanded */}
        {hasSubsteps && isExpanded && (
          <div className="mt-2">
            {step.substeps!.map((substep, i) => renderStep(substep, i, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      {/* Procedure header */}
      <div className="bg-white dark:bg-gray-800 p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {procedure.title}
        </h2>
        
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {procedure.description}
        </p>
        
        <div className="mt-3 flex flex-wrap gap-4">
          <div>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Aircraft
            </span>
            <p className="text-sm text-gray-900 dark:text-white">
              {procedure.aircraft}
            </p>
          </div>
          
          <div>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              System
            </span>
            <p className="text-sm text-gray-900 dark:text-white">
              {procedure.system}
            </p>
          </div>
          
          <div>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Estimated Time
            </span>
            <p className="text-sm text-gray-900 dark:text-white">
              {procedure.estimatedTotalTime} minutes
            </p>
          </div>
          
          {procedure.author && (
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Author
              </span>
              <p className="text-sm text-gray-900 dark:text-white">
                {procedure.author}
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Procedure steps */}
      <div className="p-4">
        <h3 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Procedure Steps
        </h3>
        
        {procedure.steps.length === 0 ? (
          <div className="text-center p-4 text-gray-500 dark:text-gray-400">
            No steps available for this procedure
          </div>
        ) : (
          <div className="space-y-2">
            {procedure.steps.map((step, index) => renderStep(step, index))}
          </div>
        )}
      </div>
    </div>
  );
}
