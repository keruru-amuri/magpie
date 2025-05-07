'use client';

import React, { useState } from 'react';
import AdaptiveVisualization from '../../components/visualizations/shared/AdaptiveVisualization';
import Message from '../../components/visualizations/shared/Message';
import TypingIndicator from '../../components/visualizations/shared/TypingIndicator';
import { DocumentNode } from '../../components/visualizations/documentation/DocumentTree';
import { Node, Edge } from '@xyflow/react';
import { Procedure, ProcedureStep } from '../../components/visualizations/maintenance/ProcedureSteps';
import Button from '../../components/common/Button';

// Sample documentation data
const documentationData: DocumentNode[] = [
  {
    id: 'root1',
    name: 'Aircraft Maintenance Manual',
    type: 'folder',
    children: [
      {
        id: 'doc1',
        name: 'Chapter 1: Introduction',
        type: 'document',
        children: [
          {
            id: 'sec1',
            name: 'Section 1.1: General Information',
            type: 'section',
            content: 'This manual provides maintenance procedures for the aircraft...'
          },
          {
            id: 'sec2',
            name: 'Section 1.2: Safety Precautions',
            type: 'section',
            content: 'Always follow these safety guidelines when performing maintenance...'
          }
        ]
      },
      {
        id: 'doc2',
        name: 'Chapter 2: Airframe',
        type: 'document',
        children: [
          {
            id: 'sec3',
            name: 'Section 2.1: Fuselage',
            type: 'section',
            content: 'The fuselage is the main body of the aircraft...'
          },
          {
            id: 'sec4',
            name: 'Section 2.2: Wings',
            type: 'section',
            content: 'The wings provide lift and stability...'
          }
        ]
      }
    ]
  },
  {
    id: 'root2',
    name: 'Component Maintenance Manual',
    type: 'folder',
    children: [
      {
        id: 'doc3',
        name: 'Engine Systems',
        type: 'document',
        content: 'This section covers maintenance procedures for engine systems...'
      },
      {
        id: 'doc4',
        name: 'Avionics Systems',
        type: 'document',
        content: 'This section covers maintenance procedures for avionics systems...'
      }
    ]
  }
];

// Sample troubleshooting data
const troubleshootingNodes: Node[] = [
  {
    id: '1',
    type: 'problem',
    position: { x: 250, y: 0 },
    data: {
      label: 'Engine Start Problem',
      problem: 'Engine fails to start',
      severity: 'high'
    }
  },
  {
    id: '2',
    type: 'decision',
    position: { x: 250, y: 100 },
    data: {
      label: 'Check Battery',
      question: 'Is the battery voltage above 24V?',
      options: ['Yes', 'No']
    }
  },
  {
    id: '3',
    type: 'action',
    position: { x: 100, y: 200 },
    data: {
      label: 'Replace Battery',
      action: 'Replace the battery with a fully charged one',
      status: 'pending'
    }
  },
  {
    id: '4',
    type: 'decision',
    position: { x: 400, y: 200 },
    data: {
      label: 'Check Fuel',
      question: 'Is there sufficient fuel in the tank?',
      options: ['Yes', 'No']
    }
  },
  {
    id: '5',
    type: 'action',
    position: { x: 400, y: 300 },
    data: {
      label: 'Add Fuel',
      action: 'Refill the fuel tank',
      status: 'completed'
    }
  },
  {
    id: '6',
    type: 'solution',
    position: { x: 250, y: 400 },
    data: {
      label: 'Solution',
      solution: 'Engine should now start properly',
      implemented: true
    }
  }
];

const troubleshootingEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: false },
  { id: 'e2-3', source: '2', target: '3', label: 'No', animated: false },
  { id: 'e2-4', source: '2', target: '4', label: 'Yes', animated: false },
  { id: 'e4-5', source: '4', target: '5', label: 'No', animated: false },
  { id: 'e3-6', source: '3', target: '6', animated: false },
  { id: 'e5-6', source: '5', target: '6', animated: false }
];

