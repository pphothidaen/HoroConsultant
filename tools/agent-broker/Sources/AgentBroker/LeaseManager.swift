import Foundation

// MARK: - Lease & Deduplication Management

public struct BrokerLease: Equatable {
    public let leaseId: String
    public let alias: String
    public var createdAt: Date
    public let ttlSeconds: Int
    public var isConsumed: Bool

    public init(
        leaseId: String,
        alias: String,
        createdAt: Date = Date(),
        ttlSeconds: Int,
        isConsumed: Bool = false
    ) {
        self.leaseId = leaseId
        self.alias = alias
        self.createdAt = createdAt
        self.ttlSeconds = ttlSeconds
        self.isConsumed = isConsumed
    }
}

public final class LeaseManager {
    private let lock = NSLock()
    private var leases: [String: BrokerLease] = [:]
    private let clockSkewToleranceSeconds: TimeInterval
    public private(set) var lastErrorCode: String?

    public init(clockSkewToleranceSeconds: TimeInterval = 0) {
        self.clockSkewToleranceSeconds = clockSkewToleranceSeconds
    }

    public func register(lease: BrokerLease) {
        lock.lock()
        defer { lock.unlock() }
        leases[lease.leaseId] = lease
    }

    public func validateLease(leaseId: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        guard let lease = leases[leaseId] else {
            lastErrorCode = "LEASE_NOT_FOUND"
            return false
        }
        let now = Date()
        let expiry = lease.createdAt.addingTimeInterval(TimeInterval(lease.ttlSeconds) + clockSkewToleranceSeconds)
        if now > expiry {
            lastErrorCode = "LEASE_EXPIRED"
            return false
        }
        lastErrorCode = nil
        return true
    }

    public func consumeLease(leaseId: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        guard var lease = leases[leaseId] else {
            lastErrorCode = "LEASE_NOT_FOUND"
            return false
        }
        if lease.isConsumed {
            lastErrorCode = "LEASE_ALREADY_CONSUMED"
            return false
        }
        lease.isConsumed = true
        leases[leaseId] = lease
        lastErrorCode = nil
        return true
    }
}

public final class RequestDeduplicator {
    private let lock = NSLock()
    private var seenRequests: [String: Date] = [:]
    private let windowSeconds: TimeInterval
    public private(set) var lastRejectionCode: String?

    public init(windowSeconds: TimeInterval = 300) {
        self.windowSeconds = windowSeconds
    }

    public func recordAndCheck(requestId: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        let now = Date()
        if let lastSeen = seenRequests[requestId] {
            if now.timeIntervalSince(lastSeen) <= windowSeconds {
                lastRejectionCode = "DUPLICATE_REQUEST_REJECTED"
                return false
            }
        }
        seenRequests[requestId] = now
        lastRejectionCode = nil
        return true
    }
}
