# Privacy and release audit

DOCX private extension review, 2 November: [DOCX_IMPORT](DOCX_IMPORT.md) records
the tested parser/storage/UI safeguards, approved hosted flow and consent copy. Reuses the
same two-account original/text processors and deletion chain; no new recipient,
signup, telemetry or package. ZIP/XML limits, no entity/template/link fetching,
private staging, paragraph provenance and existing ownership/version/lease fences
are verified locally. Hosted enablement and the exact disposable fixture cleanup
were explicitly approved; the selected native/real-model flow passed. This does
not close public hostile-upload, confinement, final retention/policy or legal gates.

Current private extension: PRIVATE_DESKTOP_DELIVERY.md records approved hosted API
and restricted credential storage, native file processing and owner-confirmed
cleanup. Only the two existing accounts are allowed; no signup, session replay or
usage analytics is enabled. Operator-gated [stage profiling](PROCESSING_SPEED.md)
allows only fixed operation names, durations/counts and mode flags in the existing
server logs. Unknown/content-shaped metrics, text, filenames, user/source IDs,
credentials and provider bodies are excluded and tested. No additional processor
or recording SDK is introduced; this private diagnostic review does not close
public telemetry/retention gates. The explicitly approved [private PDF extension](PDF_IMPORT.md) sends
confirmed original bytes to Supabase/Sydney and extracted passages to Gather's
CPU model/Mumbai. It keeps the existing quota and input limits; general hostile
uploads remain gated. Final policies/provider retention, signing and broader
release gates below remain open. This is not a legal-compliance claim.

26 October implementation addendum: [PRIVATE_TEXT_FILES.md](PRIVATE_TEXT_FILES.md)
records the restricted two-account, nonsensitive-file operator pilot and its
review/confirmation, actual processors/regions, storage and manual-cleanup limits.
Those controls do not close public-upload/account release gates. Historical
"no external processor connected" findings below describe the September build;
the production native sample and development operator modes are now distinct.

27 September architecture update: cloud-hosted inference is planned under
ADR-009, but no external processor is connected. Before enabling uploads, review
the chosen provider's retention, logging, regions and subprocessors, publish
accurate processing disclosures and implement deletion across storage/jobs and
any retained inference artifacts. The original local-model budget assumptions
in the historical audit below are superseded; provider and budget are deferred.

Date: 26 September 2026. Scope: current desktop source, build configuration, dependencies and legacy root Python source. This is an engineering audit, not certification of legal compliance. The attachment's headline sums are not automatic fines per file/user. Applicability depends on operator, audience, jurisdiction and actual behavior.

## 1. COPPA / account creation

**Found:** No signup form, OAuth callback, magic-link handler, contact form or newsletter form in the current app. App.tsx only filters fixtures; import shows an explanatory message. Supabase is not connected. No age or birthdate is collected.

**Changed:** Added an accurate preview privacy notice and documented a release gate. Did not add a fake client-only age gate to an app with no account creation.

**You still need to:** Decide the intended audience/regions and operator details before implementing auth. If the agreed product restricts under-13 registration, enforce that decision in the server/auth creation path for all methods, not just a checkbox. Do not store rejected-attempt personal data. An age checkbox alone does not establish COPPA compliance. FTC guidance distinguishes child-directed services and actual knowledge in general-audience services.

## 2. Fonts and third-party resources

**Found:** New UI uses local system fonts and bundled code. No Google Fonts, remote CSS/JS or external image loading in application source. Legacy main1.py DocumentViewer.display_document constructed a Google Docs viewer URL containing a local file URL.

**Changed:** Removed the legacy Google viewer branch; non-PDF content uses plain-text display. Added only a local, original SVG and locally bundled UI dependencies. Existing native CSP restricts remote resource loads.

**You still need to:** Recheck downloaded fonts/components and their licenses when adding assets. Legacy embedding initialization can download weights from Hugging Face; it is not evidence that the new app contacts Hugging Face. Future model downloads need explicit setup disclosure.

## 3. Analytics and session replay

**Found:** No PostHog, Hotjar, FullStory, LogRocket, Clarity, Mixpanel, Sentry Replay, heatmaps or input recording in the app source/dependency manifest. No tracking-cookie or consent-storage code. UI state remains in memory.

**Changed:** Kept tracking absent and documented that fact in the in-app notice. No unnecessary cookie banner. Thinking Orbs, Motion and Lenis run locally; no analytics integration added.

**You still need to:** Re-audit before introducing telemetry. Any future optional replay must be disabled until explicit, revocable consent and mask/exclude sensitive inputs. A consent banner alone does not establish compliance with every recording law.

