# Clean Windows acceptance

Status: pending an accessible clean Windows PC/VM. This development machine has
Node/Python/Rust and cannot establish clean-machine acceptance. No Windows Sandbox
or supported VM launcher was found. No virtualization feature/software was enabled.
The installer/native app build and current-machine flow are separate evidence.

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
in the delivery evidence. Current artifacts: output/private-desktop/; user documents,
passwords and tokens must not appear in receipts or screenshots.
