# Clean Windows acceptance

Status: current-PC installer lifecycle passed on 2 November 2026, at the user's
request. Clean-machine acceptance remains pending a separate Windows PC/VM.
This development PC has Node/Python/Rust and already had WebView2. It runs Windows
11 Home Single Language 10.0.26300; no Sandbox or VM launcher was available.
No virtualization features, other apps or protected workloads were changed.

## Current-PC evidence

The existing unsigned private installer was installed in
output/windows-install-qa/installed on D:. Installation and uninstallation both
returned zero using NSIS's supported silent mode. The interactive wizard and OS
security-prompt branches were not exercised. The installed executable, two
shortcut targets and the per-user
uninstall registration were checked. Uninstall removed the executable, shortcuts
and uninstall entry; reinstall restored them and launched through the installed
shortcut. App data was retained, and no cloud source was deleted.

The first launch used only Windows System32 in the child PATH, with a test
WebView profile and temporary files on D:. Pilot A sign-in, owned metadata and
opening the retained synthetic Markdown worked. Reinstall returned to sign-in,
as expected for memory-only sessions; pilot B's owned PDF library restored and
the generated hosted-pilot.pdf opened with its correct Page 1/Page 2 text.
No import, search, processing recovery or model request was made by this test.
This reuses earlier semantic-flow evidence, rather than claiming a new complete
import/search/delete pass. Offline, upgrade, missing-WebView2, clean-machine,
200% scaling and signing acceptance remain separate.

The installer is 2,629,494 bytes, SHA-256
82191ac6f9e3aabe8db589f8067eb7b0b63adbb6bdef5283302519285ca979d2.
The verified unbundled executable is
bd189d87d914e5e7614d227b78c36c1f85d322100e6c3d8e93e4b8ea0c63292d;
the installed executable is
6103b30ad64f874710c34de6c63ce8819dccf61eb7af626f8931b5afd2cb4ceb.

The initial raw-hash comparison stopped the harness. Investigation found exactly
three changed bytes: Tauri's bundle marker changes UNK to NSS for NSIS. All other
bytes match. This behavior is documented in the pinned tauri-utils 2.9.3
src/platform.rs. The read-only verifier accepts only that exact change against
the recorded source hash; it rejects arbitrary changes, ambiguous markers and
truncation. Seven synthetic verifier tests and the frontend build passed. These
tests are separate from the actual Windows install evidence.
The verifier is a developer check; the installed app does not require Python.

```powershell
.\scripts\python.ps1 -B -m scripts.verify_desktop_bundle --installed output/windows-install-qa/installed/gather-desktop.exe
```

Safe local receipt and installer copy: output/windows-install-qa/. Passwords,
tokens and personal file contents are excluded. The original installer and
verification receipt remain unchanged under output/private-desktop/.

References: [Tauri installer/WebView2 options](https://v2.tauri.app/distribute/windows-installer/)
and [Microsoft Sandbox edition requirements](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/#windows-edition-and-licensing-requirements).
The generated NSIS script uses current-user installation and downloadBootstrapper
only if WebView2 is missing; that prerequisite-download branch was not exercised.

## One combined acceptance pass

1. On a clean Windows11 x64 environment, record OS version, scaling and whether
   WebView2 is present. Do not install Node, Python, Docker, gcloud or model weights.
2. Copy the exact approved installer and its SHA-256 from the safe release receipt.
   Install using the normal Windows workflow. The unsigned pilot may show a warning;
   the user must handle any OS security decision. Do not automate a bypass.
3. Launch from its installed shortcut. Check one Library/search, clear private
   account scope, keyboard focus, scrolling and the minimum supported window.
4. Sign in with the existing test account. Verify owned files restore. For import/
   search acceptance, plan an available quota slot and model allowance first; never
   delete retained fixtures, increase quota or restart counters implicitly.
5. Select an owned nonsensitive supported file, review and confirm. It must appear
   in this same library and reach ready automatically. For PDF, verify page labels
   against the original, then one custom search and exact-version opening.
6. Close/reopen the app; sign in again. Saved metadata/text must restore. Check a
   disconnected-network failure and explicit recovery without automatic inference.
7. Delete only an explicitly disposable test source after action-time confirmation.
   Verify immediate hiding and confirmed cleanup or truthful pending state.
8. Uninstall through normal Windows settings under the user's control. Confirm
   shortcuts/application removal and successful reinstall. Uninstall must not
   silently delete the user's cloud library. Do not claim this from a build alone.

Record installer hash, machine prerequisites, observed outcomes and failures once
in the delivery evidence. Current artifacts: output/private-desktop/ and
output/windows-install-qa/; user documents,
passwords and tokens must not appear in receipts or screenshots.
