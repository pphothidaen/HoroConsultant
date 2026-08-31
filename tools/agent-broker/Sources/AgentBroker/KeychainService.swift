import Foundation
import Security
#if canImport(LocalAuthentication)
import LocalAuthentication
#endif

// MARK: - Keychain Security Protocol & Boundaries

public struct KeychainQueryResult: Equatable {
    public let success: Bool
    public let errorCode: String?
    public let rawSecret: String?

    public init(success: Bool, errorCode: String?, rawSecret: String?) {
        self.success = success
        self.errorCode = errorCode
        self.rawSecret = rawSecret
    }
}

public protocol KeychainProtocol {
    func queryCredential(alias: String) -> KeychainQueryResult
}

public final class SyntheticKeychainService: KeychainProtocol {
    public var mockErrorCode: Int32 = 0
    public var didPromptUserUI: Bool = false
    public let isIsolatedMock: Bool = true
    public let accessedRealKeychain: Bool = false
    private var mockSecrets: [String: String] = [:]

    public init(mockErrorCode: Int32 = 0, initialSecrets: [String: String] = [:]) {
        self.mockErrorCode = mockErrorCode
        self.mockSecrets = initialSecrets
    }

    public func setMockSecret(alias: String, secret: String) {
        mockSecrets[alias] = secret
    }

    public func queryCredential(alias: String) -> KeychainQueryResult {
        switch mockErrorCode {
        case 0:
            let secret = mockSecrets[alias] ?? "SYNTHETIC_MOCK_SECRET_123"
            return KeychainQueryResult(success: true, errorCode: nil, rawSecret: secret)
        case -25300: // errSecItemNotFound
            return KeychainQueryResult(success: false, errorCode: "AUTH_CREDENTIAL_NOT_FOUND", rawSecret: nil)
        case -25293: // errSecAuthFailed
            return KeychainQueryResult(success: false, errorCode: "AUTH_DENIED", rawSecret: nil)
        case -25308: // errSecInteractionNotAllowed
            return KeychainQueryResult(success: false, errorCode: "AUTH_INTERACTION_BLOCKED", rawSecret: nil)
        case -25299: // errSecDuplicateItem
            return KeychainQueryResult(success: false, errorCode: "AUTH_KEYCHAIN_COLLISION", rawSecret: nil)
        case -26275: // errSecDecode
            return KeychainQueryResult(success: false, errorCode: "AUTH_CORRUPTED_PAYLOAD", rawSecret: nil)
        default:
            return KeychainQueryResult(success: false, errorCode: "AUTH_UNKNOWN_ERROR", rawSecret: nil)
        }
    }
}

public final class SystemKeychainService: KeychainProtocol {
    private let serviceName: String

    public init(serviceName: String = "com.horoconsultant.agent-broker") {
        self.serviceName = serviceName
    }

    public func queryCredential(alias: String) -> KeychainQueryResult {
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: alias,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        #if canImport(LocalAuthentication)
        let context = LAContext()
        context.interactionNotAllowed = true
        query[kSecUseAuthenticationContext as String] = context
        #endif

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)

        switch status {
        case errSecSuccess:
            guard let data = item as? Data, let secret = String(data: data, encoding: .utf8) else {
                return KeychainQueryResult(success: false, errorCode: "AUTH_CORRUPTED_PAYLOAD", rawSecret: nil)
            }
            return KeychainQueryResult(success: true, errorCode: nil, rawSecret: secret)
        case errSecItemNotFound:
            return KeychainQueryResult(success: false, errorCode: "AUTH_CREDENTIAL_NOT_FOUND", rawSecret: nil)
        case errSecAuthFailed:
            return KeychainQueryResult(success: false, errorCode: "AUTH_DENIED", rawSecret: nil)
        case errSecInteractionNotAllowed:
            return KeychainQueryResult(success: false, errorCode: "AUTH_INTERACTION_BLOCKED", rawSecret: nil)
        case errSecDuplicateItem:
            return KeychainQueryResult(success: false, errorCode: "AUTH_KEYCHAIN_COLLISION", rawSecret: nil)
        case errSecDecode:
            return KeychainQueryResult(success: false, errorCode: "AUTH_CORRUPTED_PAYLOAD", rawSecret: nil)
        default:
            return KeychainQueryResult(success: false, errorCode: "AUTH_UNKNOWN_ERROR", rawSecret: nil)
        }
    }
}
