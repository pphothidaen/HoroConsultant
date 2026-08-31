import Foundation
import CryptoKit

// MARK: - Closed Request & Result Schemas

/// Closed request schema for the Agent Broker (agent-broker-request-v1).
public struct AgentBrokerRequest: Codable, Equatable {
    public let schemaVersion: String
    public let requestId: String
    public let alias: String
    public let action: String
    public let commandArgv: [String]
    public let leaseId: String?
    public let timeoutSeconds: Int?
    public let callerContext: [String: String]?

    public enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case requestId = "request_id"
        case alias
        case action
        case commandArgv = "command_argv"
        case leaseId = "lease_id"
        case timeoutSeconds = "timeout_seconds"
        case callerContext = "caller_context"
    }

    public init(
        schemaVersion: String = "agent-broker-request-v1",
        requestId: String,
        alias: String,
        action: String = "execute",
        commandArgv: [String],
        leaseId: String? = nil,
        timeoutSeconds: Int? = nil,
        callerContext: [String: String]? = nil
    ) {
        self.schemaVersion = schemaVersion
        self.requestId = requestId
        self.alias = alias
        self.action = action
        self.commandArgv = commandArgv
        self.leaseId = leaseId
        self.timeoutSeconds = timeoutSeconds
        self.callerContext = callerContext
    }
}

/// Execution status reported by the broker.
public enum AgentBrokerStatus: String, Codable {
    case success = "SUCCESS"
    case failed = "FAILED"
    case rejected = "REJECTED"
    case cancelled = "CANCELLED"
    case timeout = "TIMEOUT"
    case crashed = "CRASHED"
}

/// Closed result schema returned by the Agent Broker (agent-broker-result-v1).
public struct AgentBrokerResult: Codable, Equatable {
    public let schemaVersion: String
    public let requestId: String
    public let status: String
    public let exitCode: Int
    public let sanitizedOutputDigest: String
    public let durationMs: Int
    public let errorCode: String?
    public let errorMessage: String?

    public enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case requestId = "request_id"
        case status
        case exitCode = "exit_code"
        case sanitizedOutputDigest = "sanitized_output_digest"
        case durationMs = "duration_ms"
        case errorCode = "error_code"
        case errorMessage = "error_message"
    }

    public init(
        schemaVersion: String = "agent-broker-result-v1",
        requestId: String,
        status: String,
        exitCode: Int,
        sanitizedOutputDigest: String,
        durationMs: Int,
        errorCode: String? = nil,
        errorMessage: String? = nil
    ) {
        self.schemaVersion = schemaVersion
        self.requestId = requestId
        self.status = status
        self.exitCode = exitCode
        self.sanitizedOutputDigest = sanitizedOutputDigest
        self.durationMs = durationMs
        self.errorCode = errorCode
        self.errorMessage = errorMessage
    }
}

/// Validation result representation.
public struct BrokerValidationResult: Equatable {
    public let isValid: Bool
    public let errorCode: String?
    public let errorMessage: String?

    public static func valid() -> BrokerValidationResult {
        return BrokerValidationResult(isValid: true, errorCode: nil, errorMessage: nil)
    }

    public static func invalid(code: String, message: String) -> BrokerValidationResult {
        return BrokerValidationResult(isValid: false, errorCode: code, errorMessage: message)
    }
}

/// Schema validator for fail-closed request payloads.
public enum BrokerSchemaValidator {
    public static let allowedAliases: Set<String> = [
        "agy1", "agy2", "agy3", "agy4",
        "codex1", "codex2", "codex3"
    ]

    public static let allowedKeys: Set<String> = [
        "schema_version", "request_id", "alias", "action", "command_argv",
        "lease_id", "timeout_seconds", "caller_context"
    ]

    public static func validateClosedRequest(_ data: Data) -> BrokerValidationResult {
        guard let jsonObject = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return .invalid(code: "SCHEMA_INVALID_JSON", message: "Payload is not valid JSON")
        }

        let keys = Set(jsonObject.keys)
        let unknownKeys = keys.subtracting(allowedKeys)
        if !unknownKeys.isEmpty {
            return .invalid(code: "SCHEMA_UNKNOWN_PROPERTY", message: "Unknown properties: \(unknownKeys)")
        }

        guard let _ = jsonObject["schema_version"] as? String,
              let _ = jsonObject["request_id"] as? String,
              let alias = jsonObject["alias"] as? String,
              let _ = jsonObject["action"] as? String,
              let _ = jsonObject["command_argv"] as? [String] else {
            return .invalid(code: "SCHEMA_MISSING_REQUIRED_PROPERTY", message: "Missing required properties")
        }

        if !allowedAliases.contains(alias) {
            return .invalid(code: "UNAUTHORIZED_ALIAS", message: "Alias '\(alias)' is not authorized")
        }

        return .valid()
    }
}
