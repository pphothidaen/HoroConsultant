import Foundation
import Security
import Darwin

/*
 A deliberately small account boundary.  Callers select an account alias, not
 a keychain, provider executable, or credential source.
 */

private struct Account: Equatable {
    let alias: String
    let provider: String
}

private let accounts: [String: Account] = [
    "agy1": Account(alias: "agy1", provider: "agy"),
    "agy2": Account(alias: "agy2", provider: "agy"),
    "agy3": Account(alias: "agy3", provider: "agy"),
    "agy4": Account(alias: "agy4", provider: "agy"),
    "codex1": Account(alias: "codex1", provider: "codex"),
    "codex2": Account(alias: "codex2", provider: "codex"),
    "codex3": Account(alias: "codex3", provider: "codex"),
]

private enum BrokerError: Error {
    case rejected
    case keychainUnavailable
    case providerUnavailable
}

private func status(_ message: String) {
    // Public output is deliberately generic: aliases, paths, and credentials
    // are all potentially sensitive operational metadata.
    print(message)
}

private func accountRoot() throws -> URL {
    #if ACCOUNT_BROKER_TESTING
    guard let configured = ProcessInfo.processInfo.environment["AI_ACCOUNT_BROKER_TEST_ROOT"],
          !configured.isEmpty else {
        throw BrokerError.rejected
    }
    return URL(fileURLWithPath: configured, isDirectory: true)
    #else
    return FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent(".horo-consultant", isDirectory: true)
        .appendingPathComponent("ai-accounts", isDirectory: true)
    #endif
}

private func isSymlink(_ url: URL) -> Bool {
    var information = stat()
    guard lstat(url.path, &information) == 0 else {
        return false
    }
    return (information.st_mode & S_IFMT) == S_IFLNK
}

private func makeOwnerOnlyDirectory(_ url: URL) throws {
    if isSymlink(url) {
        throw BrokerError.rejected
    }
    let manager = FileManager.default
    var isDirectory: ObjCBool = false
    if manager.fileExists(atPath: url.path, isDirectory: &isDirectory) {
        guard isDirectory.boolValue else {
            throw BrokerError.rejected
        }
    } else {
        try manager.createDirectory(at: url, withIntermediateDirectories: true,
                                    attributes: [.posixPermissions: 0o700])
    }
    try manager.setAttributes([.posixPermissions: 0o700], ofItemAtPath: url.path)
    let attributes = try manager.attributesOfItem(atPath: url.path)
    guard let permissions = attributes[.posixPermissions] as? NSNumber,
          permissions.intValue & 0o077 == 0 else {
        throw BrokerError.rejected
    }
}

private func isolatedEnvironment(for account: Account) throws -> [String: String] {
    let root = try accountRoot().appendingPathComponent(account.alias, isDirectory: true)
    let home = root.appendingPathComponent("home", isDirectory: true)
    let xdg = root.appendingPathComponent("xdg", isDirectory: true)
    let config = xdg.appendingPathComponent("config", isDirectory: true)
    let cache = xdg.appendingPathComponent("cache", isDirectory: true)
    let data = xdg.appendingPathComponent("data", isDirectory: true)
    let temporary = root.appendingPathComponent("tmp", isDirectory: true)
    let providerHome = root.appendingPathComponent(account.provider, isDirectory: true)

    for directory in [root, home, xdg, config, cache, data, temporary, providerHome] {
        try makeOwnerOnlyDirectory(directory)
    }

    let ambient = ProcessInfo.processInfo.environment
    var environment: [String: String] = [:]
    for name in ["PATH", "LANG", "LC_ALL"] {
        if let value = ambient[name] {
            environment[name] = value
        }
    }
    #if ACCOUNT_BROKER_TESTING
    // These are synthetic fixture controls, not production credential inputs.
    for name in ["PROVIDER_CAPTURE", "PROVIDER_MODE"] {
        if let value = ambient[name] {
            environment[name] = value
        }
    }
    #endif
    environment["HOME"] = home.path
    environment["XDG_CONFIG_HOME"] = config.path
    environment["XDG_CACHE_HOME"] = cache.path
    environment["XDG_DATA_HOME"] = data.path
    environment["TMPDIR"] = temporary.path
    environment["TMP"] = temporary.path
    environment["TEMP"] = temporary.path
    environment[account.provider == "agy" ? "AGY_HOME" : "CODEX_HOME"] = providerHome.path
    return environment
}

