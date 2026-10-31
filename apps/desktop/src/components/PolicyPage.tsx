import { pilotAvailable } from "../services/pilotConfiguration";
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
        title: "Your private library",
        body: "The connected Library uses the two existing test accounts and shows their owned saved files. The separate sample-only build contains fictional examples. Passwords go to Supabase Authentication; access tokens stay in application memory. There is no public signup. Each TXT/Markdown import requires local review and confirmation. Use only your own nonsensitive test content.",
      },
      {
        title: "What is sent and where",
        body: "Selecting a file reads it locally. Save selected file sends its filename and validated bytes through the Gather API to Supabase in Sydney. Automatic processing sends text to Gather’s private CPU inference service on Google Cloud Run in Mumbai. Search and failed-processing retries are explicit actions and count toward pilot usage limits. Stored originals, passages and vectors are owner-scoped. Markdown is displayed as plain text. No model weights are downloaded by the desktop client.",
      },
      {
        title: "Storage, deletion and logging limits",
        body: "Signing out or refreshing clears local credentials and previews, not cloud data. Delete hides a source immediately. The app reports deletion complete only after server-confirmed removal of active stored text and derived data; pending cleanup can be retried. A minimal replay receipt remains to prevent resurrection by an old import. Application logging excludes file contents and tokens; provider retention and public-release policies remain under review. There is no application analytics or session replay.",
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
        body: "The connected Windows build uses the private hosted library and is restricted to two existing accounts. The default sample-only build remains separate. File import supports UTF-8 TXT and Markdown, at most 64 KiB and three processing passages. Saving queues work; it does not prove indexing or search readiness. Keep your original files. Clean-machine installation, release signing and broader release acceptance remain unverified.",
      },
      {
        title: "Explicit actions and costs",
        body: "Selection and local preview make no model calls. Saving starts processing when the operator enables automatic mode. Automatic processing and search share the server’s existing three-attempt model budget; calls count toward the cloud pilot budget. Failed-processing retries require an explicit action. There are no payments or subscriptions in the application.",
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
  const pilot = pilotAvailable;
  const page = (pilot ? pilotPages : pages)[kind];
  return (
    <section className="content policy-page">
      <h1>{page.title}</h1>
      <p className="subtitle">
        {pilot
          ? "Private evaluation build · Updated 31 October 2026"
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
