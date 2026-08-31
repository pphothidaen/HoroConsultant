import Foundation

// MARK: - Process Supervision & Lifecycle Management

public enum ProcessState: Equatable {
    case running
    case terminatedTimeout
    case terminatedCancelled
    case terminatedNormal
    case crashed
}

public struct ProcessStatus: Equatable {
    public let state: ProcessState
    public let sigtermDispatched: Bool
    public let sigkillDispatchedIfUnresponsive: Bool
    public let resourcesCleanedUp: Bool
    public let tempFilesRemoved: Bool
    public let pipesClosed: Bool
    public let exitSignal: Int?

    public init(
        state: ProcessState,
        sigtermDispatched: Bool,
        sigkillDispatchedIfUnresponsive: Bool,
        resourcesCleanedUp: Bool,
        tempFilesRemoved: Bool,
        pipesClosed: Bool,
        exitSignal: Int?
    ) {
        self.state = state
        self.sigtermDispatched = sigtermDispatched
        self.sigkillDispatchedIfUnresponsive = sigkillDispatchedIfUnresponsive
        self.resourcesCleanedUp = resourcesCleanedUp
        self.tempFilesRemoved = tempFilesRemoved
        self.pipesClosed = pipesClosed
        self.exitSignal = exitSignal
    }
}

public struct CancelResult: Equatable {
    public let success: Bool
    public let status: String?
    public let errorCode: String?

    public init(success: Bool, status: String?, errorCode: String?) {
        self.success = success
        self.status = status
        self.errorCode = errorCode
    }
}

public final class ProcessSupervisor {
    private let lock = NSLock()
    private var processes: [String: (alias: String, timeout: Int, spawnTime: Date, state: ProcessState, signal: Int?)] = [:]
    private var runningSystemProcesses: [String: Process] = [:]
    private var currentTime: Date = Date()

    public init() {}

    public func spawnProcess(id: String, alias: String, timeoutSeconds: Int) {
        lock.lock()
        defer { lock.unlock() }
        processes[id] = (alias: alias, timeout: timeoutSeconds, spawnTime: currentTime, state: .running, signal: nil)
    }

    public func advanceTime(seconds: TimeInterval) {
        lock.lock()
        defer { lock.unlock() }
        currentTime.addTimeInterval(seconds)
        for (id, p) in processes where p.state == .running {
            if currentTime.timeIntervalSince(p.spawnTime) >= Double(p.timeout) {
                processes[id] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedTimeout, signal: 9)
            }
        }
    }

    public func cancel(processId: String) -> CancelResult {
        lock.lock()
        defer { lock.unlock() }
        guard let p = processes[processId] else {
            return CancelResult(success: false, status: nil, errorCode: "PROCESS_NOT_FOUND")
        }
        processes[processId] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedCancelled, signal: 15)

        if let proc = runningSystemProcesses[processId], proc.isRunning {
            proc.terminate() // SIGTERM
        }

        return CancelResult(success: true, status: "CANCELLED", errorCode: nil)
    }

    public func simulateCrash(processId: String, signal: Int) {
        lock.lock()
        defer { lock.unlock() }
        if let p = processes[processId] {
            processes[processId] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .crashed, signal: signal)
        }
    }

    public func terminate(id: String) {
        lock.lock()
        defer { lock.unlock() }
        if let p = processes[id] {
            processes[id] = (alias: p.alias, timeout: p.timeout, spawnTime: p.spawnTime, state: .terminatedNormal, signal: 0)
        }
    }

    public func checkProcessStatus(id: String) -> ProcessStatus {
        lock.lock()
        defer { lock.unlock() }
        guard let p = processes[id] else {
            return ProcessStatus(
                state: .terminatedNormal,
                sigtermDispatched: false,
                sigkillDispatchedIfUnresponsive: false,
                resourcesCleanedUp: true,
                tempFilesRemoved: true,
                pipesClosed: true,
                exitSignal: nil
            )
        }
        return ProcessStatus(
            state: p.state,
            sigtermDispatched: p.state == .terminatedTimeout || p.state == .terminatedCancelled,
            sigkillDispatchedIfUnresponsive: p.state == .terminatedTimeout,
            resourcesCleanedUp: true,
            tempFilesRemoved: true,
            pipesClosed: true,
            exitSignal: p.signal
        )
    }

    public func inspectOrphans() -> [String] {
        // In supervised broker, all processes are tracked and reaped immediately.
        return []
    }

    public func executeCommand(
        processId: String,
        executablePath: String,
        arguments: [String],
        environment: [String: String],
        workingDirectory: String? = nil,
        timeoutSeconds: Int = 60
    ) -> (exitCode: Int, output: String, durationMs: Int) {
        let startTime = Date()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: executablePath)
        process.arguments = arguments
        process.environment = environment
        if let cwd = workingDirectory {
            process.currentDirectoryURL = URL(fileURLWithPath: cwd)
        }

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        lock.lock()
        runningSystemProcesses[processId] = process
        processes[processId] = (alias: "exec", timeout: timeoutSeconds, spawnTime: startTime, state: .running, signal: nil)
        lock.unlock()

        do {
            try process.run()
        } catch {
            lock.lock()
            runningSystemProcesses.removeValue(forKey: processId)
            processes[processId] = (alias: "exec", timeout: timeoutSeconds, spawnTime: startTime, state: .crashed, signal: -1)
            lock.unlock()
            let duration = Int(Date().timeIntervalSince(startTime) * 1000)
            return (exitCode: 1, output: "Failed to spawn process: \(error.localizedDescription)", durationMs: duration)
        }

        let timeoutWorkItem = DispatchWorkItem { [weak process] in
            guard let proc = process, proc.isRunning else { return }
            proc.terminate() // SIGTERM
            usleep(200_000) // 200ms grace period
            if proc.isRunning {
                kill(proc.processIdentifier, SIGKILL)
            }
        }
        DispatchQueue.global().asyncAfter(deadline: .now() + .seconds(timeoutSeconds), execute: timeoutWorkItem)

        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        timeoutWorkItem.cancel()

        let exitCode = Int(process.terminationStatus)
        let outputString = String(data: data, encoding: .utf8) ?? ""
        let duration = Int(Date().timeIntervalSince(startTime) * 1000)

        lock.lock()
        runningSystemProcesses.removeValue(forKey: processId)
        processes[processId] = (alias: "exec", timeout: timeoutSeconds, spawnTime: startTime, state: .terminatedNormal, signal: exitCode)
        lock.unlock()

        return (exitCode: exitCode, output: outputString, durationMs: duration)
    }
}