// Sample maintenance procedure data
const maintenanceSteps: ProcedureStep[] = [
  {
    id: 'step1',
    title: 'Prepare for Inspection',
    description: 'Gather all necessary tools and equipment for the inspection',
    type: 'action',
    status: 'completed',
    estimatedTime: 15,
    requiredTools: ['Flashlight', 'Inspection mirror', 'Digital camera'],
    substeps: [
      {
        id: 'step1.1',
        title: 'Collect Tools',
        description: 'Gather all tools from the maintenance toolbox',
        type: 'action',
        status: 'completed'
      },
      {
        id: 'step1.2',
        title: 'Prepare Documentation',
        description: 'Ensure all required documentation is available',
        type: 'action',
        status: 'completed'
      }
    ]
  },
  {
    id: 'step2',
    title: 'Visual Inspection',
    description: 'Perform a visual inspection of the engine components',
    type: 'inspection',
    status: 'in-progress',
    estimatedTime: 30,
    notes: 'Pay special attention to any signs of fluid leaks or corrosion',
    substeps: [
      {
        id: 'step2.1',
        title: 'Inspect Engine Exterior',
        description: 'Check for any visible damage or leaks on the engine exterior',
        type: 'inspection',
        status: 'completed'
      },
      {
        id: 'step2.2',
        title: 'Inspect Fuel Lines',
        description: 'Check all fuel lines for signs of wear or damage',
        type: 'inspection',
        status: 'in-progress'
      }
    ]
  },
  {
    id: 'step3',
    title: 'Check Oil Level',
    description: 'Check the engine oil level and condition',
    type: 'inspection',
    status: 'pending',
    estimatedTime: 10,
    requiredTools: ['Dipstick', 'Clean cloth'],
    notes: 'Oil should be amber to light brown in color'
  },
  {
    id: 'step4',
    title: 'Replace Air Filter',
    description: 'Remove and replace the engine air filter',
    type: 'action',
    status: 'pending',
    estimatedTime: 20,
    requiredTools: ['Screwdriver', 'Socket wrench'],
    requiredParts: ['New air filter (P/N: AF-2234)']
  }
];

const maintenanceProcedure: Procedure = {
  id: 'proc1',
  title: 'Engine Maintenance Procedure',
  description: 'Routine 100-hour inspection and maintenance for aircraft engine',
  aircraft: 'Cessna 172',
  system: 'Powerplant',
  estimatedTotalTime: 120,
  steps: maintenanceSteps,
  createdAt: new Date(),
  updatedAt: new Date(),
  author: 'John Smith',
  references: ['Maintenance Manual Section 71-00-00', 'Service Bulletin SB-2021-05']
};

// Sample messages
const sampleMessages = [
  {
    id: 'msg1',
    source: 'user' as const,
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    contents: [
      {
        type: 'text' as const,
        content: 'How do I perform a 100-hour inspection on a Cessna 172 engine?'
      }
    ]
  },
  {
    id: 'msg2',
    source: 'agent' as const,
    agentType: 'maintenance' as const,
    timestamp: new Date(Date.now() - 1000 * 60 * 4),
    contents: [
      {
        type: 'text' as const,
        content: 'I\'ll help you with the 100-hour inspection procedure for a Cessna 172 engine. Here\'s a step-by-step guide:'
      }
    ]
  }
];

export default function TestVisualizationsPage() {
  const [activeAgent, setActiveAgent] = useState<'documentation' | 'troubleshooting' | 'maintenance'>('documentation');
  const [messages, setMessages] = useState(sampleMessages);
  const [isTyping, setIsTyping] = useState(false);
  
  // Get visualization data based on active agent
  const getVisualizationData = () => {
    switch (activeAgent) {
      case 'documentation':
        return { type: 'documentation', data: documentationData };
      case 'troubleshooting':
        return { type: 'troubleshooting', nodes: troubleshootingNodes, edges: troubleshootingEdges };
      case 'maintenance':
        return { type: 'maintenance', procedure: maintenanceProcedure };
    }
  };
  
  // Handle agent change
  const handleAgentChange = (agent: 'documentation' | 'troubleshooting' | 'maintenance') => {
    setActiveAgent(agent);
    
    // Simulate typing indicator
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      
      // Add a new message from the selected agent
      const newMessage = {
        id: `msg${messages.length + 1}`,
        source: 'agent' as const,
        agentType: agent,
        timestamp: new Date(),
        contents: [
          {
            type: 'text' as const,
            content: `This is a sample response from the ${agent} agent.`
          }
        ]
      };
      
      setMessages([...messages, newMessage]);
    }, 2000);
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Visualization Test Page
      </h1>
      
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Select Agent Type
        </h2>
        
        <div className="flex space-x-4">
          <Button
            variant={activeAgent === 'documentation' ? 'primary' : 'secondary'}
            onClick={() => handleAgentChange('documentation')}
          >
            Documentation Assistant
          </Button>
          
          <Button
            variant={activeAgent === 'troubleshooting' ? 'primary' : 'secondary'}
            onClick={() => handleAgentChange('troubleshooting')}
          >
            Troubleshooting Advisor
          </Button>
          
          <Button
            variant={activeAgent === 'maintenance' ? 'primary' : 'secondary'}
            onClick={() => handleAgentChange('maintenance')}
          >
            Maintenance Procedure Generator
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Agent Visualization
          </h2>
          
          <AdaptiveVisualization
            data={getVisualizationData()}
            className="mb-6"
          />
        </div>
        
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Conversation
          </h2>
          
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-medium text-gray-900 dark:text-white">
                Sample Conversation
              </h3>
            </div>
            
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
              {messages.map((message) => (
                <Message
                  key={message.id}
                  id={message.id}
                  source={message.source}
                  agentType={message.agentType}
                  timestamp={message.timestamp}
                  contents={message.contents}
                />
              ))}
              
              {isTyping && (
                <TypingIndicator
                  agentType={activeAgent}
                  message={`${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} agent is typing...`}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
