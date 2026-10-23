import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SecurityMiddleware, DEFAULT_SECURITY_CONFIG, CircuitBreakerState, createSecurityMiddleware } from '@/security/middleware';

// Test utilities
interface TestContext {
  clientId: string;
  requestId: string;
  timestamp: number;
  requestSize?: number;
  is5xx?: boolean;
  latencyMs?: number;
}

function createTestContext(overrides: Partial<TestContext> = {}): TestContext {
  return {
    clientId: 'test-client',
    requestId: `req-${Date.now()}`,
    timestamp: Date.now(),
    ...overrides,
  };
}

function createMiddleware(config: Partial<typeof DEFAULT_SECURITY_CONFIG> = {}) {
  return createSecurityMiddleware(config);
}

describe('SecurityMiddleware - workersHardening Contract', () => {
  let middleware: SecurityMiddleware;

  beforeEach(() => {
    middleware = createMiddleware();
  });

  describe('Circuit Breaker', () => {
    it('should start in CLOSED state', () => {
      const state = middleware.getCircuitBreakerState();
      expect(state).toBe(CircuitBreakerState.CLOSED);
    });

    it('should trip to OPEN when 5xx rate exceeds 50%', async () => {
      // First 10 requests: 6 are 5xx (60% rate)
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test',
          requestId: `cb-${i}`,
          timestamp: Date.now() + i,
        });
        await middleware.checkRequest('', context);
        // Record response based on is5xx
        middleware.recordResponse(i < 6 ? 500 : 200);
      }

      const state = middleware.getCircuitBreakerState();
      expect(state).toBe(CircuitBreakerState.OPEN);
    });

    it('should stay CLOSED when 5xx rate is below 50%', async () => {
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test-2',
          requestId: `cb2-${i}`,
          timestamp: Date.now() + i,
        });
        await middleware.checkRequest('', context);
        // Record response - 40% 5xx rate
        middleware.recordResponse(i < 4 ? 500 : 200);
      }

      const state = middleware.getCircuitBreakerState();
      expect(state).toBe(CircuitBreakerState.CLOSED);
    });

    it('should reject requests when OPEN', async () => {
      // Trip the circuit breaker
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test-3',
          requestId: `cb3-${i}`,
          timestamp: Date.now() + i,
        });
        await middleware.checkRequest('', context);
        middleware.recordResponse(500);
      }

      // Next request should be rejected
      const context = createTestContext({ clientId: 'cb-test-3', requestId: 'cb3-rejected', timestamp: Date.now() + 11 });
      const result = await middleware.checkRequest('', context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('circuit breaker');
    });

    it('should transition to HALF_OPEN after timeout', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          circuitBreaker: {
            ...DEFAULT_SECURITY_CONFIG.workersHardening.circuitBreaker,
            halfOpenTimeoutMs: 10, // Very short for testing
          },
        },
      });

      // Trip the circuit breaker with test middleware
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test-5',
          requestId: `cb5-${i}`,
          timestamp: Date.now() + i,
        });
        await testMiddleware.checkRequest('', context);
        testMiddleware.recordResponse(500);
      }

      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.OPEN);

      // Wait for half-open transition
      await new Promise(resolve => setTimeout(resolve, 20));

      // Make a request to trigger the state transition
      const context = createTestContext({ clientId: 'cb-test-5', requestId: 'cb5-trigger', timestamp: Date.now() + 30 });
      await testMiddleware.checkRequest('', context);

      const state = testMiddleware.getCircuitBreakerState();
      expect(state).toBe(CircuitBreakerState.HALF_OPEN);
    });

    it('should close circuit breaker on successful requests in HALF_OPEN', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          circuitBreaker: {
            ...DEFAULT_SECURITY_CONFIG.workersHardening.circuitBreaker,
            halfOpenTimeoutMs: 10,
            halfOpenRequests: 3,
          },
        },
      });

      // Trip the circuit breaker
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test-6',
          requestId: `cb6-${i}`,
          timestamp: Date.now() + i,
        });
        await testMiddleware.checkRequest('', context);
        testMiddleware.recordResponse(500);
      }

      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.OPEN);

      // Wait for HALF_OPEN
      await new Promise(resolve => setTimeout(resolve, 20));
      const context = createTestContext({ clientId: 'cb-test-6', requestId: 'cb6-trigger', timestamp: Date.now() + 30 });
      await testMiddleware.checkRequest('', context);

      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.HALF_OPEN);

      // Make 3 successful requests (halfOpenRequests = 3)
      for (let i = 0; i < 3; i++) {
        const successContext = createTestContext({ clientId: 'cb-test-6', requestId: `cb6-success-${i}`, timestamp: Date.now() + 40 + i });
        await testMiddleware.checkRequest('', successContext);
        testMiddleware.recordResponse(200);
      }

      // Should be CLOSED now
      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.CLOSED);
    });

    it('should reopen circuit breaker on failure in HALF_OPEN', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          circuitBreaker: {
            ...DEFAULT_SECURITY_CONFIG.workersHardening.circuitBreaker,
            halfOpenTimeoutMs: 10,
            halfOpenRequests: 3,
          },
        },
      });

      // Trip the circuit breaker
      for (let i = 0; i < 10; i++) {
        const context = createTestContext({
          clientId: 'cb-test-7',
          requestId: `cb7-${i}`,
          timestamp: Date.now() + i,
        });
        await testMiddleware.checkRequest('', context);
        testMiddleware.recordResponse(500);
      }

      await new Promise(resolve => setTimeout(resolve, 20));
      await testMiddleware.checkRequest('', createTestContext({ clientId: 'cb-test-7', requestId: 'cb7-trigger', timestamp: Date.now() + 30 }));

      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.HALF_OPEN);

      // Make a failure in HALF_OPEN
      const failContext = createTestContext({ clientId: 'cb-test-7', requestId: 'cb7-fail', timestamp: Date.now() + 40 });
      await testMiddleware.checkRequest('', failContext);
      testMiddleware.recordResponse(500);

      // Should reopen
      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.OPEN);
    });

    it('should use sliding window for 5xx rate calculation', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          circuitBreaker: {
            ...DEFAULT_SECURITY_CONFIG.workersHardening.circuitBreaker,
            windowMs: 50, // Very short window for testing
            halfOpenTimeoutMs: 10, // Very short for testing
          },
        },
      });

      // First 10 requests all 5xx
      for (let i = 0; i < 10; i++) {
        await testMiddleware.checkRequest('', createTestContext({ clientId: 'sliding', requestId: `slide-${i}`, timestamp: Date.now() + i }));
        testMiddleware.recordResponse(500);
      }

      expect(testMiddleware.getCircuitBreakerState()).toBe(CircuitBreakerState.OPEN);

      // Wait for window to expire
      await new Promise(resolve => setTimeout(resolve, 60));

      // Next 10 requests all 200 - should stay OPEN initially but then...
      for (let i = 0; i < 10; i++) {
        await testMiddleware.checkRequest('', createTestContext({ clientId: 'sliding', requestId: `slide2-${i}`, timestamp: Date.now() + 100 + i }));
        testMiddleware.recordResponse(200);
      }

      // After window expires, should transition based on new data
      const state = testMiddleware.getCircuitBreakerState();
      expect(state).toBe(CircuitBreakerState.CLOSED);
    });
  });

  describe('Rate Limiting', () => {
    it('should allow up to 100 requests per minute per client', async () => {
      for (let i = 0; i < 100; i++) {
        const context = createTestContext({
          clientId: 'rate-client-1',
          requestId: `rl-${i}`,
          timestamp: Date.now() + i,
        });
        const result = await middleware.checkRequest('', context);
        expect(result.allowed).toBe(true);
      }
    });

    it('should allow burst allowance (20 additional requests)', async () => {
      // 100 normal + 20 burst = 120 total allowed
      for (let i = 0; i < 120; i++) {
        const context = createTestContext({
          clientId: 'rate-client-2',
          requestId: `rl2-${i}`,
          timestamp: Date.now() + i,
        });
        const result = await middleware.checkRequest('', context);
        expect(result.allowed).toBe(true);
      }
    });

    it('should reject requests exceeding burst allowance', async () => {
      // Exhaust rate limit
      for (let i = 0; i < 120; i++) {
        const context = createTestContext({
          clientId: 'rate-client-3',
          requestId: `rl3-${i}`,
          timestamp: Date.now() + i,
        });
        await middleware.checkRequest('', context);
      }

      // Next request should be rejected
      const context = createTestContext({ clientId: 'rate-client-3', requestId: 'rl3-exceed', timestamp: Date.now() + 121 });
      const result = await middleware.checkRequest('', context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('Rate limit');
    });

    it('should isolate rate limits per client', async () => {
      // Client A makes 100 requests
      for (let i = 0; i < 100; i++) {
        await middleware.checkRequest('', createTestContext({ clientId: 'client-a', requestId: `a-${i}`, timestamp: Date.now() + i }));
      }

      // Client B should still be able to make requests
      const result = await middleware.checkRequest('', createTestContext({ clientId: 'client-b', requestId: 'b-1', timestamp: Date.now() }));
      expect(result.allowed).toBe(true);
    });

    it('should reset rate limit after window expires', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          rateLimit: {
            ...DEFAULT_SECURITY_CONFIG.workersHardening.rateLimit,
            requestsPerMinute: 5,
            burstAllowance: 1,
            windowMs: 100, // Very short window for testing (100ms)
          },
        },
      });

      // Exhaust limit
      for (let i = 0; i < 6; i++) {
        await testMiddleware.checkRequest('', createTestContext({ clientId: 'reset-test', requestId: `r-${i}`, timestamp: Date.now() + i }));
      }

      // Should be rejected
      let result = await testMiddleware.checkRequest('', createTestContext({ clientId: 'reset-test', requestId: 'r-6', timestamp: Date.now() + 10 }));
      expect(result.allowed).toBe(false);

      // Wait for window to expire
      await new Promise(resolve => setTimeout(resolve, 150));

      // Should be allowed again
      result = await testMiddleware.checkRequest('', createTestContext({ clientId: 'reset-test', requestId: 'r-after', timestamp: Date.now() + 70000 }));
      expect(result.allowed).toBe(true);
    });
  });

  describe('Request Size Limit', () => {
    it('should allow requests under 1MB', async () => {
      const smallInput = 'x'.repeat(1024 * 1024 - 1); // 1MB - 1 byte
      const context = createTestContext({ clientId: 'size-test', requestId: 'small', timestamp: Date.now() });
      const result = await middleware.checkRequest(smallInput, context);
      expect(result.allowed).toBe(true);
    });

    it('should reject requests at exactly 1MB', async () => {
      const exactInput = 'x'.repeat(1024 * 1024); // Exactly 1MB
      const context = createTestContext({ clientId: 'size-test', requestId: 'exact', timestamp: Date.now() });
      const result = await middleware.checkRequest(exactInput, context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('Request size');
    });

    it('should reject requests over 1MB', async () => {
      const largeInput = 'x'.repeat(1024 * 1024 + 1); // 1MB + 1 byte
      const context = createTestContext({ clientId: 'size-test', requestId: 'large', timestamp: Date.now() });
      const result = await middleware.checkRequest(largeInput, context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('Request size');
    });
  });

  describe('Timeout Enforcement', () => {
    it('should allow requests under 30s timeout', async () => {
      const context = createTestContext({ clientId: 'timeout-test', requestId: 'fast', timestamp: Date.now(), latencyMs: 100 });
      const result = await middleware.checkRequest('', context);
      expect(result.allowed).toBe(true);
    });

    it('should reject requests exceeding 30s timeout', async () => {
      const context = createTestContext({ clientId: 'timeout-test', requestId: 'slow', timestamp: Date.now(), latencyMs: 35000 });
      const result = await middleware.checkRequest('', context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('timeout');
    });

    it('should use configured timeout value', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          timeoutMs: 5000, // 5 second timeout
        },
      });

      const context = createTestContext({ clientId: 'timeout-test', requestId: 'custom', timestamp: Date.now(), latencyMs: 6000 });
      const result = await testMiddleware.checkRequest('', context);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('timeout');
    });
  });

  describe('Error Sanitization', () => {
      it('should sanitize internal error details', () => {
        const error = new Error('Internal server error: database connection failed at host=prod-db-1, port=5432, user=admin');
        const sanitized = middleware.sanitizeError(error);
        expect(sanitized).not.toContain('prod-db-1');
        expect(sanitized).not.toContain('5432');
        expect(sanitized).not.toContain('admin');
        expect(sanitized).toContain('Internal server error');
      });

      it('should return generic error message when sanitizeErrors is true', () => {
        const error = new Error('Secret key: sk-1234567890abcdef123456');
        const sanitized = middleware.sanitizeError(error);
        expect(sanitized).not.toContain('sk-1234567890abcdef123456');
        expect(sanitized).toBe('Internal server error');
      });

      it('should not sanitize when sanitizeErrors is false', () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          errorSanitization: false,
        },
      });

      const error = new Error('Internal server error: database connection failed at host=prod-db-1');
      const sanitized = testMiddleware.sanitizeError(error);
      expect(sanitized).toContain('prod-db-1');
    });
  });

  describe('Integration', () => {
    it('should enforce all protections simultaneously', async () => {
      // Create middleware with tight limits
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          rateLimit: { requestsPerMinute: 2, burstAllowance: 0 },
          circuitBreaker: { failureThreshold: 50, windowMs: 60000, halfOpenTimeoutMs: 60000, halfOpenRequests: 3 },
          timeoutMs: 30000,
          errorSanitization: true,
        },
      });

      // Request 1 - should pass
      let result = await testMiddleware.checkRequest('', createTestContext({ clientId: 'integration', requestId: 'int-1', timestamp: Date.now() }));
      expect(result.allowed).toBe(true);

      // Request 2 - should pass
      result = await testMiddleware.checkRequest('', createTestContext({ clientId: 'integration', requestId: 'int-2', timestamp: Date.now() }));
      expect(result.allowed).toBe(true);

      // Request 3 - should be rate limited
      result = await testMiddleware.checkRequest('', createTestContext({ clientId: 'integration', requestId: 'int-3', timestamp: Date.now() }));
      expect(result.allowed).toBe(false);
    });

    it('should handle disabled workersHardening', async () => {
      const testMiddleware = createMiddleware({
        ...DEFAULT_SECURITY_CONFIG,
        workersHardening: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening,
          enabled: false,
        },
      });

      const context = createTestContext({ clientId: 'disabled-test', requestId: 'dis-1', timestamp: Date.now() });
      const result = await testMiddleware.checkRequest('', context);
      expect(result.allowed).toBe(true);
    });

    it('should record metrics for monitoring', async () => {
      const context = createTestContext({ clientId: 'metrics-test', requestId: 'metrics-1' });
      await middleware.checkRequest('', context);

      const metrics = middleware.getMetrics();
      expect(metrics).toBeDefined();
      expect(metrics.requestsProcessed).toBeGreaterThan(0);
      expect(metrics.blockedRequests).toBeGreaterThanOrEqual(0);
    });
  });
});