// SecKeychainUnlock is deprecated but remains required for compatibility with
// existing login keychains.  Keep this legacy API isolated from all lookup and
// process-handling logic; password bytes never enter argv, environment, or logs.
private func unlockKeychainCompatibility(_ keychain: SecKeychain, password: Data) -> OSStatus {
    return password.withUnsafeBytes { bytes in
        SecKeychainUnlock(keychain, UInt32(bytes.count), bytes.baseAddress, true)
    }
}

private func lookupSecretWithSecurityFramework(alias: String) throws -> Data {
    // Query all items matching this service and account — exactly one must
    // exist.  A duplicate or absent item indicates an ambiguous keychain state
    // that must be rejected fail-closed.
    let query: [CFString: Any] = [
        kSecClass: kSecClassGenericPassword,
        kSecAttrService: "com.horoconsultant.ai-account-keychain-broker",
        kSecAttrAccount: alias,
        kSecReturnData: true,
        kSecMatchLimit: kSecMatchLimitAll,
    ]
    var result: CFTypeRef?
    guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
          let items = result as? [Data] else {
        throw BrokerError.keychainUnavailable
    }
    guard items.count == 1, let secret = items.first, !secret.isEmpty else {
        // Reject unless exactly one non-empty secret is present.
        throw BrokerError.keychainUnavailable
    }

    var keychain: SecKeychain?
    guard SecKeychainCopyDefault(&keychain) == errSecSuccess, let keychain else {
        throw BrokerError.keychainUnavailable
    }
    var state: SecKeychainStatus = 0
    guard SecKeychainGetStatus(keychain, &state) == errSecSuccess,
          state & SecKeychainStatus(kSecUnlockStateStatus) != 0 else {
        throw BrokerError.keychainUnavailable
    }
    // Compatibility call remains local to this function.  A failure is not
    // recoverable through another alias or environment credential.
    guard unlockKeychainCompatibility(keychain, password: secret) == errSecSuccess else {
        throw BrokerError.keychainUnavailable
    }
    return secret
}

#if ACCOUNT_BROKER_TESTING
private func runQuietly(executable: String, arguments: [String], input: Data? = nil) throws -> (Int32, Data) {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: executable)
    process.arguments = arguments
    process.environment = ProcessInfo.processInfo.environment
    let output = Pipe()
    process.standardOutput = output
    process.standardError = Pipe()
    if let input {
        let stdin = Pipe()
        process.standardInput = stdin
        try process.run()
        stdin.fileHandleForWriting.write(input)
        stdin.fileHandleForWriting.closeFile()
    } else {
        process.standardInput = FileHandle.nullDevice
        try process.run()
    }
    process.waitUntilExit()
    return (process.terminationStatus, output.fileHandleForReading.readDataToEndOfFile())
}

