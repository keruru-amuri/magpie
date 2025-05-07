'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { DecisionNodeData } from '../DecisionTree';

const DecisionNode = ({ data, selected }: NodeProps<DecisionNodeData>) => {
  return (
    <div
      className={`px-4 py-2 rounded-md shadow-md border-2 ${
        selected ? 'border-blue-500' : 'border-blue-300'
      } bg-blue-50 dark:bg-blue-900/30 min-w-[150px] max-w-[250px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-blue-500"
      />
      
      <div className="text-center">
        <div className="font-semibold text-blue-800 dark:text-blue-300 mb-1">
          {data.label}
        </div>
        
        <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          {data.question}
        </div>
        
        {data.options && data.options.length > 0 && (
          <div className="text-xs text-gray-600 dark:text-gray-400 border-t border-blue-200 dark:border-blue-700 pt-1 mt-1">
            <div className="font-medium mb-1">Options:</div>
            <ul className="list-disc list-inside">
              {data.options.map((option, index) => (
                <li key={index} className="truncate">{option}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-500"
      />
    </div>
  );
};

export default memo(DecisionNode);
