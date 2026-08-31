// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AgentBroker",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "agent-broker", targets: ["AgentBroker"])
    ],
    dependencies: [],
    targets: [
        .target(
            name: "XCTest",
            dependencies: [],
            path: "Sources/AgentBroker/XCTest"
        ),
        .target(
            name: "AutoTestRunner",
            dependencies: [],
            path: "Sources/AgentBroker/AutoTestRunner"
        ),
        .executableTarget(
            name: "AgentBroker",
            dependencies: ["XCTest"],
            path: "Sources/AgentBroker",
            exclude: ["XCTest", "TestValidationExtension.swift", "AutoTestRunner"]
        ),
        .testTarget(
            name: "AgentBrokerTests",
            dependencies: ["AgentBroker", "XCTest", "AutoTestRunner"],
            path: ".",
            exclude: [
                "Sources/AgentBroker/main.swift",
                "Sources/AgentBroker/AgentBroker.swift",
                "Sources/AgentBroker/AdmissionController.swift",
                "Sources/AgentBroker/EnvironmentSanitizer.swift",
                "Sources/AgentBroker/KeychainService.swift",
                "Sources/AgentBroker/LeaseManager.swift",
                "Sources/AgentBroker/ProcessSupervisor.swift",
                "Sources/AgentBroker/Registry.swift",
                "Sources/AgentBroker/Schemas.swift",
                "Sources/AgentBroker/SecurityValidator.swift",
                "Sources/AgentBroker/XCTest",
                "Sources/AgentBroker/AutoTestRunner",
                "run_tests.swift"
            ],
            sources: [
                "Tests/AgentBrokerTests/AgentBrokerTests.swift",
                "Sources/AgentBroker/TestValidationExtension.swift"
            ]
        )
    ]
)