private func lookupSecretForTesting(alias: String) throws -> Data {
    guard let security = ProcessInfo.processInfo.environment["AI_ACCOUNT_BROKER_TEST_SECURITY"],
          !security.isEmpty else {
        // A test broker must be hermetic — never fall back to the real
        // Security.framework.
        throw BrokerError.rejected
    }
    let lookup = try runQuietly(
        executable: security,
        arguments: ["find-generic-password", "-s", "com.horoconsultant.ai-account-keychain-broker", "-a", alias, "-w"]
    )
    guard lookup.0 == 0 else {
        throw BrokerError.keychainUnavailable
    }
    // Exactly one non-empty line of output must be present.  Multiple lines
    // indicate ambiguous items; structured output (JSON) indicates a
    // non-canonical binding.  Both must be rejected fail-closed.
    let lines = String(data: lookup.1, encoding: .utf8)?
        .split(separator: "\n", omittingEmptySubsequences: true) ?? []
    guard lines.count == 1, let secretLine = lines.first else {
        throw BrokerError.keychainUnavailable
    }
    let secretText = String(secretLine)
    guard !secretText.isEmpty, !secretText.hasPrefix("{") else {
        throw BrokerError.keychainUnavailable
    }
    let secret = secretText.data(using: .utf8) ?? Data()
    guard !secret.isEmpty else {
        throw BrokerError.keychainUnavailable
    }
    let keychain = try accountRoot().appendingPathComponent(alias).appendingPathComponent("keychain").path
    var password = secret
    password.append(0x0A)
    let unlock = try runQuietly(executable: security, arguments: ["unlock-keychain", "-p", keychain], input: password)
    guard unlock.0 == 0 else {
        throw BrokerError.keychainUnavailable
    }
    return secret
}
#endif

private func providerExecutable(for account: Account, environment: [String: String]) -> URL? {
    #if ACCOUNT_BROKER_TESTING
    guard let path = environment["PATH"] else { return nil }
    for directory in path.split(separator: ":") {
        let candidate = URL(fileURLWithPath: String(directory)).appendingPathComponent(account.provider)
        if FileManager.default.isExecutableFile(atPath: candidate.path), !isSymlink(candidate) {
            return candidate
        }
    }
    return nil
    #else
    // Provider locations are fixed by the broker build; callers cannot replace
    // them through command arguments or environment variables.
    return URL(fileURLWithPath: account.provider == "agy" ? "/usr/local/bin/agy" : "/usr/local/bin/codex")
    #endif
}

private func sanitizeAndDiscard(_ data: Data, secret: Data) {
    // Provider streams are private operational metadata.  The broker reads
    // them to verify no secret leaks, then discards them without relay.
    guard let rendered = String(data: data, encoding: .utf8) else { return }
    guard let secretText = String(data: secret, encoding: .utf8), !secretText.isEmpty else { return }
    if rendered.contains(secretText) {
        status("[WARNING] provider stream contained credential material")
    }
}

private func launchProvider(account: Account, arguments: [String], secret: Data) throws -> Int32 {
    let environment = try isolatedEnvironment(for: account)
    guard let executable = providerExecutable(for: account, environment: environment) else {
        throw BrokerError.providerUnavailable
    }
    let process = Process()
    process.executableURL = executable
    process.arguments = arguments
    process.environment = environment
    process.standardInput = FileHandle.nullDevice
    let stdout = Pipe()
    let stderr = Pipe()
    process.standardOutput = stdout
    process.standardError = stderr
    try process.run()
    process.waitUntilExit()
    // Capture and scan for secret leaks, but do NOT relay provider output.
    sanitizeAndDiscard(stdout.fileHandleForReading.readDataToEndOfFile(), secret: secret)
    sanitizeAndDiscard(stderr.fileHandleForReading.readDataToEndOfFile(), secret: secret)
    return process.terminationStatus
}

private func main() -> Int32 {
    let arguments = CommandLine.arguments
    guard arguments.count >= 3, arguments[2] == "--", let account = accounts[arguments[1]] else {
        status("[ERROR] request rejected")
        return 64
    }
    let providerArguments = Array(arguments.dropFirst(3))
    do {
        #if ACCOUNT_BROKER_TESTING
        let secret = try lookupSecretForTesting(alias: account.alias)
        #else
        let secret = try lookupSecretWithSecurityFramework(alias: account.alias)
        #endif
        let result = try launchProvider(account: account, arguments: providerArguments, secret: secret)
        if result != 0 {
            status("[ERROR] provider exited unsuccessfully")
        }
        return result
    } catch BrokerError.keychainUnavailable {
        status("[ERROR] account admission unavailable")
        return 77
    } catch {
        status("[ERROR] account admission unavailable")
        return 78
    }
}

exit(main())
