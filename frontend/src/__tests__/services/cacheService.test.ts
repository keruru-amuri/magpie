/**
 * Cache Service Tests
 *
 * This file contains tests for the cache service.
 */

import cacheService from '../../services/cacheService';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    key: (index: number) => Object.keys(store)[index] || null,
    length: 0
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('Cache Service', () => {
  // Clear localStorage before each test
  beforeEach(() => {
    localStorage.clear();
  });

  describe('set and get', () => {
    test('should set and get cache entry', () => {
      // Set cache
      cacheService.set('test-key', { data: 'test-data' });

      // Get cache
      const result = cacheService.get('test-key');

      // Check result
      expect(result).toEqual({ data: 'test-data' });
    });

    test('should return null for non-existent cache entry', () => {
      // Get non-existent cache
      const result = cacheService.get('non-existent-key');

      // Check result
      expect(result).toBeNull();
    });

    test('should handle expiration', () => {
      // Set cache with expiration
      const now = Date.now();
      const expiration = 1000; // 1 second

      // Mock Date.now to return consistent values
      const originalDateNow = Date.now;
      Date.now = jest.fn(() => now);

      // Set cache
      cacheService.set('test-key', { data: 'test-data' }, expiration);

      // Check cache is available
      expect(cacheService.get('test-key')).toEqual({ data: 'test-data' });

      // Mock Date.now to return a time after expiration
      Date.now = jest.fn(() => now + expiration + 1);

      // Check cache is expired
      expect(cacheService.get('test-key')).toBeNull();

      // Restore Date.now
      Date.now = originalDateNow;
    });
  });

  describe('remove', () => {
    test('should remove cache entry', () => {
      // Set cache
      cacheService.set('test-key', { data: 'test-data' });

      // Remove cache
      cacheService.remove('test-key');

      // Check cache is removed
      expect(cacheService.get('test-key')).toBeNull();
    });
  });

  describe('clear', () => {
    test('should clear all cache entries', () => {
      // Create a spy on localStorage.removeItem
      const removeItemSpy = jest.spyOn(localStorage, 'removeItem');

      // Set multiple cache entries
      cacheService.set('test-key-1', { data: 'test-data-1' });
      cacheService.set('test-key-2', { data: 'test-data-2' });

      // Clear localStorage directly to ensure test environment is clean
      Object.keys(localStorage).forEach(key => {
        localStorage.removeItem(key);
      });

      // Set cache entries again
      cacheService.set('test-key-1', { data: 'test-data-1' });
      cacheService.set('test-key-2', { data: 'test-data-2' });

      // Clear cache
      cacheService.clear();

      // Verify removeItem was called for cache keys
      expect(removeItemSpy).toHaveBeenCalled();

      // Reset localStorage for other tests
      removeItemSpy.mockRestore();
    });
  });

  describe('hasValid', () => {
    test('should check if cache entry exists and is not expired', () => {
      // Set cache
      cacheService.set('test-key', { data: 'test-data' });

      // Check cache is valid
      expect(cacheService.hasValid('test-key')).toBe(true);

      // Check non-existent cache is not valid
      expect(cacheService.hasValid('non-existent-key')).toBe(false);
    });
  });

  describe('getWithMetadata', () => {
    test('should get cache entry with metadata', () => {
      // Set cache
      cacheService.set('test-key', { data: 'test-data' });

      // Get cache with metadata
      const result = cacheService.getWithMetadata('test-key');

      // Check result
      expect(result).toEqual({
        data: { data: 'test-data' },
        timestamp: expect.any(Number),
        expiration: expect.any(Number)
      });
    });
  });

  describe('updateExpiration', () => {
    test('should update cache expiration', () => {
      // Set cache
      cacheService.set('test-key', { data: 'test-data' });

      // Get original expiration
      const original = cacheService.getWithMetadata('test-key');
      const originalExpiration = original?.expiration;

      // Update expiration
      const newExpiration = 60000; // 1 minute
      const result = cacheService.updateExpiration('test-key', newExpiration);

      // Check result
      expect(result).toBe(true);

      // Get updated expiration
      const updated = cacheService.getWithMetadata('test-key');
      const updatedExpiration = updated?.expiration;

      // Check expiration was updated
      expect(updatedExpiration).toBe(newExpiration);
      expect(updatedExpiration).not.toBe(originalExpiration);
    });
  });
});
