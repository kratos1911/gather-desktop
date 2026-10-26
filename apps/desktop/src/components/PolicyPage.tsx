export type PolicyKind = "privacy" | "terms" | "copyright";
const pages: Record<
  PolicyKind,
  { title: string; sections: { title: string; body: string }[] }
> = {
  privacy: {
    title: "Privacy in this preview",
    sections: [
      {
        title: "What this build does",
        body: "This desktop preview displays fictional sample files. Search text and screen selections stay in application memory and are discarded when the app closes. Import, accounts, cloud storage and AI inference are not connected.",
      },
      {
        title: "External services",
        body: "The application code in this build does not send your content to an external processor. Fonts and interface code are local. There is no analytics SDK, session replay, marketing email, tracking cookie or model download in this preview. Development tooling and operating-system services are separate from application data handling.",
      },
      {
        title: "Before cloud features launch",
        body: "Supabase is planned, not currently connected. The release policy must name the operator and contact, actual processors, retention and deletion periods, international transfers, user rights and applicable regions before real accounts or uploads are enabled. This preview notice is not the final service privacy policy.",
      },
    ],
  },
  terms: {
    title: "Preview terms and limitations",
    sections: [
      {
        title: "Evaluation build",
        body: "Gather is a working name. This build is for reviewing the interface. Sample text filtering is not semantic search. It does not provide document storage or AI answers, and must not be relied on to preserve files.",
      },
      {
        title: "No purchase or subscription",
        body: "This preview has no checkout, payment collection or automatically renewing subscription. The planned service targets free operation with explicit capacity limits.",
      },
      {
        title: "Release terms pending",
        body: "The service operator, intended audience, support contact, jurisdiction and final acceptable-use terms have not been supplied. These notes describe current behavior and are not a substitute for completed release terms.",
      },
    ],
  },
  copyright: {
    title: "Copyright and content",
    sections: [
      {
        title: "Current content",
        body: "The library contains fictional examples and original decorative artwork. User uploads and public sharing are not enabled. Third-party component notices are recorded in the project.",
      },
      {
        title: "Reporting is not configured",
        body: "There is no monitored copyright contact or designated-agent registration configured yet. Do not submit personal information here. A working report route must be added before cloud uploads launch; this page does not claim DMCA safe-harbor protection.",
      },
      {
        title: "Procedure to implement before launch",
        body: "Notices should identify the work and allegedly infringing material, its location, the claimant’s contact information, the required good-faith and accuracy statements, and a signature. The operator must establish review, removal, counter-notice handling and a repeat-infringer policy, including account termination in appropriate circumstances. Operator and agent details must be verified before publishing the final policy.",
      },
    ],
  },
};
const pilotPages: typeof pages = {
  privacy: {
    title: "Privacy in this preview",
    sections: [
      {
        title: "Sample library and private operator pilot",
        body: "The sample library is fictional. The development Operator pilot connects two existing test accounts to Supabase. Passwords go to Supabase Authentication; access tokens stay in browser memory. There is no public signup. Real TXT/Markdown import requires the explicit TextFiles mode on the local server and frontend, plus review and confirmation for each file. Use only your own nonsensitive test content.",
      },
      {
        title: "What is sent and where",
        body: "Selecting a file reads it locally. Save selected file sends its filename and complete validated bytes through the local Gather API to the private Supabase database in Sydney. Processing and search are separate explicit actions that send text to Gather’s private CPU inference service on Google Cloud Run in Mumbai. Stored originals, passages and vectors are owner-scoped. Markdown is displayed as plain text. No model weights are downloaded by the desktop client.",
      },
      {
        title: "Storage, deletion and logging limits",
        body: "Disconnecting or refreshing clears local credentials and previews, not cloud data. Data remains until deletion and operator cleanup. Delete immediately hides a source; physical removal requires the existing operator cleanup step, with no guaranteed completion time. Application logging excludes file contents and tokens; provider logging and retention have not been independently verified for a public release. There is no application analytics or session replay. Do not use sensitive data in this pilot.",
      },
      {
        title: "Public release remains gated",
        body: "Operator identity/contact, audience and regions, final processor retention/logging review, a complete deletion policy and reporting procedures remain required before general accounts or uploads. This private test disclosure is not a final service privacy policy or a claim of legal compliance.",
      },
    ],
  },
  terms: {
    title: "Preview terms and limitations",
    sections: [
      {
        title: "Private evaluation only",
        body: "The packaged native application remains a sample preview. The development operator pilot is restricted to the two existing test accounts. Selected-file import supports UTF-8 TXT and Markdown, at most 64 KiB, and only documents that fit the unchanged three-request pilot processing budget. Saving queues work; it does not prove indexing or search readiness. Keep your original files.",
      },
      {
        title: "Explicit actions and costs",
        body: "Selection and local preview make no model calls. A worker or search must be invoked separately, and model calls count toward the operator’s pilot budget. There are no automatic processing retries, payments or subscriptions in the application.",
      },
      {
        title: "Release terms pending",
        body: "No public registration or general upload release is enabled. Operator/contact, intended audience, jurisdiction and final release terms remain to be supplied. These notes describe current test behavior.",
      },
    ],
  },
  copyright: {
    title: "Copyright and content",
    sections: [
      {
        title: "Private test content",
        body: "Sample library content is fictional. In the explicitly enabled file pilot, import only nonsensitive material you own or have permission to use. Content is private to its owner; no public sharing is enabled. Third-party component notices remain recorded in the project.",
      },
      {
        title: "Reporting is not configured",
        body: "No monitored copyright contact or designated-agent registration is configured. Do not submit personal information here. Reporting, review, counter-notice and repeat-infringer procedures remain public-release gates. This pilot makes no claim of DMCA safe-harbor protection.",
      },
    ],
  },
};
export function PolicyPage({ kind }: { kind: PolicyKind }) {
  const page = (import.meta.env.DEV ? pilotPages : pages)[kind];
  return (
    <section className="content policy-page">
      <h1>{page.title}</h1>
      <p className="subtitle">
        {import.meta.env.DEV
          ? "Current development build · Updated 26 October 2026"
          : "Current development build · Updated 26 September 2026"}
      </p>
      {page.sections.map((section) => (
        <section key={section.title}>
          <h2>{section.title}</h2>
          <p>{section.body}</p>
        </section>
      ))}
    </section>
  );
}
