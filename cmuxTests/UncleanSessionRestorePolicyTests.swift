import Foundation
import XCTest

#if canImport(cmux_DEV)
@testable import cmux_DEV
#elseif canImport(cmux)
@testable import cmux
#endif

final class UncleanSessionRestorePolicyTests: XCTestCase {
    func testSkipsAutomaticRestoreAfterUncleanLaunch() {
        XCTAssertFalse(
            SessionRestorePolicy.shouldAttemptRestore(
                previousLaunchWasUnclean: true,
                arguments: ["/Applications/cmux.app/Contents/MacOS/cmux"],
                environment: [:]
            )
        )
    }

    func testAllowsExplicitRecoveryOverrideAfterUncleanLaunch() {
        XCTAssertTrue(
            SessionRestorePolicy.shouldAttemptRestore(
                previousLaunchWasUnclean: true,
                arguments: ["/Applications/cmux.app/Contents/MacOS/cmux"],
                environment: ["CMUX_RESTORE_AFTER_UNCLEAN_LAUNCH": "1"]
            )
        )
    }
}
