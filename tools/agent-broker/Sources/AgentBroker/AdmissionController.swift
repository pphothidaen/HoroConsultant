import Foundation

// MARK: - Admission Controller & Capacity Management

public enum QuotaBand: String, Codable {
    case safe
    case low
    case unknown
}

public final class AdmissionController {
    private let lock = NSLock()
    private let perAliasLimits: [String: Int]
    private let rootLimits: [String: Int]
    private let maxQueueDepth: Int

    private var activeRequestsByAlias: [String: Set<String>] = [:]
    private var queuedRequestsByAlias: [String: [String]] = [:]
    private var circuitStates: [String: Bool] = [:]
    private var quotaBands: [String: QuotaBand] = [:]
    public private(set) var lastRejectionCode: String?

    public init(
        perAliasLimits: [String: Int] = [
            "agy1": 3, "agy2": 3, "agy3": 3, "agy4": 3,
            "codex1": 2, "codex2": 2, "codex3": 2
        ],
        rootLimits: [String: Int] = [
            "root_a": 3,
            "root_b": 3
        ],
        maxQueueDepth: Int = 10
    ) {
        self.perAliasLimits = perAliasLimits
        self.rootLimits = rootLimits
        self.maxQueueDepth = maxQueueDepth
    }

    public func setCircuitState(alias: String, isOpen: Bool) {
        lock.lock()
        defer { lock.unlock() }
        circuitStates[alias] = isOpen
    }

    public func setQuotaBand(alias: String, band: QuotaBand) {
        lock.lock()
        defer { lock.unlock() }
        quotaBands[alias] = band
    }

    public func effectiveCapacity(for alias: String) -> Int {
        lock.lock()
        defer { lock.unlock() }
        if circuitStates[alias] == true { return 0 }
        if quotaBands[alias] == .unknown || quotaBands[alias] == .low { return 0 }
        return perAliasLimits[alias] ?? 0
    }

    public func admit(alias: String, requestId: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        if circuitStates[alias] == true {
            lastRejectionCode = "CIRCUIT_OPEN"
            return false
        }
        if quotaBands[alias] == .unknown {
            lastRejectionCode = "QUOTA_UNKNOWN"
            return false
        }

        let currentActive = activeRequestsByAlias[alias]?.count ?? 0
        let aliasCap = perAliasLimits[alias] ?? 0
        if currentActive >= aliasCap {
            lastRejectionCode = "CAPACITY_EXCEEDED"
            return false
        }

        let rootKey = alias.hasPrefix("codex") ? "root_a" : "root_b"
        let rootCap = rootLimits[rootKey] ?? Int.max
        let totalInRoot = activeRequestsByAlias
            .filter { k, _ in (rootKey == "root_a" && k.hasPrefix("codex")) || (rootKey == "root_b" && k.hasPrefix("agy")) }
            .reduce(0) { $0 + $1.value.count }

        if totalInRoot >= rootCap {
            lastRejectionCode = "AGGREGATE_POOL_EXCEEDED"
            return false
        }

        var set = activeRequestsByAlias[alias] ?? []
        set.insert(requestId)
        activeRequestsByAlias[alias] = set
        lastRejectionCode = nil
        return true
    }

    public func enqueue(alias: String, requestId: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        var queue = queuedRequestsByAlias[alias] ?? []
        if queue.count >= maxQueueDepth {
            lastRejectionCode = "QUEUE_SATURATED_BACKPRESSURE"
            return false
        }
        queue.append(requestId)
        queuedRequestsByAlias[alias] = queue
        lastRejectionCode = nil
        return true
    }

    public func release(alias: String, requestId: String) {
        lock.lock()
        defer { lock.unlock() }
        activeRequestsByAlias[alias]?.remove(requestId)
    }

    public func activeCount(for alias: String) -> Int {
        lock.lock()
        defer { lock.unlock() }
        return activeRequestsByAlias[alias]?.count ?? 0
    }
}
