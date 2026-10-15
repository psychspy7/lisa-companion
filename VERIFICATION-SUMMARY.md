# LISA 2.2.0 verification

Current evidence: 125 desktop tests and 14 backend tests passed. The installed Godot self-test passed 73 native checks, including supplied video stream, speech-driven deformation, corrected squat crop, walking, follow selection, routine priority, private bathroom/shower return paths, no rough mesh and removed whip mapping.

A disposable clean install with Desktop shortcut and the actual updater/helper/installer/restarted native engine passed. Activation identity/receipt hashes, saved memory and custom personality survived. Release discovery alone was mocked for this fixture; app/helper/installer/update/restart were real. The user's install/registry/data were not replaced.

A separate QA entitlement redeemed successfully on the live activation service. The 50 private sale codes were provisioned separately and not used for QA. Model/runtime byte hashes match the pinned official manifest. Real local inference produced a structured answer in5.41s on this PC. Immediate grounded replies and cloud-error fallback were tested through the real backend.

Runtime: Godot4.7.2 Standard official ed1daf0bf, OpenGL Compatibility on Intel UHD Graphics,172 draws and~332MB video memory in the final capture. Frame rates during simultaneous build/QA are not a hardware guarantee.

Limits: no actual microphone recording or account-funded provider calls. Source/private owner Firebase identity config is retained; no new owner login was required. Artwork remains illustrated2.5D with bounded deformation, not a production3D/Live2D rig. Two outfit looks are tint variants. Bathroom is private rather than explicit. Offline model is a basic small fallback and speech transcription still needs an online service. Installer unsigned; source-visible DRM is not unbreakable.

A real installed unactivated launch, including the removed legacy flag, stayed on activation with no room/receipt. Its visible activation screen acknowledged the upgrade without falsely claiming the engine loaded. Activated launch still waits for native room ready.

Code review: skipped (ce-code-review unavailable). The review host stopped on usage limits/interruption; partial correctness/security/testing/standards/maintainability passes identified five issues, all fixed and tested. Remaining coverage used root manual diff checks. The Grok peer did not run because jq was missing; no independent xAI review is claimed.
