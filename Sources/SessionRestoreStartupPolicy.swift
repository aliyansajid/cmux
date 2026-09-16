import Foundation

/// Automatic session restoration is intentionally conservative after an
/// unclean exit. A layout captured while the main thread was unhealthy can
/// immediately re-enter the same launch hang; the snapshot remains available
/// to the explicit Restore Previous App Launch action.
extension SessionRestorePolicy {
    static func shouldAttemptRestore(
        previousLaunchWasUnclean: Bool,
        arguments: [String] = CommandLine.arguments,
        environment: [String: String] = ProcessInfo.processInfo.environment
    ) -> Bool {
        guard shouldAttemptRestore(arguments: arguments, environment: environment) else {
            return false
        }
        guard previousLaunchWasUnclean else { return true }
        return environment["CMUX_RESTORE_AFTER_UNCLEAN_LAUNCH"] == "1"
    }
}
