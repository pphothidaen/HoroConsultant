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
        .executableTarget(
            name: "AgentBroker",
            dependencies: [],
            path: "Sources/AgentBroker"
        ),
        .testTarget(
            name: "AgentBrokerTests",
            dependencies: ["AgentBroker"],
            path: "Tests/AgentBrokerTests"
        )
    ]
)
