"""
Security Middleware - Prompt Injection Defense (M3) + Workers Hardening (M9)
Python implementation for testing (mirrors TypeScript version for Workers)

Implements CONTRACT 1: Security Middleware Interface
File: src/security/middleware.py
"""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal, Union


# ═══ Configuration Types ═══

@dataclass
class PromptInjectionConfig:
    enabled: bool = True
    patterns: List[str] = field(default_factory=list)
    maxInputTokens: int = 4096
    sanitizeOutput: bool = True


@dataclass
class RateLimitConfig:
    requestsPerMinute: int = 100
    burstAllowance: int = 20


@dataclass
class CircuitBreakerConfig:
    failureThreshold: int = 50  # 50% 5xx rate
    windowMs: int = 60000       # 1 minute
    halfOpenRequests: int = 3


@dataclass
class WorkersHardeningConfig:
    enabled: bool = True
    maxRequestSize: int = 1024 * 1024  # 1MB
    rateLimit: RateLimitConfig = field(default_factory=RateLimitConfig)
    circuitBreaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    timeoutMs: int = 30000
    errorSanitization: bool = True


@dataclass
class SecurityConfig:
    promptInjection: PromptInjectionConfig = field(default_factory=PromptInjectionConfig)
    workersHardening: WorkersHardeningConfig = field(default_factory=WorkersHardeningConfig)


@dataclass
class SecurityContext:
    clientId: str
    requestId: str
    timestamp: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityResult:
    allowed: bool
    reason: Optional[str] = None
    sanitizedInput: Optional[str] = None
    sanitizedOutput: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityMetrics:
    requestsProcessed: int = 0
    injectionsDetected: int = 0
    injectionsBlocked: int = 0
    outputsSanitized: int = 0
    requestsByClient: Dict[str, int] = field(default_factory=dict)
    rateLimitHits: int = 0
    circuitBreakerState: Literal['closed', 'open', 'half-open'] = 'closed'
    avgPromptInjectionScore: float = 0.0
    promptInjectionScore: float = 0.0


# ═══ Default Configuration ═══

DEFAULT_PROMPT_INJECTION_PATTERNS = [
    # Direct instruction overrides
    r'ignore\s+previous\s+instructions',
    r'forget\s+all\s+prior',
    r'disregard\s+previous',
    r'override\s+instructions',
    r'new\s+instructions\s*:',
    
    # System prompt extraction
    r'system\s+prompt',
    r'show\s+me\s+the\s+system\s+prompt',
    r'what\s+is\s+your\s+system\s+prompt',
    r'reveal\s+your\s+prompt',
    r'print\s+your\s+instructions',
    
    # Role manipulation
    r'role\s*[:=]\s*(admin|system|developer|root|superuser)',
    r'you\s+are\s+now\s+(an?\s+)?(admin|system|developer|root)',
    r'pretend\s+to\s+be\s+(an?\s+)?(admin|system|developer|root)',
    r'act\s+as\s+(an?\s+)?(admin|system|developer|root)',
    r'become\s+(an?\s+)?(admin|system|developer|root)',
    
    # Safety bypass
    r'bypass\s+safety',
    r'bypass\s+security',
    r'disable\s+safety',
    r'disable\s+security',
    r'ignore\s+safety',
    r'ignore\s+security',
    
    # Jailbreak patterns
    r'DAN\s+mode',
    r'do\s+anything\s+now',
    r'unrestricted\s+mode',
    r'no\s+restrictions',
    r'unfiltered\s+response',
]


DEFAULT_SECURITY_CONFIG = SecurityConfig(
    promptInjection=PromptInjectionConfig(
        enabled=True,
        patterns=DEFAULT_PROMPT_INJECTION_PATTERNS,
        maxInputTokens=4096,
        sanitizeOutput=True,
    ),
    workersHardening=WorkersHardeningConfig(),
)


# ═══ Security Middleware Implementation ═══

