'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { SolutionNodeData } from '../DecisionTree';

const SolutionNode = ({ data, selected }: NodeProps<SolutionNodeData>) => {
  return (
    <div
      className={`px-4 py-2 rounded-md shadow-md border-2 ${
        selected ? 'border-purple-500' : 'border-purple-300'
      } bg-purple-50 dark:bg-purple-900/30 min-w-[150px] max-w-[250px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-purple-500"
      />
      
      <div className="text-center">
        <div className="flex items-center justify-center mb-1">
          <div className="font-semibold text-purple-800 dark:text-purple-300">
            {data.label}
          </div>
          
          {data.implemented ? (
            <svg 
              className="ml-2 h-5 w-5 text-green-500" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
              title="Implemented"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg 
              className="ml-2 h-5 w-5 text-gray-400" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
              title="Not implemented"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>
        
        <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          {data.solution}
        </div>
        
        {data.description && (
          <div className="text-xs text-gray-600 dark:text-gray-400 border-t border-purple-200 dark:border-purple-700 pt-1 mt-1">
            <div className="font-medium mb-1">Details:</div>
            <div>{data.description}</div>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-purple-500"
      />
    </div>
  );
};

export default memo(SolutionNode);
