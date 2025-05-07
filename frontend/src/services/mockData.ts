/**
 * Mock Data Service for MAGPIE Platform
 *
 * This service provides mock data for API requests when real backend is not available.
 */

import {
  LoginResponse,
  OrchestratorResponse,
  DocumentSearchResponse,
  Document,
  TroubleshootingResponse,
  MaintenanceProcedure
} from '../types/api';

/**
 * Get mock response for an API request
 * @param endpoint API endpoint
 * @param method HTTP method
 * @param data Request data
 * @returns Mock response
 */
export function getMockResponse(endpoint: string, method: string, data?: any): any {
  // Authentication endpoints
  if (endpoint.includes('/auth/login')) {
    return getMockLoginResponse(data);
  }

  if (endpoint.includes('/auth/logout')) {
    return { success: true };
  }

  if (endpoint.includes('/auth/user')) {
    return getMockUserResponse();
  }

  // Orchestrator endpoints
  if (endpoint.includes('/orchestrator/query')) {
    return getMockOrchestratorResponse(data);
  }

  if (endpoint.includes('/orchestrator/routing')) {
    return getMockRoutingResponse(data);
  }

  // Documentation endpoints
  if (endpoint.includes('/documentation/search')) {
    return getMockDocumentSearchResponse(data);
  }

  if (endpoint.includes('/documentation/documents/')) {
    const id = endpoint.split('/').pop();
    return getMockDocumentResponse(id);
  }

  if (endpoint.includes('/documentation/recent')) {
    return getMockRecentDocumentsResponse();
  }

  if (endpoint.includes('/documentation/popular')) {
    return getMockPopularDocumentsResponse();
  }

  // Troubleshooting endpoints
  if (endpoint.includes('/troubleshooting/analyze')) {
    return getMockTroubleshootingResponse(data);
  }

  if (endpoint.includes('/troubleshooting/solutions/')) {
    const id = endpoint.split('/').pop();
    return getMockTroubleshootingSolutionsResponse(id);
  }

  // Maintenance endpoints
  if (endpoint.includes('/maintenance/generate')) {
    return getMockMaintenanceProcedureResponse(data);
  }

  if (endpoint.includes('/maintenance/procedures/')) {
    const id = endpoint.split('/').pop();
    return getMockMaintenanceProcedureByIdResponse(id);
  }

  // Chat endpoints
  if (endpoint.includes('/chat/conversations') && method === 'GET') {
    return getMockConversationsResponse();
  }

  if (endpoint.includes('/chat/conversations/') && method === 'GET') {
    const id = endpoint.split('/').pop();
    return getMockConversationResponse(id);
  }

  if (endpoint.includes('/chat/conversations') && method === 'POST') {
    return getMockCreateConversationResponse(data);
  }

  // Health endpoints
  if (endpoint.includes('/health')) {
    return getMockHealthResponse();
  }

  // Default response
  return { message: 'Mock data not available for this endpoint' };
}

/**
 * Get mock login response
 * @param data Login request data
 * @returns Mock login response
 */
