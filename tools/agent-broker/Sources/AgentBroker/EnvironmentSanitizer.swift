import Foundation
import CryptoKit

// MARK: - Secret-Free Environment & Output Sanitization

public struct SanitizedOutput: Equatable {
    public let sanitizedString: String
    public let sha256Digest: String

    public init(sanitizedString: String, sha256Digest: String) {
        self.sanitizedString = sanitizedString
        self.sha256Digest = sha256Digest
    }
}

public enum EnvironmentSanitizer {
    public static let allowedKeys: Set<String> = ["PATH", "LANG", "LC_ALL", "HOME", "USER", "TMPDIR"]

    public static func sanitize(
        incomingEnvironment: [String: String],
        accountHome: String
    ) -> [String: String] {
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

public enum OutputSanitizer {
    private static let sensitivePatterns: [String] = [
        "sk-[a-zA-Z0-9-]+",
        "ghp_[a-zA-Z0-9]+",
        "ant-[a-zA-Z0-9-]+",
        "AKIA[0-9A-Z]{16}",
        "bearer-[a-zA-Z0-9-]+"
    ]

    public static func sanitizeOutput(raw: String) -> SanitizedOutput {
        var sanitized = raw
        for pattern in sensitivePatterns {
            if let regex = try? NSRegularExpression(pattern: pattern) {
                let range = NSRange(location: 0, length: sanitized.utf16.count)
                sanitized = regex.stringByReplacingMatches(
                    in: sanitized,
                    options: [],
                    range: range,
                    withTemplate: "[REDACTED_SECRET]"
                )
            }
        }

        let data = Data(sanitized.utf8)
        let hash = SHA256.hash(data: data)
        let digest = hash.map { String(format: "%02x", $0) }.joined()

        return SanitizedOutput(sanitizedString: sanitized, sha256Digest: digest)
    }
}
