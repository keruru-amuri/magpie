'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ProblemNodeData } from '../DecisionTree';

const ProblemNode = ({ data, selected }: NodeProps<ProblemNodeData>) => {
  // Get severity color
  const getSeverityColor = () => {
    switch (data.severity) {
      case 'critical':
        return 'bg-red-700';
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
      default:
        return 'bg-yellow-300';
    }
  };

  return (
    <div
      className={`px-4 py-2 rounded-md shadow-md border-2 ${
        selected ? 'border-red-500' : 'border-red-300'
      } bg-red-50 dark:bg-red-900/30 min-w-[150px] max-w-[250px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-red-500"
      />
      
      <div className="text-center">
        <div className="flex items-center justify-center mb-1">
          <div className="font-semibold text-red-800 dark:text-red-300">
            {data.label}
          </div>
          
          <div 
            className={`ml-2 w-3 h-3 rounded-full ${getSeverityColor()}`} 
            title={`Severity: ${data.severity}`} 
          />
        </div>
        
        <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          {data.problem}
        </div>
        
        {data.description && (
          <div className="text-xs text-gray-600 dark:text-gray-400 border-t border-red-200 dark:border-red-700 pt-1 mt-1">
            <div className="font-medium mb-1">Details:</div>
            <div>{data.description}</div>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-red-500"
      />
    </div>
  );
};

export default memo(ProblemNode);