function getMockLoginResponse(data: any): LoginResponse {
  return {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    expires_in: 3600,
    user: {
      id: 'user-123',
      username: data?.username || 'mockuser',
      email: `${data?.username || 'mockuser'}@example.com`,
      role: 'user',
      firstName: 'Mock',
      lastName: 'User',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  };
}

/**
 * Get mock user response
 * @returns Mock user response
 */
function getMockUserResponse(): any {
  return {
    id: 'user-123',
    username: 'mockuser',
    email: 'mockuser@example.com',
    role: 'user',
    firstName: 'Mock',
    lastName: 'User',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    preferences: {
      theme: 'system',
      notifications: {
        email: true,
        inApp: true
      }
    }
  };
}

/**
 * Get mock orchestrator response
 * @param data Orchestrator request data
 * @returns Mock orchestrator response
 */
function getMockOrchestratorResponse(data: any): OrchestratorResponse {
  // Determine agent type based on query
  let agentType = 'documentation';
  let confidence = 0.8;

  const query = data?.query?.toLowerCase() || '';

  if (query.includes('troubleshoot') || query.includes('problem') || query.includes('issue') || query.includes('error')) {
    agentType = 'troubleshooting';
    confidence = 0.9;
  } else if (query.includes('maintenance') || query.includes('procedure') || query.includes('repair') || query.includes('replace')) {
    agentType = 'maintenance';
    confidence = 0.85;
  }

  return {
    response: `This is a mock response to: "${data?.query}"`,
    agentType,
    agentName: `${agentType.charAt(0).toUpperCase() + agentType.slice(1)} Agent`,
    confidence,
    conversationId: data?.conversationId || `conv-${Date.now()}`,
    messageId: `msg-${Date.now()}`
  };
}

/**
 * Get mock routing response
 * @param data Routing request data
 * @returns Mock routing response
 */
function getMockRoutingResponse(data: any): any {
  // Determine agent type based on query
  let agentType = 'documentation';
  let confidence = 0.8;

  const query = data?.query?.toLowerCase() || '';

  if (query.includes('troubleshoot') || query.includes('problem') || query.includes('issue') || query.includes('error')) {
    agentType = 'troubleshooting';
    confidence = 0.9;
  } else if (query.includes('maintenance') || query.includes('procedure') || query.includes('repair') || query.includes('replace')) {
    agentType = 'maintenance';
    confidence = 0.85;
  }

  return {
    agentType,
    confidence,
    reasoning: `Query "${data?.query}" appears to be a ${agentType} request.`
  };
}

/**
 * Get mock document search response
 * @param data Search request data
 * @returns Mock document search response
 */
function getMockDocumentSearchResponse(data: any): DocumentSearchResponse {
  const query = typeof data === 'string' ? data : data?.query || '';

  return {
    results: [
      {
        id: 'doc-1',
        title: 'Aircraft Maintenance Manual',
        documentType: 'manual',
        aircraftModel: 'A320',
        system: 'hydraulic',
        relevanceScore: 0.95,
        snippet: `This section describes the hydraulic system for the A320 aircraft. ${query}`
      },
      {
        id: 'doc-2',
        title: 'Component Maintenance Manual',
        documentType: 'manual',
        aircraftModel: 'A320',
        system: 'electrical',
        relevanceScore: 0.85,
        snippet: `Electrical system components and maintenance procedures. ${query}`
      },
      {
        id: 'doc-3',
        title: 'Service Bulletin',
        documentType: 'bulletin',
        aircraftModel: 'A320',
        system: 'avionics',
        relevanceScore: 0.75,
        snippet: `Service bulletin for avionics system updates. ${query}`
      }
    ],
    total: 3,
    query
  };
}

/**
 * Get mock document response
 * @param id Document ID
 * @returns Mock document
 */
function getMockDocumentResponse(id: string | undefined): Document {
  return {
    id: id || 'doc-1',
    title: 'Aircraft Maintenance Manual',
    documentType: 'manual',
    aircraftModel: 'A320',
    system: 'hydraulic',
    content: 'This is a mock document content for the Aircraft Maintenance Manual.',
    sections: [
      {
        id: 'section-1',
        title: 'Introduction',
        content: 'Introduction to the hydraulic system.'
      },
      {
        id: 'section-2',
        title: 'Components',
        content: 'Description of hydraulic system components.'
      },
      {
        id: 'section-3',
        title: 'Maintenance',
        content: 'Maintenance procedures for the hydraulic system.'
      }
    ],
    metadata: {
      author: 'Airbus',
      version: '1.0',
      lastUpdated: new Date().toISOString(),
      tags: ['hydraulic', 'maintenance', 'A320']
    }
  };
}

/**
 * Get mock recent documents response
 * @returns Mock recent documents
 */
function getMockRecentDocumentsResponse(): Document[] {
  return [
    {
      id: 'doc-1',
      title: 'Aircraft Maintenance Manual',
      documentType: 'manual',
      aircraftModel: 'A320',
      system: 'hydraulic',
      content: 'This is a mock document content for the Aircraft Maintenance Manual.',
      metadata: {
        author: 'Airbus',
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        tags: ['hydraulic', 'maintenance', 'A320']
      }
    },
    {
      id: 'doc-2',
      title: 'Component Maintenance Manual',
      documentType: 'manual',
      aircraftModel: 'A320',
      system: 'electrical',
      content: 'This is a mock document content for the Component Maintenance Manual.',
      metadata: {
        author: 'Airbus',
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        tags: ['electrical', 'maintenance', 'A320']
      }
    }
  ];
}

/**
 * Get mock popular documents response
 * @returns Mock popular documents
 */
function getMockPopularDocumentsResponse(): Document[] {
  return [
    {
      id: 'doc-3',
      title: 'Service Bulletin',
      documentType: 'bulletin',
      aircraftModel: 'A320',
      system: 'avionics',
      content: 'This is a mock document content for the Service Bulletin.',
      metadata: {
        author: 'Airbus',
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        tags: ['avionics', 'bulletin', 'A320']
      }
    },
    {
      id: 'doc-4',
      title: 'Troubleshooting Guide',
      documentType: 'guide',
      aircraftModel: 'A320',
      system: 'landing gear',
      content: 'This is a mock document content for the Troubleshooting Guide.',
      metadata: {
        author: 'Airbus',
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        tags: ['landing gear', 'troubleshooting', 'A320']
      }
    }
  ];
}

/**
 * Get mock troubleshooting response
 * @param data Troubleshooting request data
 * @returns Mock troubleshooting response
 */
function getMockTroubleshootingResponse(data: any): TroubleshootingResponse {
  return {
    analysis: {
      possibleCauses: [
        {
          id: 'cause-1',
          description: 'Faulty pressure sensor',
          probability: 0.8,
          evidence: 'Fluctuating pressure readings'
        },
        {
          id: 'cause-2',
          description: 'Damaged wiring harness',
          probability: 0.6,
          evidence: 'Intermittent electrical signals'
        }
      ],
      recommendedActions: [
        {
          id: 'action-1',
          description: 'Replace pressure sensor',
          priority: 'high',
          estimatedTime: '2 hours',
          requiredParts: ['Pressure sensor P/N 123456']
        },
        {
          id: 'action-2',
          description: 'Inspect wiring harness',
          priority: 'medium',
          estimatedTime: '1 hour',
          requiredTools: ['Multimeter', 'Wire stripper']
        }
      ]
    },
    symptoms: data?.symptoms || ['Fluctuating pressure readings', 'System warnings'],
    systemAffected: data?.system || 'hydraulic',
    aircraftModel: data?.aircraftModel || 'A320',
    confidence: 0.85
  };
}

/**
 * Get mock troubleshooting solutions response
 * @param id Troubleshooting ID
 * @returns Mock troubleshooting solutions
 */
function getMockTroubleshootingSolutionsResponse(id: string | undefined): any {
  return {
    id: id || 'troubleshooting-1',
    title: 'Hydraulic System Pressure Issues',
    solutions: [
      {
        id: 'solution-1',
        title: 'Replace Pressure Sensor',
        steps: [
          'Ensure aircraft is powered down',
          'Access the hydraulic bay',
          'Disconnect electrical connections',
          'Remove and replace sensor',
          'Reconnect electrical connections',
          'Perform system test'
        ],
        requiredParts: ['Pressure sensor P/N 123456'],
        requiredTools: ['Socket set', 'Torque wrench'],
        estimatedTime: '2 hours',
        difficulty: 'medium'
      },
      {
        id: 'solution-2',
        title: 'Repair Wiring Harness',
        steps: [
          'Ensure aircraft is powered down',
          'Access the hydraulic bay',
          'Inspect wiring harness for damage',
          'Repair or replace damaged sections',
          'Perform continuity test',
          'Reconnect and secure wiring',
          'Perform system test'
        ],
        requiredParts: ['Wire harness repair kit'],
        requiredTools: ['Multimeter', 'Wire stripper', 'Heat shrink gun'],
        estimatedTime: '3 hours',
        difficulty: 'high'
      }
    ]
  };
}

/**
 * Get mock maintenance procedure response
 * @param data Maintenance procedure request data
 * @returns Mock maintenance procedure
 */
function getMockMaintenanceProcedureResponse(data: any): MaintenanceProcedure {
  return {
    id: `procedure-${Date.now()}`,
    title: data?.title || 'Hydraulic System Maintenance',
    aircraftModel: data?.aircraftModel || 'A320',
    system: data?.system || 'hydraulic',
    estimatedTime: '4 hours',
    skillLevel: 'certified technician',
    steps: [
      {
        id: 'step-1',
        title: 'Preparation',
        description: 'Ensure aircraft is powered down and properly secured.',
        estimatedTime: '30 minutes',
        warnings: ['Ensure all power sources are disconnected'],
        images: []
      },
      {
        id: 'step-2',
        title: 'Access Hydraulic Bay',
        description: 'Open access panels to reach the hydraulic system components.',
        estimatedTime: '15 minutes',
        tools: ['Screwdriver set'],
        images: []
      },
      {
        id: 'step-3',
        title: 'Inspect Components',
        description: 'Visually inspect all hydraulic components for leaks or damage.',
        estimatedTime: '45 minutes',
        tools: ['Flashlight', 'Inspection mirror'],
        images: []
      },
      {
        id: 'step-4',
        title: 'Replace Filters',
        description: 'Remove and replace hydraulic filters according to maintenance schedule.',
        estimatedTime: '1 hour',
        tools: ['Filter wrench', 'Torque wrench'],
        parts: ['Hydraulic filter kit P/N 789012'],
        images: []
      },
      {
        id: 'step-5',
        title: 'System Test',
        description: 'Perform operational test of the hydraulic system.',
        estimatedTime: '1 hour',
        tools: ['Hydraulic pressure gauge'],
        warnings: ['Ensure all personnel are clear of moving surfaces'],
        images: []
      },
      {
        id: 'step-6',
        title: 'Close Access Panels',
        description: 'Replace and secure all access panels.',
        estimatedTime: '30 minutes',
        tools: ['Screwdriver set', 'Torque wrench'],
        images: []
      }
    ],
    requiredTools: [
      'Screwdriver set',
      'Torque wrench',
      'Filter wrench',
      'Flashlight',
      'Inspection mirror',
      'Hydraulic pressure gauge'
    ],
    requiredParts: ['Hydraulic filter kit P/N 789012'],
    safetyPrecautions: [
      'Ensure aircraft is properly grounded',
      'Wear appropriate PPE including gloves and eye protection',
      'Follow all standard safety procedures for hydraulic system maintenance'
    ],
    references: [
      'Aircraft Maintenance Manual Chapter 29',
      'Component Maintenance Manual for Hydraulic Filters'
    ]
  };
}

/**
 * Get mock maintenance procedure by ID response
 * @param id Procedure ID
 * @returns Mock maintenance procedure
 */
function getMockMaintenanceProcedureByIdResponse(id: string | undefined): MaintenanceProcedure {
  return {
    id: id || 'procedure-1',
    title: 'Hydraulic System Maintenance',
    aircraftModel: 'A320',
    system: 'hydraulic',
    estimatedTime: '4 hours',
    skillLevel: 'certified technician',
    steps: [
      {
        id: 'step-1',
        title: 'Preparation',
        description: 'Ensure aircraft is powered down and properly secured.',
        estimatedTime: '30 minutes',
        warnings: ['Ensure all power sources are disconnected'],
        images: []
      },
      {
        id: 'step-2',
        title: 'Access Hydraulic Bay',
        description: 'Open access panels to reach the hydraulic system components.',
        estimatedTime: '15 minutes',
        tools: ['Screwdriver set'],
        images: []
      }
    ],
    requiredTools: [
      'Screwdriver set',
      'Torque wrench',
      'Filter wrench',
      'Flashlight',
      'Inspection mirror',
      'Hydraulic pressure gauge'
    ],
    requiredParts: ['Hydraulic filter kit P/N 789012'],
    safetyPrecautions: [
      'Ensure aircraft is properly grounded',
      'Wear appropriate PPE including gloves and eye protection',
      'Follow all standard safety procedures for hydraulic system maintenance'
    ],
    references: [
      'Aircraft Maintenance Manual Chapter 29',
      'Component Maintenance Manual for Hydraulic Filters'
    ]
  };
}

/**
 * Get mock conversations response
 * @returns Mock conversations
 */
function getMockConversationsResponse(): any {
  return [
    {
      id: 'conv-1',
      title: 'Hydraulic System Troubleshooting',
      agentType: 'troubleshooting',
      createdAt: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      updatedAt: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      messageCount: 5
    },
    {
      id: 'conv-2',
      title: 'A320 Maintenance Manual Query',
      agentType: 'documentation',
      createdAt: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
      updatedAt: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
      messageCount: 3
    },
    {
      id: 'conv-3',
      title: 'Landing Gear Maintenance Procedure',
      agentType: 'maintenance',
      createdAt: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
      updatedAt: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
      messageCount: 7
    }
  ];
}

/**
 * Get mock conversation response
 * @param id Conversation ID
 * @returns Mock conversation
 */
function getMockConversationResponse(id: string | undefined): any {
  return {
    id: id || 'conv-1',
    title: 'Hydraulic System Troubleshooting',
    agentType: 'troubleshooting',
    createdAt: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    updatedAt: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    messages: [
      {
        id: 'msg-1',
        content: 'I\'m experiencing issues with the hydraulic system pressure fluctuating during flight.',
        role: 'user',
        timestamp: new Date(Date.now() - 86400000).toISOString() // 1 day ago
      },
      {
        id: 'msg-2',
        content: 'I\'ll help you troubleshoot this issue. Can you provide more details about when the fluctuations occur and any warning messages you\'re seeing?',
        role: 'assistant',
        agentType: 'troubleshooting',
        timestamp: new Date(Date.now() - 86390000).toISOString() // 1 day ago - 10 seconds
      },
      {
        id: 'msg-3',
        content: 'The fluctuations occur during cruise phase and we\'re seeing intermittent "HYD SYS PRESS" warnings.',
        role: 'user',
        timestamp: new Date(Date.now() - 86300000).toISOString() // 1 day ago - 100 seconds
      },
      {
        id: 'msg-4',
        content: 'Based on your description, this could be related to a faulty pressure sensor or damaged wiring harness. I recommend checking the pressure sensor connections and inspecting the wiring for any damage.',
        role: 'assistant',
        agentType: 'troubleshooting',
        timestamp: new Date(Date.now() - 86290000).toISOString() // 1 day ago - 110 seconds
      },
      {
        id: 'msg-5',
        content: 'Thanks, I\'ll check those components and report back.',
        role: 'user',
        timestamp: new Date(Date.now() - 3610000).toISOString() // 1 hour ago - 10 seconds
      }
    ]
  };
}

/**
 * Get mock create conversation response
 * @param data Create conversation request data
 * @returns Mock create conversation response
 */
function getMockCreateConversationResponse(data: any): any {
  const uniqueId = `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  return {
    id: uniqueId,
    title: data?.title || 'New Conversation',
    agentType: data?.agentType || 'documentation',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: []
  };
}

/**
 * Get mock health response
 * @returns Mock health response
 */
function getMockHealthResponse(): any {
  return {
    status: 'ok',
    version: '1.0.0',
    uptime: 12345,
    timestamp: new Date().toISOString()
  };
}

// Export mock data functions
export default {
  getMockResponse
};