## 4. Marketing email / CAN-SPAM

**Found:** No email sender, templates, mailing lists or outbound email provider in current application code.

**Changed:** Recorded the feature as absent rather than inventing a postal address or nonfunctional unsubscribe link.

**You still need to:** Before adding marketing, provide a real postal address, suppression storage, functioning unsubscribe endpoint and applicable unsubscribe headers. Check suppression on every send and process opt-outs within the applicable deadline. Keep transactional templates separate; adding marketing may change their classification. The requested one-click/header behavior is an engineering requirement, not a claim that every header is itself mandated by CAN-SPAM.

## 5. Subscriptions / automatic renewal

**Found:** No Stripe/Paddle payment integration, checkout, subscription button or recurring plan. PaddleOCR is OCR software, not Paddle payments. The user's budget is zero recurring service fees.

**Changed:** In-app terms explain that the preview has no purchase or subscription.

**You still need to:** If monetization is introduced, show price, interval, renewal and cancellation terms at purchase, obtain affirmative consent, provide a simple cancellation path, confirmations and required trial/renewal reminders. Recheck current regional rules at that time. No payment feature was introduced by this audit.

## 6. Copyright / user uploads / DMCA

**Found:** New app contains fictional fixtures and original artwork. It has no upload endpoint or public content hosting. The legacy application imports local files, and the proposed Supabase service will host originals; therefore this is a real future release requirement, not permanently inapplicable.

**Changed:** Added a linked copyright information screen and a source-adjacent copyright link. It explicitly says the reporting contact is not configured. Added the notice, counter-notice and repeat-infringer workflow requirements; did not pretend a report was submitted or publish invented agent details.

**You still need to:** Before hosted uploads launch, decide the service operator and monitored copyright contact, publish the final procedure and implement report handling. If relying on US section 512 safe harbor, assess eligibility and satisfy all applicable conditions, including a reasonably implemented repeat-infringer policy. Registration alone is insufficient.

Registration handoff: use https://www.copyright.gov/dmca-directory/ and its official help to create the registration account; enter the service provider's legal name, physical street address and alternate names; enter the agent's name/organization, mailing address, phone and email; review and submit the designation with the current fee. The FAQ lists $6 and a three-year renewal requirement. Keep public website/app details consistent with the registration. The user must supply these facts and handle the account/payment; nothing was registered or paid here.

## Additional checks

- Privacy, preview terms and copyright screens are linked through App.tsx and contain accurate current-state text. They are not completed production legal policies. Operator identity, contact, audience, jurisdiction, retention/deletion and actual processors remain release inputs.
- No active remote processor receives document content in the new preview's application code. Supabase/model hosts are planned dependencies, not active ones. Build/package registries and OS services are outside this app-source statement. Legacy Ollama uses its configured local service and model libraries may download weights.
- The old Python scripts logged content, filenames, metadata, embeddings and exception strings. Dynamic print arguments were redacted to fixed messages. This reduces accidental console disclosure; it is not a full legacy security rewrite. Python syntax is checked without executing the scripts or touching document stores.
- `.env` and private data directories remain ignored. No secrets were printed or copied into the interface. Known-token-pattern scanning of source/built assets is a limited check, not proof against every secret format.
- Local error reports, native crash behavior, Supabase logging and account deletion must be assessed when those features are connected.

## Summary

| Item | Current result | Files / evidence | Owner follow-up |
| --- | --- | --- | --- |
| 1 Age/signup | No account collection | App.tsx; package.json; PolicyPage.tsx | Audience/regions and server-side policy before auth |
| 2 External loads | Removed legacy remote viewer; local assets | main1.py display_document; App.css; contours.svg; Tauri CSP | Review new asset licenses |
| 3 Replay | No replay or analytics | package.json; app source scan | Re-audit future telemetry |
| 4 Email | No sending feature | app source scan | Address/suppression flow before marketing |
| 5 Renewal | No payments | app source scan; preview terms | Re-audit if pricing added |
| 6 Copyright | Information page linked; report route pending | PolicyPage.tsx; App.tsx | Operator/contact, procedure, agent if applicable |
| Logs/secrets | Legacy dynamic prints redacted | main.py; main1.py; chroma.py | Broader release security review |

## Primary references checked

- https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions
- https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- https://www.oag.ca.gov/news/press-releases/attorney-general-bonta-issues-consumer-alert-california%E2%80%99s-automatic-renewal-law
- https://www.copyright.gov/512/
- https://www.copyright.gov/dmca-directory/faq.html
