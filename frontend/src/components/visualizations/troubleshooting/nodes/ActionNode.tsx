'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ActionNodeData } from '../DecisionTree';

const ActionNode = ({ data, selected }: NodeProps<ActionNodeData>) => {
  // Get status color
  const getStatusColor = () => {
    switch (data.status) {
      case 'completed':
        return 'bg-green-500';
      case 'in-progress':
        return 'bg-yellow-500';
      case 'failed':
        return 'bg-red-500';
      case 'pending':
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div
      className={`px-4 py-2 rounded-md shadow-md border-2 ${
        selected ? 'border-green-500' : 'border-green-300'
      } bg-green-50 dark:bg-green-900/30 min-w-[150px] max-w-[250px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-green-500"
      />
      
      <div className="text-center">
        <div className="flex items-center justify-center mb-1">
          <div className="font-semibold text-green-800 dark:text-green-300">
            {data.label}
          </div>
          
          {data.status && (
            <div className={`ml-2 w-3 h-3 rounded-full ${getStatusColor()}`} title={data.status} />
          )}
        </div>
        
        <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          {data.action}
        </div>
        
        {data.result && (
          <div className="text-xs text-gray-600 dark:text-gray-400 border-t border-green-200 dark:border-green-700 pt-1 mt-1">
            <div className="font-medium mb-1">Result:</div>
            <div>{data.result}</div>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-green-500"
      />
    </div>
  );
};

export default memo(ActionNode);
