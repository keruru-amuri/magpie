/**
 * API Service Tests
 *
 * This file contains tests for the API service.
 */

import { api } from '../../services/api';
import fetchMock from 'jest-fetch-mock';

// Mock fetch
fetchMock.enableMocks();

describe('API Service', () => {
  // Reset mocks before each test
  beforeEach(() => {
    fetchMock.resetMocks();
    localStorage.clear();
  });

  describe('Authentication', () => {
    test('login should make a POST request to /auth/login', async () => {
      // Mock response
      fetchMock.mockResponseOnce(JSON.stringify({
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        expires_in: 3600,
        user: {
          id: '123',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user'
        }
      }));

      // Call login
      const result = await api.auth.login({
        username: 'testuser',
        password: 'password'
      });

      // Check fetch was called with correct arguments
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            username: 'testuser',
            password: 'password'
          })
        })
      );

      // Parse result if it's a string
      const parsedResult = typeof result === 'string' ? JSON.parse(result) : result;

      // Check result contains expected properties
      expect(parsedResult).toHaveProperty('access_token', 'test-token');
      expect(parsedResult).toHaveProperty('refresh_token', 'test-refresh-token');
      expect(parsedResult).toHaveProperty('expires_in', 3600);
      expect(parsedResult).toHaveProperty('user');
      expect(parsedResult.user).toHaveProperty('id', '123');
      expect(parsedResult.user).toHaveProperty('username', 'testuser');
      expect(parsedResult.user).toHaveProperty('email', 'test@example.com');
      expect(parsedResult.user).toHaveProperty('role', 'user');
    });

    test('logout should make a POST request to /auth/logout', async () => {
      // Mock response
      fetchMock.mockResponseOnce(JSON.stringify({ success: true }));

      // Call logout
      await api.auth.logout();

      // Check fetch was called with correct arguments
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/logout'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  describe('Orchestrator', () => {
    test('query should make a POST request to /orchestrator/query', async () => {
      // Mock response
      fetchMock.mockResponseOnce(JSON.stringify({
        response: 'Test response',
        agentType: 'documentation',
        agentName: 'Documentation Agent',
        confidence: 0.9,
        conversationId: '123'
      }));

      // Call query
      const result = await api.orchestrator.query({
        query: 'test query',
        userId: '123'
      });

      // Check fetch was called with correct arguments
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/orchestrator/query'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            query: 'test query',
            userId: '123'
          })
        })
      );

      // Parse result if it's a string
      const parsedResult = typeof result === 'string' ? JSON.parse(result) : result;

      // Check result contains expected properties
      expect(parsedResult).toHaveProperty('response', 'Test response');
      expect(parsedResult).toHaveProperty('agentType', 'documentation');
      expect(parsedResult).toHaveProperty('agentName', 'Documentation Agent');
      expect(parsedResult).toHaveProperty('confidence', 0.9);
      expect(parsedResult).toHaveProperty('conversationId', '123');
    });
  });

  describe('Documentation', () => {
    test('search should make a GET request to /documentation/search', async () => {
      // Mock response
      fetchMock.mockResponseOnce(JSON.stringify({
        results: [
          {
            id: '123',
            title: 'Test Document',
            documentType: 'manual',
            aircraftModel: 'A320',
            system: 'hydraulic',
            relevanceScore: 0.9,
            snippet: 'Test snippet'
          }
        ],
        total: 1,
        query: 'test'
      }));

      // Call search
      const result = await api.documentation.search('test');

      // Check fetch was called with correct arguments
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/documentation/search?q=test'),
        expect.any(Object)
      );

      // Parse result if it's a string
      const parsedResult = typeof result === 'string' ? JSON.parse(result) : result;

      // Check result contains expected properties
      expect(parsedResult).toHaveProperty('results');
      expect(parsedResult).toHaveProperty('total', 1);
      expect(parsedResult).toHaveProperty('query', 'test');

      // Check results array
      expect(Array.isArray(parsedResult.results)).toBe(true);
      expect(parsedResult.results.length).toBe(1);

      // Check first result
      const firstResult = parsedResult.results[0];
      expect(firstResult).toHaveProperty('id', '123');
      expect(firstResult).toHaveProperty('title', 'Test Document');
      expect(firstResult).toHaveProperty('documentType', 'manual');
      expect(firstResult).toHaveProperty('aircraftModel', 'A320');
      expect(firstResult).toHaveProperty('system', 'hydraulic');
      expect(firstResult).toHaveProperty('relevanceScore', 0.9);
      expect(firstResult).toHaveProperty('snippet', 'Test snippet');
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors', async () => {
      // Mock error response
      fetchMock.mockResponseOnce(JSON.stringify({
        detail: 'Invalid credentials'
      }), { status: 401 });

      // Call login and expect it to throw
      await expect(api.auth.login({
        username: 'testuser',
        password: 'wrong-password'
      })).rejects.toEqual(expect.objectContaining({
        status: 401,
        message: 'Invalid credentials'
      }));
    });

    test('should retry on network errors', async () => {
      // Mock network error then success
      fetchMock.mockRejectOnce(new Error('Network error'));
      fetchMock.mockResponseOnce(JSON.stringify({ success: true }));

      // Call health check
      const result = await api.health.check();

      // Check fetch was called twice
      expect(fetchMock).toHaveBeenCalledTimes(2);

      // Parse result if it's a string
      const parsedResult = typeof result === 'string' ? JSON.parse(result) : result;

      // Check result has success property
      expect(parsedResult).toHaveProperty('success', true);
    });
  });
});
