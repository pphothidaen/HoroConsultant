import Foundation
#if canImport(ObjectiveC)
import ObjectiveC
#endif

// MARK: - XCTest Compatibility Shim for Standalone Toolchains

open class XCTestCase: NSObject {
    public override init() {
        super.init()
    }

    open func setUp() throws {}
    open func tearDown() throws {}

    open func setUpWithError() throws {
        try setUp()
    }

    open func tearDownWithError() throws {
        try tearDown()
    }
}

public struct XCTIssue {
    public enum IssueType {
        case assertionFailure
        case thrownError
        case uncaughtException
        case performanceRegression
        case system
        case unmatchedExpectedFailure
        case unknown
    }

    public let type: IssueType
    public let compactDescription: String
    public let detailedDescription: String?
    public let sourceCodeContext: XCTSourceCodeContext
    public let associatedError: Error?
    public let attachments: [XCTAttachment]

    public init(
        type: IssueType = .assertionFailure,
        compactDescription: String,
        detailedDescription: String? = nil,
        sourceCodeContext: XCTSourceCodeContext = XCTSourceCodeContext(),
        associatedError: Error? = nil,
        attachments: [XCTAttachment] = []
    ) {
        self.type = type
        self.compactDescription = compactDescription
        self.detailedDescription = detailedDescription
        self.sourceCodeContext = sourceCodeContext
        self.associatedError = associatedError
        self.attachments = attachments
    }
}

public struct XCTSourceCodeLocation {
    public let fileURL: URL
    public let lineNumber: Int

    public init(fileURL: URL, lineNumber: Int) {
        self.fileURL = fileURL
        self.lineNumber = lineNumber
    }
}

public struct XCTSourceCodeFrame {
    public let address: UInt64

    public init(address: UInt64 = 0) {
        self.address = address
    }

    public func symbolInfo() throws -> XCTSourceCodeSymbolInfo {
        return XCTSourceCodeSymbolInfo(imageName: "AgentBrokerTests", symbolName: "test", location: nil)
    }
}

public struct XCTSourceCodeSymbolInfo {
    public let imageName: String
    public let symbolName: String
    public let location: XCTSourceCodeLocation?

    public init(imageName: String, symbolName: String, location: XCTSourceCodeLocation? = nil) {
        self.imageName = imageName
        self.symbolName = symbolName
        self.location = location
    }
}

public struct XCTSourceCodeContext {
    public let callStack: [XCTSourceCodeFrame]
    public let location: XCTSourceCodeLocation?

    public init(callStack: [XCTSourceCodeFrame] = [], location: XCTSourceCodeLocation? = nil) {
        self.callStack = callStack
        self.location = location
    }
}

public final class XCTAttachment: NSObject {
    public let name: String?
    public let uniformTypeIdentifier: String

    public init(name: String? = nil, uniformTypeIdentifier: String = "public.data") {
        self.name = name
        self.uniformTypeIdentifier = uniformTypeIdentifier
        super.init()
    }
}

public final class XCTExpectedFailure: NSObject {
    public let issue: XCTIssue
    public let failureReason: String?

    public init(issue: XCTIssue, failureReason: String? = nil) {
        self.issue = issue
        self.failureReason = failureReason
        super.init()
    }
}

public class XCTestSuite: NSObject {
    public let name: String
    public init(name: String = "AgentBrokerTestSuite") {
        self.name = name
        super.init()
    }
}

public protocol XCTestObservation: AnyObject {
    func testBundleWillStart(_ testBundle: Bundle)
    func testSuiteWillStart(_ testSuite: XCTestSuite)
    func testCaseWillStart(_ testCase: XCTestCase)
    func testCaseDidFinish(_ testCase: XCTestCase)
    func testSuiteDidFinish(_ testSuite: XCTestSuite)
    func testBundleDidFinish(_ testBundle: Bundle)
}

public extension XCTestObservation {
    func testBundleWillStart(_ testBundle: Bundle) {}
    func testSuiteWillStart(_ testSuite: XCTestSuite) {}
    func testCaseWillStart(_ testCase: XCTestCase) {}
    func testCaseDidFinish(_ testCase: XCTestCase) {}
    func testSuiteDidFinish(_ testSuite: XCTestSuite) {}
    func testBundleDidFinish(_ testBundle: Bundle) {}
}

public final class XCTestObservationCenter: NSObject {
    public static let shared = XCTestObservationCenter()
    private var observers: [XCTestObservation] = []

    public func addTestObserver(_ observer: XCTestObservation) {
        observers.append(observer)
    }

    public func removeTestObserver(_ observer: XCTestObservation) {
        observers.removeAll { $0 === observer }
    }
}

// MARK: - Assertions

public func XCTFail(_ message: String = "", file: StaticString = #filePath, line: UInt = #line) {
    let msg = message.isEmpty ? "Assertion failed" : message
    print("[FAIL] \(file):\(line) - \(msg)")
    exit(1)
}

