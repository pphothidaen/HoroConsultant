/**
 * Security Middleware - Prompt Injection Defense (M3) + Workers Hardening (M9)
 * 
 * Implements CONTRACT 1: Security Middleware Interface
 * File: src/security/middleware.ts
 */

// ═══ Enums ═══

export enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN',
}

// ═══ Configuration Types ═══

export interface SecurityConfig {
  // M3: Prompt Injection
  promptInjection: {
    enabled: boolean;
    patterns: string[];           // Regex patterns for injection detection
    maxInputTokens: number;       // Hard limit on input size
    sanitizeOutput: boolean;      // Strip potential injection from responses
  };

  // M9: Workers Hardening
  workersHardening: {
    enabled: boolean;
    maxRequestSize: number;       // bytes (default: 1MB)
    rateLimit: {
      requestsPerMinute: number;  // default: 100
      burstAllowance: number;     // default: 20
      windowMs: number;           // default: 60000 (1 minute)
    };
    circuitBreaker: {
      failureThreshold: number;   // 5xx rate % (default: 50)
      windowMs: number;           // evaluation window (default: 60000)
      halfOpenRequests: number;   // test requests in half-open (default: 3)
      halfOpenTimeoutMs: number;  // timeout before trying half-open (default: 60000)
    };
    timeoutMs: number;            // max request duration (default: 30000)
    errorSanitization: boolean;   // strip stack traces (default: true)
  };
}

export interface SecurityContext {
  clientId: string;               // IP or auth token hash
  requestId: string;              // correlation ID
  timestamp: number;
  metadata: Record<string, unknown>;
  latencyMs?: number;             // for timeout enforcement
  requestSize?: number;           // for request size limit
}

export interface SecurityResult {
  allowed: boolean;
  reason?: string;                // if blocked
  sanitizedInput?: string;        // if sanitized
  sanitizedOutput?: string;       // if sanitized
  error?: string;                 // sanitized error message
  metrics: {
    promptInjectionScore: number; // 0-1 confidence
    rateLimitRemaining: number;
    circuitBreakerState: CircuitBreakerState;
  };
}

export interface SecurityMetrics {
  requestsProcessed: number;
  injectionsDetected: number;
  injectionsBlocked: number;
  outputsSanitized: number;
  requestsByClient: Record<string, number>;
  rateLimitHits: number;
  circuitBreakerState: CircuitBreakerState;
  avgPromptInjectionScore: number;
  totalRequests: number;
  blockedRequests: number;
}

// ═══ Default Configuration ═══

export const DEFAULT_SECURITY_CONFIG: SecurityConfig = {
  promptInjection: {
    enabled: true,
    patterns: [
      // Direct instruction overrides
      'ignore\\s+previous\\s+instructions',
      'forget\\s+all\\s+prior',
      'disregard\\s+previous',
      'override\\s+instructions',
      'new\\s+instructions\\s*:',
      
      // System prompt extraction
      'system\\s+prompt',
      'show\\s+me\\s+the\\s+system\\s+prompt',
      'what\\s+is\\s+your\\s+system\\s+prompt',
      'reveal\\s+your\\s+prompt',
      'print\\s+your\\s+instructions',
      
      // Role manipulation
      'role\\s*[:=]\\s*(admin|system|developer|root|superuser)',
      'you\\s+are\\s+now\\s+(an?\\s+)?(admin|system|developer|root)',
      'pretend\\s+to\\s+be\\s+(an?\\s+)?(admin|system|developer|root)',
      'act\\s+as\\s+(an?\\s+)?(admin|system|developer|root)',
      'become\\s+(an?\\s+)?(admin|system|developer|root)',
      
      // Safety bypass
      'bypass\\s+safety',
      'bypass\\s+security',
      'disable\\s+safety',
      'disable\\s+security',
      'ignore\\s+safety',
      'ignore\\s+security',
      
      // Jailbreak patterns
      'DAN\\s+mode',
      'do\\s+anything\\s+now',
      'unrestricted\\s+mode',
      'no\\s+restrictions',
      'unfiltered\\s+response',
    ],
    maxInputTokens: 4096,
    sanitizeOutput: true,
  },
  
  workersHardening: {
    enabled: true,
    maxRequestSize: 1024 * 1024, // 1MB
    rateLimit: {
      requestsPerMinute: 100,
      burstAllowance: 20,
      windowMs: 60000, // 1 minute
    },
    circuitBreaker: {
      failureThreshold: 50, // 50% 5xx rate
      windowMs: 60000,      // 1 minute
      halfOpenRequests: 3,
      halfOpenTimeoutMs: 60000, // 1 minute before trying half-open
    },
    timeoutMs: 30000,
    errorSanitization: true,
  },
};

