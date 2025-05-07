'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  NodeTypes,
  Panel,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Import custom node components
import DecisionNode from './nodes/DecisionNode';
import ActionNode from './nodes/ActionNode';
import ProblemNode from './nodes/ProblemNode';
import SolutionNode from './nodes/SolutionNode';

// Define node data types
export interface BaseNodeData {
  label: string;
  description?: string;
  status?: 'pending' | 'in-progress' | 'completed' | 'failed';
}

export interface DecisionNodeData extends BaseNodeData {
  question: string;
  options: string[];
}

export interface ActionNodeData extends BaseNodeData {
  action: string;
  result?: string;
}

export interface ProblemNodeData extends BaseNodeData {
  problem: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface SolutionNodeData extends BaseNodeData {
  solution: string;
  implemented: boolean;
}

// Define custom node types
const nodeTypes: NodeTypes = {
  decision: DecisionNode,
  action: ActionNode,
  problem: ProblemNode,
  solution: SolutionNode,
};

interface DecisionTreeProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodeClick?: (node: Node) => void;
  onEdgeClick?: (edge: Edge) => void;
  readOnly?: boolean;
  className?: string;
}

function DecisionTreeComponent({
  initialNodes = [],
  initialEdges = [],
  onNodeClick,
  onEdgeClick,
  readOnly = false,
  className = '',
}: DecisionTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

  const reactFlowInstance = useReactFlow();

  // Handle node click
  const handleNodeClick = (event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);

    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  // Handle edge click
  const handleEdgeClick = (event: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);

    if (onEdgeClick) {
      onEdgeClick(edge);
    }
  };

  // Handle connection
  const handleConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;

      // Create a custom edge with a marker
      const newEdge = {
        ...params,
        type: 'smoothstep',
        animated: false,
        style: { stroke: '#6366F1' },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#6366F1',
        },
      };

      setEdges((eds) => addEdge(newEdge, eds));
    },
    [readOnly, setEdges]
  );

  // Fit view on initial render
  useEffect(() => {
    if (nodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 100);
    }
  }, [reactFlowInstance, nodes.length]);

  return (
    <div className={`h-[500px] ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
        minZoom={0.2}
        maxZoom={1.5}
        defaultEdgeOptions={{
          type: 'smoothstep',
          style: { stroke: '#6366F1' },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#6366F1',
          },
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Controls />
        <Background color="#aaa" gap={16} />

        {/* Legend panel */}
        <Panel position="top-left" className="bg-white dark:bg-gray-800 p-2 rounded-md shadow-md">
          <div className="text-sm font-medium mb-2">Legend</div>
          <div className="flex flex-col space-y-1">
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-md bg-blue-500 mr-2"></div>
              <span className="text-xs">Decision</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-md bg-green-500 mr-2"></div>
              <span className="text-xs">Action</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-md bg-red-500 mr-2"></div>
              <span className="text-xs">Problem</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded-md bg-purple-500 mr-2"></div>
              <span className="text-xs">Solution</span>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

// Wrap component with ReactFlowProvider
export default function DecisionTree(props: DecisionTreeProps) {
  return (
    <ReactFlowProvider>
      <DecisionTreeComponent {...props} />
    </ReactFlowProvider>
  );
}