public func XCTAssertEqual<T: Equatable>(
    _ expression1: @autoclosure () throws -> T,
    _ expression2: @autoclosure () throws -> T,
    _ message: @autoclosure () -> String = "",
    file: StaticString = #filePath,
    line: UInt = #line
) {
    do {
        let val1 = try expression1()
        let val2 = try expression2()
        if val1 != val2 {
            let customMsg = message()
            let detail = customMsg.isEmpty ? "(\"\(val1)\") is not equal to (\"\(val2)\")" : "\(customMsg) - (\"\(val1)\") is not equal to (\"\(val2)\")"
            print("[FAIL] \(file):\(line) - XCTAssertEqual failed: \(detail)")
            exit(1)
        }
    } catch {
        print("[FAIL] \(file):\(line) - XCTAssertEqual threw unexpected error: \(error)")
        exit(1)
    }
}

public func XCTAssertTrue(
    _ expression: @autoclosure () throws -> Bool,
    _ message: @autoclosure () -> String = "",
    file: StaticString = #filePath,
    line: UInt = #line
) {
    do {
        let val = try expression()
        if !val {
            let customMsg = message()
            let detail = customMsg.isEmpty ? "Expression is false" : customMsg
            print("[FAIL] \(file):\(line) - XCTAssertTrue failed: \(detail)")
            exit(1)
        }
    } catch {
        print("[FAIL] \(file):\(line) - XCTAssertTrue threw unexpected error: \(error)")
        exit(1)
    }
}

public func XCTAssertFalse(
    _ expression: @autoclosure () throws -> Bool,
    _ message: @autoclosure () -> String = "",
    file: StaticString = #filePath,
    line: UInt = #line
) {
    do {
        let val = try expression()
        if val {
            let customMsg = message()
            let detail = customMsg.isEmpty ? "Expression is true" : customMsg
            print("[FAIL] \(file):\(line) - XCTAssertFalse failed: \(detail)")
            exit(1)
        }
    } catch {
        print("[FAIL] \(file):\(line) - XCTAssertFalse threw unexpected error: \(error)")
        exit(1)
    }
}

public func XCTAssertNil(
    _ expression: @autoclosure () throws -> Any?,
    _ message: @autoclosure () -> String = "",
    file: StaticString = #filePath,
    line: UInt = #line
) {
    do {
        let val = try expression()
        if val != nil {
            let customMsg = message()
            let detail = customMsg.isEmpty ? "Expression is not nil: \(String(describing: val))" : customMsg
            print("[FAIL] \(file):\(line) - XCTAssertNil failed: \(detail)")
            exit(1)
        }
    } catch {
        print("[FAIL] \(file):\(line) - XCTAssertNil threw unexpected error: \(error)")
        exit(1)
    }
}

// MARK: - Test Discovery & Execution Engine

#if canImport(ObjectiveC)
@_cdecl("runAllDiscoveredXCTests")
public func runAllDiscoveredXCTests() {
    var count: UInt32 = 0
    guard let classList = objc_copyClassList(&count) else { return }
    defer { free(UnsafeMutableRawPointer(classList)) }

    var testClasses: [AnyClass] = []
    for i in 0..<Int(count) {
        let cls: AnyClass = classList[i]
        let name = NSStringFromClass(cls)
        if name.contains("Test") {
            var superCls: AnyClass? = class_getSuperclass(cls)
            while let s = superCls {
                if s == XCTestCase.self {
                    testClasses.append(cls)
                    break
                }
                superCls = class_getSuperclass(s)
            }
        }
    }

    var totalTests = 0
    var totalFailures = 0
    let suiteStartTime = Date()

    print("Test Suite 'All tests' started at \(Date())")
    for testClass in testClasses {
        let className = NSStringFromClass(testClass)
        print("Test Suite '\(className)' started at \(Date())")

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
            totalTests += 1
            print("Test Case '-[\(className) \(selName)]' started.")
            let startTime = Date()
            do {
                try instance.setUpWithError()
                _ = instance.perform(sel)
                try instance.tearDownWithError()
                let elapsed = Date().timeIntervalSince(startTime)
                print(String(format: "Test Case '-[\(className) \(selName)]' passed (%.3f seconds).", elapsed))
            } catch {
                totalFailures += 1
                print("Test Case '-[\(className) \(selName)]' failed: \(error)")
            }
        }
        print("Test Suite '\(className)' passed at \(Date()).")
    }
    let totalDuration = Date().timeIntervalSince(suiteStartTime)
    print(String(format: "\t Executed %d tests, with %d failures (0 unexpected) in %.3f (%.3f) seconds", totalTests, totalFailures, totalDuration, totalDuration))
    print("Test Suite 'All tests' passed at \(Date()).")
}
#endif
