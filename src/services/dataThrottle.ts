/**
 * Data Throttling Service
 * Prevents excessive API calls by caching responses and throttling requests
 */

interface CachedResponse<T = unknown> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class DataThrottleService {
  private cache = new Map<string, CachedResponse>();
  private pendingRequests = new Map<string, Promise<unknown>>();
  
  /**
   * Get data with caching and throttling
   * @param key - Unique identifier for the request
   * @param fetcher - Function that performs the actual API call
   * @param cacheDuration - How long to cache the response (ms)
   * @returns Promise with the data
   */
  async getData<T>(
    key: string, 
    fetcher: () => Promise<T>, 
    cacheDuration: number = 120000 // 2 minutes default
  ): Promise<T> {
    const now = Date.now();
    
    // Check if we have valid cached data
    const cached = this.cache.get(key);
    if (cached && now < cached.expiresAt) {
      return cached.data;
    }
    
    // Check if there's already a pending request for this key
    const pending = this.pendingRequests.get(key);
    if (pending) {
      return pending;
    }
    
    // Make the request
    const request = fetcher();
    this.pendingRequests.set(key, request);
    
    try {
      const data = await request;
      
      // Cache the response
      this.cache.set(key, {
        data,
        timestamp: now,
        expiresAt: now + cacheDuration
      });
      
      return data;
    } finally {
      // Remove from pending requests
      this.pendingRequests.delete(key);
    }
  }
  
  /**
   * Clear cache for a specific key or all cache
   */
  clearCache(key?: string) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
  
  /**
   * Get cache status for debugging
   */
  getCacheStatus() {
    const now = Date.now();
    const stats = {
      totalKeys: this.cache.size,
      validKeys: 0,
      expiredKeys: 0,
      pendingRequests: this.pendingRequests.size
    };
    
    this.cache.forEach((cached) => {
      if (now < cached.expiresAt) {
        stats.validKeys++;
      } else {
        stats.expiredKeys++;
      }
    });
    
    return stats;
  }
  
  /**
   * Clean up expired cache entries
   */
  cleanExpiredCache() {
    const now = Date.now();
    for (const [key, cached] of this.cache.entries()) {
      if (now >= cached.expiresAt) {
        this.cache.delete(key);
      }
    }
  }
}

// Singleton instance
export const dataThrottleService = new DataThrottleService();

// Clean up expired entries every 5 minutes
setInterval(() => {
  dataThrottleService.cleanExpiredCache();
}, 5 * 60 * 1000);