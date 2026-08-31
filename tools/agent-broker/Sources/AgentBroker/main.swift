import Foundation
import XCTest

// MARK: - CLI Entry Point

func runCLI() {
    let args = CommandLine.arguments

    if args.contains("--help") || args.contains("-h") {
        print("Usage: agent-broker [--stdin | --request <json>]")
        print("macOS Swift Agent Broker for isolated multi-account execution.")
        exit(0)
    }

    if args.contains("--version") || args.contains("-v") {
        print("agent-broker version 1.0.0 (BRK-B1-010)")
        exit(0)
    }

    var inputData: Data?

    if let reqIndex = args.firstIndex(of: "--request"), reqIndex + 1 < args.count {
        inputData = args[reqIndex + 1].data(using: .utf8)
    } else {
        inputData = FileHandle.standardInput.readDataToEndOfFile()
    }

    guard let data = inputData, !data.isEmpty else {
        let result = AgentBrokerResult(
            requestId: "unknown",
            status: AgentBrokerStatus.rejected.rawValue,
            exitCode: 1,
            sanitizedOutputDigest: String(repeating: "0", count: 64),
            durationMs: 0,
            errorCode: "EMPTY_REQUEST_PAYLOAD",
            errorMessage: "No request payload provided via stdin or --request"
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        if let output = try? encoder.encode(result), let str = String(data: output, encoding: .utf8) {
            print(str)
        }
        exit(1)
    }

    let core = AgentBrokerCore()
    let result = core.handleRequestData(data)

    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
    if let outputData = try? encoder.encode(result), let outputStr = String(data: outputData, encoding: .utf8) {
        print(outputStr)
    }

    exit(Int32(result.exitCode))
}

runCLI()
