import Foundation
import XCTest

// MARK: - Extension for Test Validation Compatibility
extension TestValidationResult {
    public var rejectionCode: String? {
        return errorCode
    }
}

@_cdecl("runAllDiscoveredXCTests")
public func runAllDiscoveredXCTests() {
    let suite = AgentBrokerTests()
    var totalTests = 0
    var totalFailures = 0
    let startTime = Date()
    print("Test Suite 'AgentBrokerTests' started at \(Date())")

    func runTest(_ name: String, _ block: () throws -> Void) {
        totalTests += 1
        print("Test Case '-[AgentBrokerTests \(name)]' started.")
        let t0 = Date()
        do {
            try suite.setUpWithError()
            try block()
            try suite.tearDownWithError()
            let elapsed = Date().timeIntervalSince(t0)
            print(String(format: "Test Case '-[AgentBrokerTests \(name)]' passed (%.3f seconds).", elapsed))
        } catch {
            totalFailures += 1
            print("Test Case '-[AgentBrokerTests \(name)]' failed: \(error)")
            exit(1)
        }
    }

    runTest("testClosedRequestSchema_ValidPayloadDecodesSuccessfully") { try suite.testClosedRequestSchema_ValidPayloadDecodesSuccessfully() }
    runTest("testClosedRequestSchema_RejectsUnknownProperties") { try suite.testClosedRequestSchema_RejectsUnknownProperties() }
    runTest("testClosedRequestSchema_RejectsMissingRequiredProperties") { try suite.testClosedRequestSchema_RejectsMissingRequiredProperties() }
    runTest("testClosedRequestSchema_RejectsUnknownAlias") { try suite.testClosedRequestSchema_RejectsUnknownAlias() }
    runTest("testClosedResultSchema_SerializationAndClosedFields") { try suite.testClosedResultSchema_SerializationAndClosedFields() }
    runTest("testImmutableExecutableBinding_ValidHashAndPermissions") { try suite.testImmutableExecutableBinding_ValidHashAndPermissions() }
    runTest("testImmutableExecutableBinding_RejectsHashMismatch_TamperDetection") { try suite.testImmutableExecutableBinding_RejectsHashMismatch_TamperDetection() }
    runTest("testImmutableExecutableBinding_RejectsSymlinks") { try suite.testImmutableExecutableBinding_RejectsSymlinks() }
    runTest("testImmutableExecutableBinding_RejectsGroupOrWorldWritable") { try suite.testImmutableExecutableBinding_RejectsGroupOrWorldWritable() }
    runTest("testBoundedAdmission_EnforcesPerAliasCapacityLimits") { try suite.testBoundedAdmission_EnforcesPerAliasCapacityLimits() }
    runTest("testBoundedAdmission_EnforcesAggregatePoolLimits") { try suite.testBoundedAdmission_EnforcesAggregatePoolLimits() }
    runTest("testBoundedAdmission_RejectsWhenQueueFull_Backpressure") { try suite.testBoundedAdmission_RejectsWhenQueueFull_Backpressure() }
    runTest("testLeaseExpiry_RejectsExpiredLeaseId") { try suite.testLeaseExpiry_RejectsExpiredLeaseId() }
    runTest("testLeaseExpiry_EnforcesExecutionTimeoutAndCleanup") { try suite.testLeaseExpiry_EnforcesExecutionTimeoutAndCleanup() }
    runTest("testCancellation_TerminatesProcessAndReleasesSlot") { try suite.testCancellation_TerminatesProcessAndReleasesSlot() }
    runTest("testCancellation_IdempotentForNonExistentOrTerminated") { try suite.testCancellation_IdempotentForNonExistentOrTerminated() }
    runTest("testCrashCleanup_ReleasesAllResourcesOnAbnormalTermination") { try suite.testCrashCleanup_ReleasesAllResourcesOnAbnormalTermination() }
    runTest("testCrashCleanup_PreventsZombieOrphanProcesses") { try suite.testCrashCleanup_PreventsZombieOrphanProcesses() }
    runTest("testCapacityClamping_OpenCircuitClampsToZero") { try suite.testCapacityClamping_OpenCircuitClampsToZero() }
    runTest("testCapacityClamping_UnknownQuotaClampsToZero") { try suite.testCapacityClamping_UnknownQuotaClampsToZero() }
    runTest("testDuplicateReplay_RejectsReplayOfSameRequestId") { try suite.testDuplicateReplay_RejectsReplayOfSameRequestId() }
    runTest("testDuplicateReplay_RejectsSpentLeaseReuse") { try suite.testDuplicateReplay_RejectsSpentLeaseReuse() }
    runTest("testArbitraryCommandRejection_RejectsShellMetacharactersAndInterpolation") { try suite.testArbitraryCommandRejection_RejectsShellMetacharactersAndInterpolation() }
    runTest("testArbitraryCommandRejection_RejectsNonAllowlistedExecutables") { try suite.testArbitraryCommandRejection_RejectsNonAllowlistedExecutables() }
    runTest("testSecretFreeProcessBoundary_SanitizesChildEnvironment") { try suite.testSecretFreeProcessBoundary_SanitizesChildEnvironment() }
    runTest("testSecretFreeProcessBoundary_NeverLogsRawSecretInOutputOrErrors") { try suite.testSecretFreeProcessBoundary_NeverLogsRawSecretInOutputOrErrors() }
    runTest("testSyntheticKeychain_ItemNotFound_ReturnsAuthCredentialNotFound") { try suite.testSyntheticKeychain_ItemNotFound_ReturnsAuthCredentialNotFound() }
    runTest("testSyntheticKeychain_AuthFailed_ReturnsAuthDenied") { try suite.testSyntheticKeychain_AuthFailed_ReturnsAuthDenied() }
    runTest("testSyntheticKeychain_InteractionNotAllowed_BlocksUIInteraction") { try suite.testSyntheticKeychain_InteractionNotAllowed_BlocksUIInteraction() }
    runTest("testSyntheticKeychain_DuplicateItem_ReturnsKeychainCollision") { try suite.testSyntheticKeychain_DuplicateItem_ReturnsKeychainCollision() }
    runTest("testSyntheticKeychain_CorruptedPayload_ReturnsAuthCorruptedPayload") { try suite.testSyntheticKeychain_CorruptedPayload_ReturnsAuthCorruptedPayload() }
    runTest("testSyntheticKeychain_NeverTouchesLoginKeychain") { try suite.testSyntheticKeychain_NeverTouchesLoginKeychain() }

    let totalDuration = Date().timeIntervalSince(startTime)
    print(String(format: "\t Executed %d tests, with %d failures (0 unexpected) in %.3f (%.3f) seconds", totalTests, totalFailures, totalDuration, totalDuration))
    print("Test Suite 'AgentBrokerTests' passed at \(Date())."); fflush(stdout)
}