// ═══ Security Middleware Implementation ═══

export class SecurityMiddleware {
  private config: SecurityConfig;
  private metrics: SecurityMetrics;
  private rateLimitStore: Map<string, { count: number; windowStart: number }> = new Map();
  private circuitBreakerState: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private circuitBreakerFailures = 0;
  private circuitBreakerSuccesses = 0;
  private circuitBreakerOpenedAt = 0;  // Track when circuit breaker was opened
  private circuitBreakerLastCheck = 0;
  private compiledPatterns: RegExp[] = [];

  constructor(config: Partial<SecurityConfig> = {}) {
    // Merge with defaults
    this.config = {
      promptInjection: {
        ...DEFAULT_SECURITY_CONFIG.promptInjection,
        ...config.promptInjection,
        patterns: config.promptInjection?.patterns ?? DEFAULT_SECURITY_CONFIG.promptInjection.patterns,
      },
      workersHardening: {
        ...DEFAULT_SECURITY_CONFIG.workersHardening,
        ...config.workersHardening,
        rateLimit: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening.rateLimit,
          ...config.workersHardening?.rateLimit,
        },
        circuitBreaker: {
          ...DEFAULT_SECURITY_CONFIG.workersHardening.circuitBreaker,
          ...config.workersHardening?.circuitBreaker,
        },
      },
    };

    this.metrics = {
      requestsProcessed: 0,
      injectionsDetected: 0,
      injectionsBlocked: 0,
      outputsSanitized: 0,
      requestsByClient: {},
      rateLimitHits: 0,
      circuitBreakerState: CircuitBreakerState.CLOSED,
      avgPromptInjectionScore: 0,
      totalRequests: 0,
      blockedRequests: 0,
    };

