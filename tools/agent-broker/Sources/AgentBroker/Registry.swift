import Foundation

// MARK: - Alias and Provider Registry

public enum ProviderType: String, Codable {
    case agy = "agy"
    case codex = "codex"
}

public enum RootPool: String, Codable {
    case rootA = "root_a"
    case rootB = "root_b"
}

public struct AccountDescriptor: Equatable {
    public let alias: String
    public let provider: ProviderType
    public let rootPool: RootPool
    public let homeDirectory: String
    public let binaryPath: String
    public let defaultCapacity: Int

    public init(
        alias: String,
        provider: ProviderType,
        rootPool: RootPool,
        homeDirectory: String,
        binaryPath: String,
        defaultCapacity: Int
    ) {
        self.alias = alias
        self.provider = provider
        self.rootPool = rootPool
        self.homeDirectory = homeDirectory
        self.binaryPath = binaryPath
        self.defaultCapacity = defaultCapacity
    }
}

public final class AccountRegistry {
    public static let shared = AccountRegistry()

    private let accounts: [String: AccountDescriptor]

    public init(baseHome: String = NSHomeDirectory()) {
        self.accounts = [
            "agy1": AccountDescriptor(
                alias: "agy1",
                provider: .agy,
                rootPool: .rootB,
                homeDirectory: "\(baseHome)/.ai-accounts/agy/account1",
                binaryPath: "\(baseHome)/.local/bin/agy1",
                defaultCapacity: 3
            ),
            "agy2": AccountDescriptor(
                alias: "agy2",
                provider: .agy,
                rootPool: .rootB,
                homeDirectory: "\(baseHome)/.ai-accounts/agy/account2",
                binaryPath: "\(baseHome)/.local/bin/agy2",
                defaultCapacity: 3
            ),
            "agy3": AccountDescriptor(
                alias: "agy3",
                provider: .agy,
                rootPool: .rootB,
                homeDirectory: "\(baseHome)/.ai-accounts/agy/account3",
                binaryPath: "\(baseHome)/.local/bin/agy3",
                defaultCapacity: 3
            ),
            "codex1": AccountDescriptor(
                alias: "codex1",
                provider: .codex,
                rootPool: .rootA,
                homeDirectory: "\(baseHome)/.ai-accounts/codex/account1",
                binaryPath: "\(baseHome)/.local/bin/codex1",
                defaultCapacity: 2
            ),
            "codex2": AccountDescriptor(
                alias: "codex2",
                provider: .codex,
                rootPool: .rootA,
                homeDirectory: "\(baseHome)/.ai-accounts/codex/account2",
                binaryPath: "\(baseHome)/.local/bin/codex2",
                defaultCapacity: 2
            ),
            "codex3": AccountDescriptor(
                alias: "codex3",
                provider: .codex,
                rootPool: .rootA,
                homeDirectory: "\(baseHome)/.ai-accounts/codex/account3",
                binaryPath: "\(baseHome)/.local/bin/codex3",
                defaultCapacity: 2
            )
        ]
    }

    public func account(for alias: String) -> AccountDescriptor? {
        return accounts[alias]
    }

    public func allAliases() -> [String] {
        return Array(accounts.keys).sorted()
    }

    public func isAuthorized(alias: String) -> Bool {
        return accounts[alias] != nil
    }

    public func rootPool(for alias: String) -> RootPool? {
        return accounts[alias]?.rootPool
    }
}
