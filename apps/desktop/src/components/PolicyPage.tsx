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
export function PolicyPage({ kind }: { kind: PolicyKind }) {
  const page = pages[kind];
  return (
    <section className="content policy-page">
      <h1>{page.title}</h1>
      <p className="subtitle">
        Current development build · Updated 26 September 2026
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
