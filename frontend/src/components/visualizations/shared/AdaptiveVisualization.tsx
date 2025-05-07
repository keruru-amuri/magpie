'use client';

import React, { useState, useEffect } from 'react';
import { DocumentNode } from '../documentation/DocumentTree';
import { Node, Edge } from '@xyflow/react';
import { Procedure } from '../maintenance/ProcedureSteps';
import DocumentTree from '../documentation/DocumentTree';
import DecisionTree from '../troubleshooting/DecisionTree';
import ProcedureSteps from '../maintenance/ProcedureSteps';
import AgentIndicator from '../../orchestrator/AgentIndicator';

// Define visualization data types
export type VisualizationData = 
  | { type: 'documentation'; data: DocumentNode[] }
  | { type: 'troubleshooting'; nodes: Node[]; edges: Edge[] }
  | { type: 'maintenance'; procedure: Procedure };

interface AdaptiveVisualizationProps {
  data: VisualizationData;
  onDocumentNodeSelect?: (node: DocumentNode) => void;
  onFlowNodeClick?: (node: Node) => void;
  onFlowEdgeClick?: (edge: Edge) => void;
  onProcedureStepStatusChange?: (stepId: string, status: any) => void;
  onProcedureStepClick?: (step: any) => void;
  className?: string;
}

/**
 * A component that adapts its visualization based on the agent type
 */
export default function AdaptiveVisualization({
  data,
  onDocumentNodeSelect,
  onFlowNodeClick,
  onFlowEdgeClick,
  onProcedureStepStatusChange,
  onProcedureStepClick,
  className = '',
}: AdaptiveVisualizationProps) {
  const [prevType, setPrevType] = useState<'documentation' | 'troubleshooting' | 'maintenance' | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  // Handle transition when visualization type changes
  useEffect(() => {
    if (prevType && prevType !== data.type) {
      setIsTransitioning(true);
      
      // Reset transition after animation completes
      const timer = setTimeout(() => {
        setIsTransitioning(false);
      }, 300);
      
      return () => clearTimeout(timer);
    }
    
    setPrevType(data.type as any);
  }, [data.type, prevType]);

  // Render visualization based on type
  const renderVisualization = () => {
    switch (data.type) {
      case 'documentation':
        return (
          <DocumentTree
            data={data.data}
            onSelectNode={onDocumentNodeSelect}
            className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}
          />
        );
      case 'troubleshooting':
        return (
          <DecisionTree
            initialNodes={data.nodes}
            initialEdges={data.edges}
            onNodeClick={onFlowNodeClick}
            onEdgeClick={onFlowEdgeClick}
            className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}
          />
        );
      case 'maintenance':
        return (
          <ProcedureSteps
            procedure={data.procedure}
            onStepStatusChange={onProcedureStepStatusChange}
            onStepClick={onProcedureStepClick}
            className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}
          />
        );
      default:
        return (
          <div className="flex items-center justify-center p-8 text-gray-500 dark:text-gray-400">
            No visualization available
          </div>
        );
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* Header with agent indicator */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Visualization
        </h2>
        
        <AgentIndicator 
          agentType={data.type} 
          showLabel={true} 
          size="md"
        />
      </div>
      
      {/* Visualization content */}
      <div className="relative">
        {renderVisualization()}
      </div>
    </div>
  );
}