    // Pre-compile regex patterns
    this.compilePatterns();
  }

  private compilePatterns(): void {
    this.compiledPatterns = this.config.promptInjection.patterns.map(
      (pattern) => new RegExp(pattern, 'gi')
    );
  }

  /**
   * Main entry point - called on every request
   * Checks input for prompt injection patterns and enforces token limits
   */
  async checkRequest(input: string, context: SecurityContext): Promise<SecurityResult> {
    this.metrics.requestsProcessed++;
    this.metrics.totalRequests++;
    this.metrics.requestsByClient[context.clientId] = 
      (this.metrics.requestsByClient[context.clientId] || 0) + 1;

    // Check rate limiting (M9)
    if (this.config.workersHardening.enabled) {
      const rateLimitResult = this.checkRateLimit(context.clientId);
      if (!rateLimitResult.allowed) {
        this.metrics.rateLimitHits++;
        this.metrics.blockedRequests++;
        return {
          allowed: false,
          reason: rateLimitResult.reason,
          metrics: {
            promptInjectionScore: 0,
            rateLimitRemaining: rateLimitResult.remaining,
            circuitBreakerState: this.circuitBreakerState,
          },
        };
      }
    }

    // Check circuit breaker (M9)
    if (this.config.workersHardening.enabled) {
      const cbState = this.getCircuitBreakerState();
      if (cbState === CircuitBreakerState.OPEN) {
        this.metrics.blockedRequests++;
        return {
          allowed: false,
          reason: 'circuit breaker open - too many failures',
          metrics: {
            promptInjectionScore: 0,
            rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
            circuitBreakerState: cbState,
          },
        };
      }
    }

    // Check max input size (M9)
    if (this.config.workersHardening.enabled) {
      const inputSize = new TextEncoder().encode(input).length;
      if (inputSize >= this.config.workersHardening.maxRequestSize) {
        this.metrics.blockedRequests++;
        return {
          allowed: false,
          reason: `Request size ${inputSize} bytes exceeds limit of ${this.config.workersHardening.maxRequestSize} bytes`,
          metrics: {
            promptInjectionScore: 0,
            rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
            circuitBreakerState: this.circuitBreakerState,
          },
        };
      }
    }

    // Check timeout (M9)
    if (this.config.workersHardening.enabled && context.latencyMs !== undefined) {
      if (context.latencyMs > this.config.workersHardening.timeoutMs) {
        this.metrics.blockedRequests++;
        return {
          allowed: false,
          reason: `Request timeout: ${context.latencyMs}ms exceeds limit of ${this.config.workersHardening.timeoutMs}ms`,
          metrics: {
            promptInjectionScore: 0,
            rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
            circuitBreakerState: this.circuitBreakerState,
          },
        };
      }
    }

    // Check prompt injection (M3)
    if (this.config.promptInjection.enabled) {
      const injectionResult = this.detectPromptInjection(input);
      this.metrics.avgPromptInjectionScore = 
        (this.metrics.avgPromptInjectionScore * (this.metrics.requestsProcessed - 1) + injectionResult.score) 
        / this.metrics.requestsProcessed;

      if (injectionResult.detected) {
        this.metrics.injectionsDetected++;
        this.metrics.injectionsBlocked++;
        this.metrics.blockedRequests++;
        
        // Sanitize input if needed
        const sanitizedInput = this.sanitizeInput(input);
        
        return {
          allowed: false,
          reason: `Prompt injection detected: ${injectionResult.matchedPatterns.join(', ')}`,
          sanitizedInput,
          metrics: {
            promptInjectionScore: injectionResult.score,
            rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
            circuitBreakerState: this.circuitBreakerState,
          },
        };
      }
    }

    return {
      allowed: true,
      metrics: {
        promptInjectionScore: 0,
        rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
        circuitBreakerState: this.circuitBreakerState,
      },
    };
  }

  /**
   * Called on response before returning to client
   * Sanitizes output to prevent injection leakage
   */
  async checkResponse(output: string, context: SecurityContext): Promise<SecurityResult> {
    let sanitizedOutput = output;
    let wasSanitized = false;

    if (this.config.promptInjection.enabled && this.config.promptInjection.sanitizeOutput) {
      const injectionResult = this.detectPromptInjection(output);
      
      if (injectionResult.detected) {
        sanitizedOutput = this.sanitizeOutput(output);
        wasSanitized = true;
        this.metrics.outputsSanitized++;
      }
    }

    return {
      allowed: true,
      sanitizedOutput: wasSanitized ? sanitizedOutput : undefined,
      metrics: {
        promptInjectionScore: 0,
        rateLimitRemaining: this.getRateLimitState(context.clientId).remaining,
        circuitBreakerState: this.circuitBreakerState,
      },
    };
  }

  /**
   * Detect prompt injection patterns in text
   */
  private detectPromptInjection(text: string): { detected: boolean; score: number; matchedPatterns: string[] } {
    const matchedPatterns: string[] = [];
    let totalMatches = 0;

    for (let i = 0; i < this.compiledPatterns.length; i++) {
      const pattern = this.compiledPatterns[i];
      const matches = text.match(pattern);
      if (matches) {
        matchedPatterns.push(this.config.promptInjection.patterns[i]);
        totalMatches += matches.length;
      }
    }

    // Calculate confidence score (0-1)
    // More matches = higher confidence
    const score = Math.min(1, totalMatches * 0.3 + matchedPatterns.length * 0.2);

    return {
      detected: matchedPatterns.length > 0,
      score,
      matchedPatterns,
    };
  }

  /**
   * Sanitize input by removing/redacting injection patterns
   */
  private sanitizeInput(input: string): string {
    let result = input;
    
    for (const pattern of this.compiledPatterns) {
      result = result.replace(pattern, '[REDACTED: PROMPT INJECTION]');
    }
    
    return result;
  }

  /**
   * Sanitize output to prevent injection leakage
   */
  private sanitizeOutput(output: string): string {
    let result = output;
    
    for (const pattern of this.compiledPatterns) {
      result = result.replace(pattern, '[REDACTED]');
    }
    
    return result;
  }

  // ═══ Rate Limiting (M9) ═══

  private checkRateLimit(clientId: string): { allowed: boolean; remaining: number; reason?: string } {
    const now = Date.now();
    const windowMs = this.config.workersHardening.rateLimit.windowMs ?? 60000; // 1 minute default
    const limit = this.config.workersHardening.rateLimit.requestsPerMinute;
    const burst = this.config.workersHardening.rateLimit.burstAllowance;
    const effectiveLimit = limit + burst;

    const clientData = this.rateLimitStore.get(clientId);
    
    if (!clientData || now - clientData.windowStart >= windowMs) {
      // New window
      this.rateLimitStore.set(clientId, { count: 1, windowStart: now });
      return { allowed: true, remaining: effectiveLimit - 1 };
    }

    if (clientData.count >= effectiveLimit) {
      return { 
        allowed: false, 
        remaining: 0, 
        reason: `Rate limit exceeded: ${clientData.count}/${effectiveLimit} requests per minute` 
      };
    }

    clientData.count++;
    return { allowed: true, remaining: effectiveLimit - clientData.count };
  }

  getRateLimitState(clientId: string): { remaining: number; resetAt: number } {
    const now = Date.now();
    const windowMs = this.config.workersHardening.rateLimit.windowMs ?? 60000;
    const limit = this.config.workersHardening.rateLimit.requestsPerMinute;
    const burst = this.config.workersHardening.rateLimit.burstAllowance;
    const effectiveLimit = limit + burst;

    const clientData = this.rateLimitStore.get(clientId);
    
    if (!clientData) {
      return { remaining: effectiveLimit, resetAt: now + windowMs };
    }

    const resetAt = clientData.windowStart + windowMs;
    const remaining = Math.max(0, effectiveLimit - clientData.count);
    
    return { remaining, resetAt };
  }

  // ═══ Circuit Breaker (M9) ═══

  private circuitBreakerMetrics: {
    totalRequests: number;
    failedRequests: number;
    windowStart: number;
  } = {
    totalRequests: 0,
    failedRequests: 0,
    windowStart: Date.now(),
  };

  getCircuitBreakerState(): CircuitBreakerState {
    const now = Date.now();
    const halfOpenTimeoutMs = this.config.workersHardening.circuitBreaker.halfOpenTimeoutMs;

    // Check if we should evaluate circuit breaker state
    if (now - this.circuitBreakerLastCheck >= halfOpenTimeoutMs) {
      this.evaluateCircuitBreaker();
      this.circuitBreakerLastCheck = now;
    }

    return this.circuitBreakerState;
  }

  private evaluateCircuitBreaker(): void {
    const threshold = this.config.workersHardening.circuitBreaker.failureThreshold;
    const windowMs = this.config.workersHardening.circuitBreaker.windowMs;
    const now = Date.now();

    // Reset window if expired
    if (now - this.circuitBreakerMetrics.windowStart >= windowMs) {
      this.circuitBreakerMetrics.windowStart = now;
      this.circuitBreakerMetrics.totalRequests = 0;
      this.circuitBreakerMetrics.failedRequests = 0;
    }

    if (this.circuitBreakerState === CircuitBreakerState.CLOSED) {
      // Check failure rate percentage
      if (this.circuitBreakerMetrics.totalRequests >= 10) { // Minimum sample size
        const failureRate = (this.circuitBreakerMetrics.failedRequests / this.circuitBreakerMetrics.totalRequests) * 100;
        if (failureRate >= threshold) {
          this.circuitBreakerState = CircuitBreakerState.OPEN;
          this.circuitBreakerOpenedAt = now;
        }
      }
    } else if (this.circuitBreakerState === CircuitBreakerState.OPEN) {
      // After halfOpenTimeoutMs, try half-open
      const halfOpenTimeoutMs = this.config.workersHardening.circuitBreaker.halfOpenTimeoutMs;
      if (now - this.circuitBreakerOpenedAt >= halfOpenTimeoutMs) {
        this.circuitBreakerState = CircuitBreakerState.HALF_OPEN;
        this.circuitBreakerSuccesses = 0;
        // Reset metrics for HALF_OPEN evaluation
        this.circuitBreakerMetrics.totalRequests = 0;
        this.circuitBreakerMetrics.failedRequests = 0;
      }
    } else if (this.circuitBreakerState === CircuitBreakerState.HALF_OPEN) {
      const halfOpenRequests = this.config.workersHardening.circuitBreaker.halfOpenRequests;
      if (this.circuitBreakerSuccesses >= halfOpenRequests) {
        this.circuitBreakerState = CircuitBreakerState.CLOSED;
        this.circuitBreakerFailures = 0;
        this.circuitBreakerMetrics.totalRequests = 0;
        this.circuitBreakerMetrics.failedRequests = 0;
      }
      // Check if we should reopen due to failure in HALF_OPEN
      else if (this.circuitBreakerMetrics.failedRequests > 0 && this.circuitBreakerMetrics.totalRequests > 0) {
        const failureRate = (this.circuitBreakerMetrics.failedRequests / this.circuitBreakerMetrics.totalRequests) * 100;
        if (failureRate >= this.config.workersHardening.circuitBreaker.failureThreshold) {
          this.circuitBreakerState = CircuitBreakerState.OPEN;
          this.circuitBreakerOpenedAt = now;
        }
      }
    }

    this.metrics.circuitBreakerState = this.circuitBreakerState;
  }

  recordResponse(statusCode: number): void {
    const now = Date.now();
    const windowMs = this.config.workersHardening.circuitBreaker.windowMs;

    // Reset window if expired
    if (now - this.circuitBreakerMetrics.windowStart >= windowMs) {
      this.circuitBreakerMetrics.windowStart = now;
      this.circuitBreakerMetrics.totalRequests = 0;
      this.circuitBreakerMetrics.failedRequests = 0;
    }

    this.circuitBreakerMetrics.totalRequests++;
    if (statusCode >= 500 && statusCode < 600) {
      this.circuitBreakerMetrics.failedRequests++;
    } else {
      // Track successful requests for HALF_OPEN transition
      if (this.circuitBreakerState === CircuitBreakerState.HALF_OPEN) {
        this.circuitBreakerSuccesses++;
      }
    }

    // Evaluate circuit breaker after recording response
    this.evaluateCircuitBreaker();
    this.circuitBreakerLastCheck = now;
  }

  recordFailure(): void {
    this.circuitBreakerMetrics.totalRequests++;
    this.circuitBreakerMetrics.failedRequests++;
  }

  recordSuccess(): void {
    this.circuitBreakerMetrics.totalRequests++;
    if (this.circuitBreakerState === CircuitBreakerState.HALF_OPEN) {
      this.circuitBreakerSuccesses++;
    }
    // Evaluate circuit breaker after recording success
    this.evaluateCircuitBreaker();
  }

  // ═══ Error Sanitization ═══

  sanitizeError(error: Error): string {
    if (!this.config.workersHardening.errorSanitization) {
      return error.message;
    }

    // Strip sensitive information
    let sanitized = error.message;
    let hasSecrets = false;
    
    // Remove potential secrets/keys
    sanitized = sanitized.replace(/sk-[a-zA-Z0-9]{20,}/g, () => { hasSecrets = true; return '[REDACTED]'; });
    sanitized = sanitized.replace(/api[_-]?key[=:]\\s*[a-zA-Z0-9_-]{20,}/gi, () => { hasSecrets = true; return 'api_key=[REDACTED]'; });
    sanitized = sanitized.replace(/password[=:]\\s*[^\\s]+/gi, () => { hasSecrets = true; return 'password=[REDACTED]'; });
    sanitized = sanitized.replace(/token[=:]\\s*[^\\s]+/gi, () => { hasSecrets = true; return 'token=[REDACTED]'; });
    sanitized = sanitized.replace(/secret[=:]\\s*[^\\s]+/gi, () => { hasSecrets = true; return 'secret=[REDACTED]'; });
    
    // If secrets were found, return generic error message
    if (hasSecrets) {
      return 'Internal server error';
    }

    // Remove stack traces
    sanitized = sanitized.replace(/\\n\\s*at\\s+.*/g, '');
    sanitized = sanitized.replace(/\\(.*:\\d+:\\d+\\)/g, '');
    
    // Remove internal hostnames/IPs
        sanitized = sanitized.replace(/\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/g, '[REDACTED IP]');
        // Remove internal host patterns (like prod-db-1, staging-app, etc.)
        sanitized = sanitized.replace(/[a-z]+-[a-z]+-\d+/g, '[REDACTED HOST]');
        // Remove port numbers
        sanitized = sanitized.replace(/port\s*=\s*\d+/gi, 'port=[REDACTED]');
        sanitized = sanitized.replace(/port\s*:\s*\d+/gi, 'port=[REDACTED]');
        sanitized = sanitized.replace(/\bport\s+\d+\b/gi, 'port=[REDACTED]');
        sanitized = sanitized.replace(/:\d{2,5}\b/g, ':[REDACTED PORT]');
        // Remove user credentials
        sanitized = sanitized.replace(/user\s*=\s*[^\s,]+/gi, 'user=[REDACTED]');
        sanitized = sanitized.replace(/user\s*:\s*[^\s,]+/gi, 'user=[REDACTED]');
        sanitized = sanitized.replace(/\buser\s+[^\s,]+\b/gi, 'user=[REDACTED]');
    sanitized = sanitized.replace(/\\b[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b/g, (match) => {
      // Keep common domains, redact internal ones
      if (match.includes('localhost') || match.includes('internal') || match.includes('.local')) {
        return '[REDACTED HOST]';
      }
      return match;
    });

    return sanitized || 'Internal server error';
  }

  // ═══ Metrics ═══

  getMetrics(): SecurityMetrics {
    return { ...this.metrics };
  }

  // ═══ Utility Methods ═══

  /**
   * Update prompt injection patterns at runtime
   */
  updatePatterns(patterns: string[]): void {
    this.config.promptInjection.patterns = patterns;
    this.compilePatterns();
  }

  /**
   * Enable/disable prompt injection detection
   */
  setPromptInjectionEnabled(enabled: boolean): void {
    this.config.promptInjection.enabled = enabled;
  }

  /**
   * Enable/disable output sanitization
   */
  setSanitizeOutput(enabled: boolean): void {
    this.config.promptInjection.sanitizeOutput = enabled;
  }

  /**
   * Set max input tokens
   */
  setMaxInputTokens(tokens: number): void {
    this.config.promptInjection.maxInputTokens = tokens;
  }

  /**
   * Reset all metrics
   */
  resetMetrics(): void {
    this.metrics = {
      requestsProcessed: 0,
      injectionsDetected: 0,
      injectionsBlocked: 0,
      outputsSanitized: 0,
      requestsByClient: {},
      rateLimitHits: 0,
      circuitBreakerState: CircuitBreakerState.CLOSED,
      avgPromptInjectionScore: 0,
      totalRequests: 0,
      blockedRequests: 0,
    };
    this.rateLimitStore.clear();
    this.circuitBreakerState = CircuitBreakerState.CLOSED;
    this.circuitBreakerFailures = 0;
    this.circuitBreakerSuccesses = 0;
    this.circuitBreakerOpenedAt = 0;
    this.circuitBreakerLastCheck = 0;
  }
}

// ═══ Export for Workers Integration ═══

// Default instance for easy importing
export const securityMiddleware = new SecurityMiddleware(DEFAULT_SECURITY_CONFIG);

// Helper to create middleware with custom config
export function createSecurityMiddleware(config: Partial<SecurityConfig>): SecurityMiddleware {
  return new SecurityMiddleware(config);
}