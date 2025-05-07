/**
 * Agent Service for MAGPIE Platform
 * 
 * This service provides functionality for interacting with different agent types
 * (documentation, troubleshooting, maintenance) and their specific APIs.
 */

import { api } from './api';
import { 
  DocumentSearchRequest, 
  DocumentSearchResponse, 
  Document, 
  TroubleshootingRequest, 
  TroubleshootingResponse,
  MaintenanceProcedureRequest,
  MaintenanceProcedure
} from '../types/api';
import analyticsService from './analyticsService';

// Documentation Agent Service
export const documentationAgent = {
  /**
   * Search for documents
   * @param query Search query
   * @returns Search results
   */
  search: async (query: string): Promise<DocumentSearchResponse> => {
    try {
      analyticsService.trackEvent('search', { query, agentType: 'documentation' });
      return await api.documentation.search(query);
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  },

  /**
   * Advanced search for documents
   * @param request Search request
   * @returns Search results
   */
  advancedSearch: async (request: DocumentSearchRequest): Promise<DocumentSearchResponse> => {
    try {
      analyticsService.trackEvent('advanced_search', { 
        query: request.query, 
        filters: request.filters,
        agentType: 'documentation' 
      });
      return await api.documentation.advancedSearch(request);
    } catch (error) {
      console.error('Error performing advanced search:', error);
      throw error;
    }
  },

  /**
   * Get document by ID
   * @param id Document ID
   * @returns Document
   */
  getDocument: async (id: string): Promise<Document> => {
    try {
      analyticsService.trackEvent('document_view', { documentId: id });
      return await api.documentation.getDocument(id);
    } catch (error) {
      console.error(`Error getting document ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get recent documents
   * @returns Recent documents
   */
  getRecentDocuments: async (): Promise<Document[]> => {
    try {
      return await api.documentation.getRecentDocuments();
    } catch (error) {
      console.error('Error getting recent documents:', error);
      throw error;
    }
  },

  /**
   * Get popular documents
   * @returns Popular documents
   */
  getPopularDocuments: async (): Promise<Document[]> => {
    try {
      return await api.documentation.getPopularDocuments();
    } catch (error) {
      console.error('Error getting popular documents:', error);
      throw error;
    }
  },

  /**
   * Get cross-references for a document
   * @param documentId Document ID
   * @returns Cross-references
   */
  getCrossReferences: async (documentId: string): Promise<Document[]> => {
    try {
      return await api.documentation.getCrossReferences(documentId);
    } catch (error) {
      console.error(`Error getting cross-references for document ${documentId}:`, error);
      throw error;
    }
  }
};

// Troubleshooting Agent Service
export const troubleshootingAgent = {
  /**
   * Analyze a problem
   * @param problem Problem description
   * @returns Troubleshooting response
   */
  analyze: async (problem: TroubleshootingRequest): Promise<TroubleshootingResponse> => {
    try {
      analyticsService.trackEvent('troubleshooting_analyze', { 
        problem: problem.problem,
        aircraftModel: problem.aircraftModel,
        system: problem.system,
        agentType: 'troubleshooting'
      });
      return await api.troubleshooting.analyze(problem);
    } catch (error) {
      console.error('Error analyzing problem:', error);
      throw error;
    }
  },

  /**
   * Get solutions for a problem
   * @param problemId Problem ID
   * @returns Troubleshooting solutions
   */
  getSolutions: async (problemId: string): Promise<TroubleshootingResponse> => {
    try {
      analyticsService.trackEvent('troubleshooting_solutions', { problemId });
      return await api.troubleshooting.getSolutions(problemId);
    } catch (error) {
      console.error(`Error getting solutions for problem ${problemId}:`, error);
      throw error;
    }
  },

  /**
   * Get step details
   * @param problemId Problem ID
   * @param stepId Step ID
   * @returns Step details
   */
  getStepDetails: async (problemId: string, stepId: string): Promise<any> => {
    try {
      analyticsService.trackEvent('troubleshooting_step_details', { problemId, stepId });
      return await api.troubleshooting.getStepDetails(problemId, stepId);
    } catch (error) {
      console.error(`Error getting step details for problem ${problemId}, step ${stepId}:`, error);
      throw error;
    }
  },

  /**
   * Update step status
   * @param problemId Problem ID
   * @param stepId Step ID
   * @param status Step status
   * @returns Updated step
   */
  updateStepStatus: async (problemId: string, stepId: string, status: string): Promise<any> => {
    try {
      analyticsService.trackEvent('troubleshooting_step_update', { problemId, stepId, status });
      return await api.troubleshooting.updateStepStatus(problemId, stepId, status);
    } catch (error) {
      console.error(`Error updating step status for problem ${problemId}, step ${stepId}:`, error);
      throw error;
    }
  },

  /**
   * Get similar problems
   * @param problemId Problem ID
   * @returns Similar problems
   */
  getSimilarProblems: async (problemId: string): Promise<any[]> => {
    try {
      return await api.troubleshooting.getSimilarProblems(problemId);
    } catch (error) {
      console.error(`Error getting similar problems for ${problemId}:`, error);
      throw error;
    }
  }
};

// Maintenance Agent Service
export const maintenanceAgent = {
  /**
   * Generate maintenance procedure
   * @param params Procedure parameters
   * @returns Maintenance procedure
   */
  generateProcedure: async (params: MaintenanceProcedureRequest): Promise<MaintenanceProcedure> => {
    try {
      analyticsService.trackEvent('maintenance_generate', { 
        equipment: params.equipment,
        task: params.task,
        agentType: 'maintenance'
      });
      return await api.maintenance.generateProcedure(params);
    } catch (error) {
      console.error('Error generating maintenance procedure:', error);
      throw error;
    }
  },

  /**
   * Get procedure by ID
   * @param id Procedure ID
   * @returns Maintenance procedure
   */
  getProcedure: async (id: string): Promise<MaintenanceProcedure> => {
    try {
      analyticsService.trackEvent('maintenance_view', { procedureId: id });
      return await api.maintenance.getProcedure(id);
    } catch (error) {
      console.error(`Error getting maintenance procedure ${id}:`, error);
      throw error;
    }
  },

  /**
   * Update step status
   * @param procedureId Procedure ID
   * @param stepId Step ID
   * @param completed Whether step is completed
   * @returns Updated step
   */
  updateStepStatus: async (procedureId: string, stepId: string, completed: boolean): Promise<any> => {
    try {
      analyticsService.trackEvent('maintenance_step_update', { procedureId, stepId, completed });
      return await api.maintenance.updateStepStatus(procedureId, stepId, completed);
    } catch (error) {
      console.error(`Error updating step status for procedure ${procedureId}, step ${stepId}:`, error);
      throw error;
    }
  },

  /**
   * Get tools and parts for a procedure
   * @param procedureId Procedure ID
   * @returns Tools and parts
   */
  getToolsAndParts: async (procedureId: string): Promise<any> => {
    try {
      return await api.maintenance.getToolsAndParts(procedureId);
    } catch (error) {
      console.error(`Error getting tools and parts for procedure ${procedureId}:`, error);
      throw error;
    }
  },

  /**
   * Get safety precautions for a procedure
   * @param procedureId Procedure ID
   * @returns Safety precautions
   */
  getSafetyPrecautions: async (procedureId: string): Promise<any[]> => {
    try {
      return await api.maintenance.getSafetyPrecautions(procedureId);
    } catch (error) {
      console.error(`Error getting safety precautions for procedure ${procedureId}:`, error);
      throw error;
    }
  }
};

// Export agent services
const agentService = {
  documentation: documentationAgent,
  troubleshooting: troubleshootingAgent,
  maintenance: maintenanceAgent
};

export default agentService;
