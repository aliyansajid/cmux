# Issue #12788: unresolved post-update hang

Status: no confirmed reproduction, causal diagnosis, or verified fix.

The customer reports an immediately stuck workspace after updating to cmux
0.64.24 (build 104, `f5da007dd`) on macOS 26.6.2, Apple M3 Pro. The issue has
no reproduction steps, process sample, session fixture, or attachment.

## Correction to the initial PR

PR #12800 originally proposed skipping automatic session restore after any
unclean exit and enabling the existing startup file log for stable builds.
Those changes have been withdrawn. There is no evidence tying this report
to restored session state, and changing crash recovery is not justified by
an unspecified post-update hang. The associated policy tests established
neither the customer failure nor responsiveness after the proposed change.

The earlier description of a clean-environment reproduction was incorrect.
The local observations below are inconclusive and must not be used to close
the issue or describe a fix as verified.

## What was actually observed

- The downloaded release DMG matched the appcast size of 225143654 bytes.
  Its SHA-256 was
  `5bda5ca997a9369de45be6e34fe9c6e7b55b44cd42d0779ec6dd14c39b830924`.
  The bundle identified itself as 0.64.24, build 104, with arm64 and x86_64
  executable slices.
- The local host ran macOS 26.4.1, not the reported 26.6.2. The invoking
  shell reported `sysctl.proc_translated=1`.
- One direct launch remained alive before startup logging began. A five-second
  sample contained only `??? (in Rosetta Runtime Routines)`, reported a 244 KB
  footprint, and provided no cmux/AppKit/SwiftUI stack. It does not attribute
  a hang to the application.
- That launch later emitted breadcrumbs through `app.init.delegate.configured`.
  The explicitly native repeat returned exit status 143 (SIGTERM), also after
  reaching that marker. No stack at that boundary established a blocked thread.
- Another stable cmux with the same `com.cmuxterm.app` bundle ID was already
  running. `AppDelegate.observeDuplicateLaunches()` terminates same-ID launches,
  so the attempts were not isolated even with temporary HOME/CFFIXED_USER_HOME.
  The exact sender of SIGTERM was not recorded.
- The attempts passed `-ApplePersistenceIgnoreState YES`.
  `SessionRestorePolicy.shouldAttemptRestore()` rejects explicit arguments
  other than Finder's `-psn_` argument, so these attempts did not exercise
  automatic session replay. Snapshot preparation itself occurs during
  `AppDelegate.configure()`, before `applicationDidFinishLaunching`; the last
  breadcrumb alone cannot exclude that work as a potential stall location.
- The tagged Debug build failed during SwiftPM manifest linking with
  `No space left on device`. No changed app was built or exercised before
  the initial PR was opened. Green general CI checks are not evidence of
  a before/after hang test or customer recovery.

## Evidence needed to validate a fix

1. Use a leased fleet Mac and an isolated app identity. Match macOS 26.6.2
   where available and record OS/hardware differences explicitly. Keep
   native and translated launch results separate.
2. Exercise the affected release with a fresh account/profile, then a
   controlled persisted session and an update/relaunch. Do not add launch
   arguments that bypass the restoration path under investigation.
3. Distinguish process existence, socket acceptance, main-thread command
   completion, and actual terminal input/output. A live process or a socket
   path alone does not prove the workspace is interactive.
4. Capture a process sample while the failure is occurring, together with
   launch/update milestones and the session shape. Obtain equivalent
   evidence from the affected customer if the controlled workloads remain
   responsive. Related issues with generic SwiftUI stacks do not establish
   the cause of this report.
5. Once a blocking path is demonstrated, add a behavioral regression that
   fails on the affected implementation, apply the causal fix, and repeat
   the same workload with responsiveness and session-preservation assertions.
   Confirm recovery on the customer's setup when local reproduction remains
   unavailable. Report residual uncertainty rather than implying that an
   unrelated green test verifies the customer failure.

This internal investigation note changes no product UI, CLI help, localized
documentation site, or message catalog.
