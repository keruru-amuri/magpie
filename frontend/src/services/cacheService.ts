/**
 * Cache Service for MAGPIE Platform
 * 
 * This service provides caching functionality for API responses to improve performance
 * and enable offline support.
 */

// Cache storage key prefix
const CACHE_PREFIX = 'magpie_cache_';

// Cache expiration time (in milliseconds)
const DEFAULT_CACHE_EXPIRATION = 24 * 60 * 60 * 1000; // 24 hours

// Cache entry interface
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiration: number;
}

/**
 * Set a cache entry
 * @param key Cache key
 * @param data Data to cache
 * @param expiration Cache expiration time in milliseconds (default: 24 hours)
 */
export function setCache<T>(key: string, data: T, expiration: number = DEFAULT_CACHE_EXPIRATION): void {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiration,
    };
    
    localStorage.setItem(cacheKey, JSON.stringify(entry));
  } catch (error) {
    console.error('Error setting cache:', error);
  }
}

/**
 * Get a cache entry
 * @param key Cache key
 * @returns Cached data or null if not found or expired
 */
export function getCache<T>(key: string): T | null {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (!cachedData) {
      return null;
    }
    
    const entry: CacheEntry<T> = JSON.parse(cachedData);
    const now = Date.now();
    
    // Check if cache is expired
    if (now - entry.timestamp > entry.expiration) {
      // Remove expired cache
      localStorage.removeItem(cacheKey);
      return null;
    }
    
    return entry.data;
  } catch (error) {
    console.error('Error getting cache:', error);
    return null;
  }
}

/**
 * Remove a cache entry
 * @param key Cache key
 */
export function removeCache(key: string): void {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    localStorage.removeItem(cacheKey);
  } catch (error) {
    console.error('Error removing cache:', error);
  }
}

/**
 * Clear all cache entries
 */
export function clearCache(): void {
  try {
    // Get all cache keys
    const cacheKeys = Object.keys(localStorage).filter(key => key.startsWith(CACHE_PREFIX));
    
    // Remove all cache entries
    cacheKeys.forEach(key => localStorage.removeItem(key));
  } catch (error) {
    console.error('Error clearing cache:', error);
  }
}

/**
 * Get all cache entries
 * @returns Object with all cache entries
 */
export function getAllCache(): Record<string, any> {
  try {
    const cacheKeys = Object.keys(localStorage).filter(key => key.startsWith(CACHE_PREFIX));
    const cache: Record<string, any> = {};
    
    cacheKeys.forEach(key => {
      const shortKey = key.replace(CACHE_PREFIX, '');
      const cachedData = localStorage.getItem(key);
      
      if (cachedData) {
        try {
          const entry = JSON.parse(cachedData);
          cache[shortKey] = entry.data;
        } catch (e) {
          console.error(`Error parsing cache for key ${key}:`, e);
        }
      }
    });
    
    return cache;
  } catch (error) {
    console.error('Error getting all cache:', error);
    return {};
  }
}

/**
 * Check if a cache entry exists and is not expired
 * @param key Cache key
 * @returns True if cache exists and is not expired
 */
export function hasValidCache(key: string): boolean {
  return getCache(key) !== null;
}

/**
 * Get cache entry with metadata
 * @param key Cache key
 * @returns Cache entry with metadata or null if not found
 */
export function getCacheWithMetadata<T>(key: string): CacheEntry<T> | null {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (!cachedData) {
      return null;
    }
    
    return JSON.parse(cachedData);
  } catch (error) {
    console.error('Error getting cache with metadata:', error);
    return null;
  }
}

/**
 * Update cache expiration time
 * @param key Cache key
 * @param expiration New expiration time in milliseconds
 * @returns True if cache was updated
 */
export function updateCacheExpiration(key: string, expiration: number): boolean {
  try {
    const cacheEntry = getCacheWithMetadata(key);
    
    if (!cacheEntry) {
      return false;
    }
    
    cacheEntry.expiration = expiration;
    
    const cacheKey = `${CACHE_PREFIX}${key}`;
    localStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
    
    return true;
  } catch (error) {
    console.error('Error updating cache expiration:', error);
    return false;
  }
}

// Export cache service
const cacheService = {
  set: setCache,
  get: getCache,
  remove: removeCache,
  clear: clearCache,
  getAll: getAllCache,
  hasValid: hasValidCache,
  getWithMetadata: getCacheWithMetadata,
  updateExpiration: updateCacheExpiration,
};

export default cacheService;
