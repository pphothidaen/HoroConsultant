import Foundation
import CryptoKit

// MARK: - Manifest & Command Security Validation

public struct ExecutableManifest: Equatable {
    public let executablePath: String
    public let expectedSha256: String
    public let allowedModes: [Int]
    public let requireOwnerOnly: Bool

    public init(
        executablePath: String,
        expectedSha256: String,
        allowedModes: [Int],
        requireOwnerOnly: Bool
    ) {
        self.executablePath = executablePath
        self.expectedSha256 = expectedSha256
        self.allowedModes = allowedModes
        self.requireOwnerOnly = requireOwnerOnly
    }
}

public struct FileMetadata: Equatable {
    public let path: String
    public let sha256: String
    public let posixPermissions: Int
    public let isSymlink: Bool
    public let ownerUid: Int
    public let currentProcessUid: Int

    public init(
        path: String,
        sha256: String,
        posixPermissions: Int,
        isSymlink: Bool,
        ownerUid: Int,
        currentProcessUid: Int
    ) {
        self.path = path
        self.sha256 = sha256
        self.posixPermissions = posixPermissions
        self.isSymlink = isSymlink
        self.ownerUid = ownerUid
        self.currentProcessUid = currentProcessUid
    }
}

public struct ManifestValidationResult: Equatable {
    public let isPassing: Bool
    public let rejectionCode: String?
    public let rejectionReason: String?

    public static func pass() -> ManifestValidationResult {
        return ManifestValidationResult(isPassing: true, rejectionCode: nil, rejectionReason: nil)
    }

    public static func reject(code: String, reason: String) -> ManifestValidationResult {
        return ManifestValidationResult(isPassing: false, rejectionCode: code, rejectionReason: reason)
    }
}

public enum ManifestValidator {
    public static func validate(metadata: FileMetadata, manifest: ExecutableManifest) -> ManifestValidationResult {
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

    public static func inspectFile(at path: String) throws -> FileMetadata {
        let fileManager = FileManager.default
        let url = URL(fileURLWithPath: path)
        let resourceValues = try url.resourceValues(forKeys: [.isSymbolicLinkKey])
        let isSymlink = resourceValues.isSymbolicLink ?? false

        let attributes = try fileManager.attributesOfItem(atPath: path)
        let posixPermissions = (attributes[.posixPermissions] as? NSNumber)?.intValue ?? 0
        let ownerUid = (attributes[.ownerAccountID] as? NSNumber)?.intValue ?? 0
        let currentProcessUid = Int(getuid())

        let fileData = try Data(contentsOf: url)
        let hash = SHA256.hash(data: fileData)
        let sha256String = hash.map { String(format: "%02x", $0) }.joined()

        return FileMetadata(
            path: path,
            sha256: sha256String,
            posixPermissions: posixPermissions,
            isSymlink: isSymlink,
            ownerUid: ownerUid,
            currentProcessUid: currentProcessUid
        )
    }
}

public enum CommandSecurityValidator {
    public static let prohibitedTokens: Set<String> = [";", "&&", "||", "|", "`", "$(", "sh", "bash", "zsh"]

    public static func validateArgv(_ argv: [String]) -> BrokerValidationResult {
        for arg in argv {
            for token in prohibitedTokens {
                if arg == token || (token.count > 1 && arg.contains(token)) {
                    return .invalid(code: "UNAUTHORIZED_SHELL_INTERPOLATION", message: "Prohibited shell metacharacter detected: \(arg)")
                }
            }
        }
        return .valid()
    }

    public static func validateExecutableCommand(_ command: [String]) -> BrokerValidationResult {
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
