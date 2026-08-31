import Foundation
import CryptoKit

// MARK: - Agent Broker Core Orchestrator

public final class AgentBrokerCore {
    public let registry: AccountRegistry
    public let admissionController: AdmissionController
    public let leaseManager: LeaseManager
    public let deduplicator: RequestDeduplicator
    public let supervisor: ProcessSupervisor
    public let keychainService: KeychainProtocol

    public init(
        registry: AccountRegistry = .shared,
        admissionController: AdmissionController = AdmissionController(),
        leaseManager: LeaseManager = LeaseManager(),
        deduplicator: RequestDeduplicator = RequestDeduplicator(),
        supervisor: ProcessSupervisor = ProcessSupervisor(),
        keychainService: KeychainProtocol = SyntheticKeychainService()
    ) {
        self.registry = registry
        self.admissionController = admissionController
        self.leaseManager = leaseManager
        self.deduplicator = deduplicator
        self.supervisor = supervisor
        self.keychainService = keychainService
    }

    public func handleRequestData(_ data: Data) -> AgentBrokerResult {
        let startTime = Date()

        // 1. Validate Closed Request Schema
        let schemaValidation = BrokerSchemaValidator.validateClosedRequest(data)
        guard schemaValidation.isValid else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: "unknown",
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: schemaValidation.errorCode,
                errorMessage: schemaValidation.errorMessage
            )
        }

        // 2. Decode Request
        let decoder = JSONDecoder()
        guard let request = try? decoder.decode(AgentBrokerRequest.self, from: data) else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: "unknown",
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: "SCHEMA_INVALID_JSON",
                errorMessage: "Failed to decode valid AgentBrokerRequest"
            )
        }

        // 3. Request Deduplication Check
        guard deduplicator.recordAndCheck(requestId: request.requestId) else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: request.requestId,
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: deduplicator.lastRejectionCode ?? "DUPLICATE_REQUEST_REJECTED",
                errorMessage: "Duplicate request ID detected within window"
            )
        }

        // 4. Validate Argv Security
        let argvValidation = CommandSecurityValidator.validateArgv(request.commandArgv)
        guard argvValidation.isValid else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: request.requestId,
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: argvValidation.errorCode,
                errorMessage: argvValidation.errorMessage
            )
        }

        // 5. Account Registry Check
        guard let account = registry.account(for: request.alias) else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: request.requestId,
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: "UNAUTHORIZED_ALIAS",
                errorMessage: "Alias '\(request.alias)' not found in registry"
            )
        }

        // 6. Lease Verification if leaseId is provided
        if let leaseId = request.leaseId {
            guard leaseManager.validateLease(leaseId: leaseId) else {
                let duration = Int(Date().timeIntervalSince(startTime) * 1000)
                return AgentBrokerResult(
                    requestId: request.requestId,
                    status: AgentBrokerStatus.rejected.rawValue,
                    exitCode: 1,
                    sanitizedOutputDigest: String(repeating: "0", count: 64),
                    durationMs: duration,
                    errorCode: leaseManager.lastErrorCode ?? "LEASE_EXPIRED",
                    errorMessage: "Lease validation failed"
                )
            }
            guard leaseManager.consumeLease(leaseId: leaseId) else {
                let duration = Int(Date().timeIntervalSince(startTime) * 1000)
                return AgentBrokerResult(
                    requestId: request.requestId,
                    status: AgentBrokerStatus.rejected.rawValue,
                    exitCode: 1,
                    sanitizedOutputDigest: String(repeating: "0", count: 64),
                    durationMs: duration,
                    errorCode: leaseManager.lastErrorCode ?? "LEASE_ALREADY_CONSUMED",
                    errorMessage: "Lease already consumed"
                )
            }
        }

        // 7. Capacity Admission Check
        guard admissionController.admit(alias: request.alias, requestId: request.requestId) else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: request.requestId,
                status: AgentBrokerStatus.rejected.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: admissionController.lastRejectionCode ?? "CAPACITY_EXCEEDED",
                errorMessage: "Capacity admission denied"
            )
        }
        defer {
            admissionController.release(alias: request.alias, requestId: request.requestId)
        }

        // 8. Keychain Query Boundary
        let keyResult = keychainService.queryCredential(alias: request.alias)
        guard keyResult.success else {
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return AgentBrokerResult(
                requestId: request.requestId,
                status: AgentBrokerStatus.failed.rawValue,
                exitCode: 1,
                sanitizedOutputDigest: String(repeating: "0", count: 64),
                durationMs: duration,
                errorCode: keyResult.errorCode ?? "AUTH_UNKNOWN_ERROR",
                errorMessage: "Keychain credential resolution failed"
            )
        }

        // 9. Prepare Environment & Execute Subprocess
        let hostEnv = ProcessInfo.processInfo.environment
        var sanitizedEnv = EnvironmentSanitizer.sanitize(
            incomingEnvironment: hostEnv,
            accountHome: account.homeDirectory
        )
        if let token = keyResult.rawSecret {
            sanitizedEnv["ACCOUNT_AUTH_TOKEN"] = token
        }

        let timeout = request.timeoutSeconds ?? 60
        let (exitCode, rawOutput, durationMs) = supervisor.executeCommand(
            processId: request.requestId,
            executablePath: account.binaryPath,
            arguments: request.commandArgv,
            environment: sanitizedEnv,
            workingDirectory: account.homeDirectory,
            timeoutSeconds: timeout
        )

        let sanitizedOutput = OutputSanitizer.sanitizeOutput(raw: rawOutput)

        return AgentBrokerResult(
            requestId: request.requestId,
            status: exitCode == 0 ? AgentBrokerStatus.success.rawValue : AgentBrokerStatus.failed.rawValue,
            exitCode: exitCode,
            sanitizedOutputDigest: sanitizedOutput.sha256Digest,
            durationMs: durationMs,
            errorCode: exitCode == 0 ? nil : "PROCESS_NONZERO_EXIT",
            errorMessage: exitCode == 0 ? nil : sanitizedOutput.sanitizedString
        )
    }
}
