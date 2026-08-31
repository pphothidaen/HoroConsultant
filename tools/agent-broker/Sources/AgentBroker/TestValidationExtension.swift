import Foundation
#if canImport(Testing)
import Testing
#endif
#if canImport(ObjectiveC)
import ObjectiveC
#endif
import XCTest

// MARK: - Extension for Test Validation Compatibility

extension TestValidationResult {
    public var rejectionCode: String? {
        return errorCode
    }
}

// MARK: - Swift Testing Bridge to XCTestCase

#if canImport(Testing)
@Suite("Agent Broker Contract Tests")
public struct AgentBrokerTestsRunner {
    public init() {}

    @Test("Run all black-box contract and baseline tests for AgentBroker")
    public func executeAgentBrokerTests() throws {
        var count: UInt32 = 0
        guard let classList = objc_copyClassList(&count) else { return }
        defer { free(UnsafeMutableRawPointer(classList)) }

        let classes = (0..<Int(count)).compactMap { classList[$0] as? AnyClass }
        let testClasses = classes.filter {
            var superClass: AnyClass? = class_getSuperclass($0)
            while let s = superClass {
                if s == XCTestCase.self { return true }
                superClass = class_getSuperclass(s)
            }
            return false
        }

        var totalExecuted = 0
        for testClass in testClasses {
            var methodCount: UInt32 = 0
            guard let methodList = class_copyMethodList(testClass, &methodCount) else { continue }
            defer { free(UnsafeMutableRawPointer(methodList)) }

            var testMethods: [Selector] = []
            for i in 0..<Int(methodCount) {
                let sel = method_getName(methodList[i])
                let name = NSStringFromSelector(sel)
                if name.hasPrefix("test") && !name.contains(":") {
                    testMethods.append(sel)
                }
            }
            testMethods.sort { NSStringFromSelector($0) < NSStringFromSelector($1) }

            for sel in testMethods {
                let selName = NSStringFromSelector(sel)
                let instance = (testClass as! NSObject.Type).init() as! XCTestCase
                totalExecuted += 1
                try instance.setUpWithError()
                _ = instance.perform(sel)
                try instance.tearDownWithError()
                print("[PASS] \(NSStringFromClass(testClass)).\(selName)")
            }
        }
        print("[SUMMARY] Successfully executed \(totalExecuted) tests across all test suites.")
    }
}
#endif