class SecurityMiddleware:
    def __init__(self, config: Optional[Union[SecurityConfig, Dict[str, Any]]] = None):
        # Merge with defaults
        if config is None:
            config = DEFAULT_SECURITY_CONFIG
        elif isinstance(config, dict):
            # Convert dict to dataclass
            config = self._dictToConfig(config)
        elif isinstance(config, SecurityConfig):
            # Ensure nested configs are dataclasses, not dicts
            config = self._ensureDataclassConfig(config)
        
        self.config = config
        self.metrics = SecurityMetrics()
        self.rateLimitStore: Dict[str, Dict[str, Any]] = {}
        self.circuitBreakerState: Literal['closed', 'open', 'half-open'] = 'closed'
        self.circuitBreakerFailures = 0
        self.circuitBreakerSuccesses = 0
        self.circuitBreakerLastCheck = 0
        self.compiledPatterns: List[re.Pattern] = []
        
        self._compilePatterns()

    def _dictToConfig(self, config_dict: Dict[str, Any]) -> SecurityConfig:
        """Convert dictionary config to SecurityConfig dataclass."""
        pi_dict = config_dict.get('promptInjection', {})
        wh_dict = config_dict.get('workersHardening', {})
        
        # Build promptInjection config
        pi_config = PromptInjectionConfig(
            enabled=pi_dict.get('enabled', True),
            patterns=pi_dict.get('patterns', DEFAULT_PROMPT_INJECTION_PATTERNS),
            maxInputTokens=pi_dict.get('maxInputTokens', 4096),
            sanitizeOutput=pi_dict.get('sanitizeOutput', True),
        )
        
        # Build workersHardening config
        rl_dict = wh_dict.get('rateLimit', {})
        cb_dict = wh_dict.get('circuitBreaker', {})
        
        rate_limit_config = RateLimitConfig(
            requestsPerMinute=rl_dict.get('requestsPerMinute', 100),
            burstAllowance=rl_dict.get('burstAllowance', 20),
        )
        
        circuit_breaker_config = CircuitBreakerConfig(
            failureThreshold=cb_dict.get('failureThreshold', 50),
            windowMs=cb_dict.get('windowMs', 60000),
            halfOpenRequests=cb_dict.get('halfOpenRequests', 3),
        )
        
        wh_config = WorkersHardeningConfig(
            enabled=wh_dict.get('enabled', True),
            maxRequestSize=wh_dict.get('maxRequestSize', 1024 * 1024),
            rateLimit=rate_limit_config,
            circuitBreaker=circuit_breaker_config,
            timeoutMs=wh_dict.get('timeoutMs', 30000),
            errorSanitization=wh_dict.get('errorSanitization', True),
        )
        
        return SecurityConfig(
            promptInjection=pi_config,
            workersHardening=wh_config,
        )

    def _ensureDataclassConfig(self, config: SecurityConfig) -> SecurityConfig:
        """Ensure nested configs are dataclasses, not dicts."""
        pi = config.promptInjection
        wh = config.workersHardening
        
        # Fix promptInjection if it's a dict
        if isinstance(pi, dict):
            pi = PromptInjectionConfig(
                enabled=pi.get('enabled', True),
                patterns=pi.get('patterns', DEFAULT_PROMPT_INJECTION_PATTERNS),
                maxInputTokens=pi.get('maxInputTokens', 4096),
                sanitizeOutput=pi.get('sanitizeOutput', True),
            )
        
        # Fix workersHardening if it's a dict
        if isinstance(wh, dict):
            rl_dict = wh.get('rateLimit', {})
            cb_dict = wh.get('circuitBreaker', {})
            
            rate_limit_config = RateLimitConfig(
                requestsPerMinute=rl_dict.get('requestsPerMinute', 100),
                burstAllowance=rl_dict.get('burstAllowance', 20),
            )
            
            circuit_breaker_config = CircuitBreakerConfig(
                failureThreshold=cb_dict.get('failureThreshold', 50),
                windowMs=cb_dict.get('windowMs', 60000),
                halfOpenRequests=cb_dict.get('halfOpenRequests', 3),
            )
            
            wh = WorkersHardeningConfig(
                enabled=wh.get('enabled', True),
                maxRequestSize=wh.get('maxRequestSize', 1024 * 1024),
                rateLimit=rate_limit_config,
                circuitBreaker=circuit_breaker_config,
                timeoutMs=wh.get('timeoutMs', 30000),
                errorSanitization=wh.get('errorSanitization', True),
            )
        
        return SecurityConfig(promptInjection=pi, workersHardening=wh)

    def _compilePatterns(self) -> None:
        self.compiledPatterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.config.promptInjection.patterns
        ]

    # ═══ Main Entry Points ═══

    async def checkRequest(self, input: str, context: SecurityContext) -> SecurityResult:
        self.metrics.requestsProcessed += 1
        self.metrics.requestsByClient[context.clientId] = \
            self.metrics.requestsByClient.get(context.clientId, 0) + 1

        # Check rate limiting (M9)
        if self.config.workersHardening.enabled:
            rateLimitResult = self._checkRateLimit(context.clientId)
            if not rateLimitResult['allowed']:
                self.metrics.rateLimitHits += 1
                return SecurityResult(
                    allowed=False,
                    reason=rateLimitResult.get('reason'),
                    metrics={
                        'promptInjectionScore': 0,
                        'rateLimitRemaining': rateLimitResult['remaining'],
                        'circuitBreakerState': self.circuitBreakerState,
                    }
                )

        # Check circuit breaker (M9)
        if self.config.workersHardening.enabled:
            cbState = self.getCircuitBreakerState()
            if cbState == 'open':
                return SecurityResult(
                    allowed=False,
                    reason='Circuit breaker open - too many failures',
                    metrics={
                        'promptInjectionScore': 0,
                        'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                        'circuitBreakerState': cbState,
                    }
                )

        # Check max input size (M9)
        if self.config.workersHardening.enabled:
            inputSize = len(input.encode('utf-8'))
            if inputSize > self.config.workersHardening.maxRequestSize:
                return SecurityResult(
                    allowed=False,
                    reason=f'Request size {inputSize} bytes exceeds limit of {self.config.workersHardening.maxRequestSize} bytes',
                    metrics={
                        'promptInjectionScore': 0,
                        'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                        'circuitBreakerState': self.circuitBreakerState,
                    }
                )

        # Check max input tokens (M3)
        if self.config.promptInjection.enabled:
            tokenCount = self._estimateTokens(input)
            if tokenCount > self.config.promptInjection.maxInputTokens:
                return SecurityResult(
                    allowed=False,
                    reason=f'Input token count {tokenCount} exceeds limit of {self.config.promptInjection.maxInputTokens} tokens',
                    metrics={
                        'promptInjectionScore': 0,
                        'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                        'circuitBreakerState': self.circuitBreakerState,
                    }
                )

        # Check prompt injection (M3)
        if self.config.promptInjection.enabled:
            injectionResult = self._detectPromptInjection(input)
            self.metrics.avgPromptInjectionScore = (
                (self.metrics.avgPromptInjectionScore * (self.metrics.requestsProcessed - 1) + injectionResult['score']) 
                / self.metrics.requestsProcessed
            )

            if injectionResult['detected']:
                self.metrics.injectionsDetected += 1
                self.metrics.injectionsBlocked += 1
                
                # Sanitize input
                sanitizedInput = self._sanitizeInput(input)
                
                return SecurityResult(
                    allowed=False,
                    reason=f"Prompt injection detected: {', '.join(injectionResult['matchedPatterns'])}",
                    sanitizedInput=sanitizedInput,
                    metrics={
                        'promptInjectionScore': injectionResult['score'],
                        'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                        'circuitBreakerState': self.circuitBreakerState,
                    }
                )

        return SecurityResult(
            allowed=True,
            metrics={
                'promptInjectionScore': 0,
                'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                'circuitBreakerState': self.circuitBreakerState,
            }
        )

    async def checkResponse(self, output: str, context: SecurityContext) -> SecurityResult:
        sanitizedOutput = output
        wasSanitized = False

        if (self.config.promptInjection.enabled and 
            self.config.promptInjection.sanitizeOutput):
            injectionResult = self._detectPromptInjection(output)
            
            if injectionResult['detected']:
                sanitizedOutput = self._sanitizeOutput(output)
                wasSanitized = True
                self.metrics.outputsSanitized += 1

        return SecurityResult(
            allowed=True,
            sanitizedOutput=sanitizedOutput if wasSanitized else None,
            metrics={
                'promptInjectionScore': 0,
                'rateLimitRemaining': self.getRateLimitState(context.clientId)['remaining'],
                'circuitBreakerState': self.circuitBreakerState,
            }
        )

    # ═══ Prompt Injection Detection ═══

    def _detectPromptInjection(self, text: str) -> Dict[str, Any]:
        matchedPatterns = []
        totalMatches = 0

        for i, pattern in enumerate(self.compiledPatterns):
            matches = pattern.findall(text)
            if matches:
                matchedPatterns.append(self.config.promptInjection.patterns[i])
                totalMatches += len(matches)

        # Calculate confidence score (0-1)
        score = min(1.0, totalMatches * 0.3 + len(matchedPatterns) * 0.2)

        return {
            'detected': len(matchedPatterns) > 0,
            'score': score,
            'matchedPatterns': matchedPatterns,
        }

    def _sanitizeInput(self, input: str) -> str:
        result = input
        for pattern in self.compiledPatterns:
            result = pattern.sub('[REDACTED: PROMPT INJECTION]', result)
        return result

    def _sanitizeOutput(self, output: str) -> str:
        result = output
        for pattern in self.compiledPatterns:
            result = pattern.sub('[REDACTED]', result)
        return result

    def _estimateTokens(self, text: str) -> int:
        """Estimate token count (roughly 4 chars per token)."""
        return len(text) // 4

    # ═══ Rate Limiting (M9) ═══

    def _checkRateLimit(self, clientId: str) -> Dict[str, Any]:
        now = time.time() * 1000  # Convert to ms
        windowMs = 60000  # 1 minute
        limit = self.config.workersHardening.rateLimit.requestsPerMinute
        burst = self.config.workersHardening.rateLimit.burstAllowance
        effectiveLimit = limit + burst

        clientData = self.rateLimitStore.get(clientId)
        
        if not clientData or now - clientData['windowStart'] >= windowMs:
            # New window
            self.rateLimitStore[clientId] = {'count': 1, 'windowStart': now}
            return {'allowed': True, 'remaining': effectiveLimit - 1}

        if clientData['count'] >= effectiveLimit:
            return { 
                'allowed': False, 
                'remaining': 0, 
                'reason': f'Rate limit exceeded: {clientData["count"]}/{effectiveLimit} requests per minute' 
            }

        clientData['count'] += 1
        return {'allowed': True, 'remaining': effectiveLimit - clientData['count']}

    def getRateLimitState(self, clientId: str) -> Dict[str, Any]:
        now = time.time() * 1000
        windowMs = 60000
        limit = self.config.workersHardening.rateLimit.requestsPerMinute
        burst = self.config.workersHardening.rateLimit.burstAllowance
        effectiveLimit = limit + burst

        clientData = self.rateLimitStore.get(clientId)
        
        if not clientData:
            return {'remaining': effectiveLimit, 'resetAt': now + windowMs}

        resetAt = clientData['windowStart'] + windowMs
        remaining = max(0, effectiveLimit - clientData['count'])
        
        return {'remaining': remaining, 'resetAt': resetAt}

    # ═══ Circuit Breaker (M9) ═══

    def getCircuitBreakerState(self) -> Literal['closed', 'open', 'half-open']:
        now = time.time() * 1000
        windowMs = self.config.workersHardening.circuitBreaker.windowMs

        if now - self.circuitBreakerLastCheck >= windowMs:
            self._evaluateCircuitBreaker()
            self.circuitBreakerLastCheck = now

        return self.circuitBreakerState

    def _evaluateCircuitBreaker(self) -> None:
        threshold = self.config.workersHardening.circuitBreaker.failureThreshold
        
        if self.circuitBreakerState == 'closed':
            if self.circuitBreakerFailures >= threshold:
                self.circuitBreakerState = 'open'
        elif self.circuitBreakerState == 'open':
            self.circuitBreakerState = 'half-open'
            self.circuitBreakerSuccesses = 0
        elif self.circuitBreakerState == 'half-open':
            halfOpenRequests = self.config.workersHardening.circuitBreaker.halfOpenRequests
            if self.circuitBreakerSuccesses >= halfOpenRequests:
                self.circuitBreakerState = 'closed'
                self.circuitBreakerFailures = 0

        self.metrics.circuitBreakerState = self.circuitBreakerState

    def recordFailure(self) -> None:
        self.circuitBreakerFailures += 1

    def recordSuccess(self) -> None:
        if self.circuitBreakerState == 'half-open':
            self.circuitBreakerSuccesses += 1
        self.circuitBreakerFailures = max(0, self.circuitBreakerFailures - 1)

    # ═══ Metrics ═══

    def getMetrics(self) -> SecurityMetrics:
        return SecurityMetrics(
            requestsProcessed=self.metrics.requestsProcessed,
            injectionsDetected=self.metrics.injectionsDetected,
            injectionsBlocked=self.metrics.injectionsBlocked,
            outputsSanitized=self.metrics.outputsSanitized,
            requestsByClient=dict(self.metrics.requestsByClient),
            rateLimitHits=self.metrics.rateLimitHits,
            circuitBreakerState=self.metrics.circuitBreakerState,
            avgPromptInjectionScore=self.metrics.avgPromptInjectionScore,
        )

    # ═══ Utility Methods ═══

    def updatePatterns(self, patterns: List[str]) -> None:
        self.config.promptInjection.patterns = patterns
        self._compilePatterns()

    def setPromptInjectionEnabled(self, enabled: bool) -> None:
        self.config.promptInjection.enabled = enabled

    def setSanitizeOutput(self, enabled: bool) -> None:
        self.config.promptInjection.sanitizeOutput = enabled

    def setMaxInputTokens(self, tokens: int) -> None:
        self.config.promptInjection.maxInputTokens = tokens

    def resetMetrics(self) -> None:
        self.metrics = SecurityMetrics()
        self.rateLimitStore.clear()
        self.circuitBreakerState = 'closed'
        self.circuitBreakerFailures = 0
        self.circuitBreakerSuccesses = 0
        self.circuitBreakerLastCheck = 0


# ═══ Export for Testing ═══

# Default instance for easy importing
securityMiddleware = SecurityMiddleware(DEFAULT_SECURITY_CONFIG)


def createSecurityMiddleware(config: Optional[SecurityConfig] = None) -> SecurityMiddleware:
    return SecurityMiddleware(config)


# For backward compatibility with test imports
__all__ = [
    'SecurityMiddleware',
    'SecurityConfig',
    'SecurityContext',
    'SecurityResult',
    'SecurityMetrics',
    'PromptInjectionConfig',
    'WorkersHardeningConfig',
    'RateLimitConfig',
    'CircuitBreakerConfig',
    'createSecurityMiddleware',
    'securityMiddleware',
    'DEFAULT_SECURITY_CONFIG',
]