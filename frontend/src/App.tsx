import { useEffect, useMemo, useState } from "react";

type PipelineStage =
  | "Identified"
  | "Contacted"
  | "Follow-up"
  | "Engaged"
  | "Qualified"
  | "Dropped";

type Contact = {
  id: string;
  name: string;
  title: string;
  email: string;
  phone: string;
};

type EmailStep = {
  id: string;
  version: string;
  subject: string;
  status: "Draft" | "Queued" | "Sent";
  summary: string;
};

type Company = {
  id: string;
  name: string;
  industry: string;
  stage: PipelineStage;
  contacts: Contact[];
  sequences: EmailStep[];
};

type BantField = "Confirmed" | "In progress" | "Missing";

type BantRecord = {
  companyId: string;
  budget: BantField;
  authority: BantField;
  need: BantField;
  timeline: BantField;
};

type DeadLetterTask = {
  id: string;
  task: string;
  reason: string;
  attemptedAt: string;
  retryCount?: number;
};

const PIPELINE_STAGES: PipelineStage[] = [
  "Identified",
  "Contacted",
  "Follow-up",
  "Engaged",
  "Qualified",
  "Dropped",
];

const companies: Company[] = [
  {
    id: "inscalia",
    name: "Inscalia Labs",
    industry: "AI Productivity",
    stage: "Engaged",
    contacts: [
      {
        id: "maya-cole",
        name: "Maya Cole",
        title: "VP of Growth",
        email: "maya.cole@inscalia.ai",
        phone: "+1 (415) 555-0100",
      },
      {
        id: "ravi-singh",
        name: "Ravi Singh",
        title: "RevOps Lead",
        email: "ravi.singh@inscalia.ai",
        phone: "+1 (415) 555-0111",
      },
    ],
    sequences: [
      {
        id: "seq-1",
        version: "v2",
        subject: "Aligning growth ops + AI assistants",
        status: "Sent",
        summary: "Intro with quantified lift and a 15-min fit check.",
      },
      {
        id: "seq-2",
        version: "v2",
        subject: "Follow-up: sales signals from inbound",
        status: "Sent",
        summary: "Share benchmark data and ask for preferred workflows.",
      },
      {
        id: "seq-3",
        version: "v1",
        subject: "Pilot outline + success metrics",
        status: "Queued",
        summary: "Outline 2-week pilot with success criteria.",
      },
      {
        id: "seq-4",
        version: "v1",
        subject: "Stakeholder alignment for RevOps",
        status: "Draft",
        summary: "Invite wider team and map integrations.",
      },
      {
        id: "seq-5",
        version: "v1",
        subject: "Closing loop on decision timeline",
        status: "Draft",
        summary: "Confirm timeline + next steps for procurement.",
      },
    ],
  },
  {
    id: "northwind",
    name: "Northwind Foods",
    industry: "CPG",
    stage: "Contacted",
    contacts: [
      {
        id: "elena-ramos",
        name: "Elena Ramos",
        title: "Head of Sales",
        email: "eramos@northwind.com",
        phone: "+1 (312) 555-0143",
      },
    ],
    sequences: [
      {
        id: "nw-1",
        version: "v1",
        subject: "Inscalia x Northwind growth signals",
        status: "Sent",
        summary: "Highlights pipeline gaps and data enrichment.",
      },
      {
        id: "nw-2",
        version: "v1",
        subject: "Sample account map and intent signals",
        status: "Queued",
        summary: "Share account map and intent scoring overview.",
      },
      {
        id: "nw-3",
        version: "v1",
        subject: "Deep-dive on distributor engagement",
        status: "Draft",
        summary: "Offer a workshop on distributor enablement.",
      },
      {
        id: "nw-4",
        version: "v1",
        subject: "Pilot timeline + stakeholders",
        status: "Draft",
        summary: "Confirm pilot timeline and stakeholder list.",
      },
      {
        id: "nw-5",
        version: "v1",
        subject: "Next steps on intent rollout",
        status: "Draft",
        summary: "Outline Q4 rollout and decision gates.",
      },
    ],
  },
  {
    id: "atlas",
    name: "Atlas Logistics",
    industry: "Logistics",
    stage: "Qualified",
    contacts: [
      {
        id: "jamie-lee",
        name: "Jamie Lee",
        title: "COO",
        email: "jamie.lee@atlas.io",
        phone: "+1 (646) 555-0188",
      },
    ],
    sequences: [
      {
        id: "al-1",
        version: "v3",
        subject: "ROI summary for Atlas Logistics",
        status: "Sent",
        summary: "Summarize ROI and procurement requirements.",
      },
      {
        id: "al-2",
        version: "v2",
        subject: "Implementation plan + timeline",
        status: "Sent",
        summary: "Share phased rollout and enablement plan.",
      },
      {
        id: "al-3",
        version: "v2",
        subject: "Security and compliance review",
        status: "Queued",
        summary: "Schedule compliance review and security Q&A.",
      },
      {
        id: "al-4",
        version: "v2",
        subject: "Finalize commercial terms",
        status: "Draft",
        summary: "Provide term sheet and approval path.",
      },
      {
        id: "al-5",
        version: "v2",
        subject: "Decision checkpoint",
        status: "Draft",
        summary: "Confirm decision date and sign-off flow.",
      },
    ],
  },
];

const initialBant: BantRecord[] = [
  {
    companyId: "inscalia",
    budget: "In progress",
    authority: "Confirmed",
    need: "Confirmed",
    timeline: "Missing",
  },
  {
    companyId: "northwind",
    budget: "Missing",
    authority: "In progress",
    need: "Confirmed",
    timeline: "Missing",
  },
  {
    companyId: "atlas",
    budget: "Confirmed",
    authority: "Confirmed",
    need: "Confirmed",
    timeline: "Confirmed",
  },
];

const DEADLETTER_FALLBACK: DeadLetterTask[] = [
  {
    id: "dl-204",
    task: "enrich_company",
    reason: "3rd party enrichment timeout",
    attemptedAt: "2024-05-20 09:42",
    retryCount: 3,
  },
  {
    id: "dl-219",
    task: "generate_sequence",
    reason: "LLM response exceeded token budget",
    attemptedAt: "2024-05-20 10:18",
    retryCount: 2,
  },
  {
    id: "dl-233",
    task: "news_digest",
    reason: "Rate limit from News API",
    attemptedAt: "2024-05-20 11:04",
    retryCount: 4,
  },
];

type DeadLetterApiItem = {
  id: number;
  reason: string;
  deadlettered_at: string;
  task: {
    task_id: string;
    task_type: string;
    retry_count: number;
  };
};

const fieldOptions: BantField[] = ["Confirmed", "In progress", "Missing"];

export default function App() {
  const [consoleInput, setConsoleInput] = useState("");
  const [consoleLog, setConsoleLog] = useState<string[]>([
    "Generate pipeline update for Northwind Foods",
  ]);
  const [selectedCompanyId, setSelectedCompanyId] = useState(companies[0].id);
  const [selectedContactId, setSelectedContactId] = useState(
    companies[0].contacts[0].id,
  );
  const [bantRecords, setBantRecords] = useState<BantRecord[]>(initialBant);
  const [bantFilter, setBantFilter] = useState<
    "All" | "Needs attention" | "Complete"
  >("All");
  const [deadLetterTasks, setDeadLetterTasks] = useState<DeadLetterTask[]>(
    DEADLETTER_FALLBACK,
  );

  const selectedCompany = useMemo(
    () => companies.find((company) => company.id === selectedCompanyId),
    [selectedCompanyId],
  );

  useEffect(() => {
    if (!("fetch" in globalThis)) {
      return;
    }
    let isMounted = true;
    const loadDeadletter = async () => {
      try {
        const response = await fetch("/deadletter");
        if (!response.ok) {
          throw new Error("Failed to load deadletter queue.");
        }
        const payload = (await response.json()) as DeadLetterApiItem[];
        if (!isMounted) {
          return;
        }
        const mapped = payload.map((item) => ({
          id: item.task.task_id ?? String(item.id),
          task: item.task.task_type,
          reason: item.reason,
          attemptedAt: new Date(item.deadlettered_at).toLocaleString(),
          retryCount: item.task.retry_count,
        }));
        setDeadLetterTasks(mapped.length > 0 ? mapped : DEADLETTER_FALLBACK);
      } catch {
        if (isMounted) {
          setDeadLetterTasks(DEADLETTER_FALLBACK);
        }
      }
    };
    void loadDeadletter();
    return () => {
      isMounted = false;
    };
  }, []);

  const selectedContact = useMemo(() => {
    if (!selectedCompany) {
      return undefined;
    }
    return selectedCompany.contacts.find(
      (contact) => contact.id === selectedContactId,
    );
  }, [selectedCompany, selectedContactId]);

  const filteredBant = useMemo(() => {
    return bantRecords.filter((record) => {
      const fields = [
        record.budget,
        record.authority,
        record.need,
        record.timeline,
      ];
      const hasMissing = fields.includes("Missing");
      const hasInProgress = fields.includes("In progress");
      const isComplete = !hasMissing && !hasInProgress;
      if (bantFilter === "Needs attention") {
        return hasMissing || hasInProgress;
      }
      if (bantFilter === "Complete") {
        return isComplete;
      }
      return true;
    });
  }, [bantRecords, bantFilter]);

  const handleConsoleSubmit = () => {
    if (!consoleInput.trim()) {
      return;
    }
    setConsoleLog((prev) => [consoleInput.trim(), ...prev].slice(0, 5));
    setConsoleInput("");
  };

  const handleCompanyChange = (companyId: string) => {
    setSelectedCompanyId(companyId);
    const company = companies.find((item) => item.id === companyId);
    if (company?.contacts[0]) {
      setSelectedContactId(company.contacts[0].id);
    }
  };

  const updateBantRecord = (
    companyId: string,
    field: keyof BantRecord,
    value: BantField,
  ) => {
    setBantRecords((records) =>
      records.map((record) =>
        record.companyId === companyId
          ? {
              ...record,
              [field]: value,
            }
          : record,
      ),
    );
  };

  return (
    <main
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        padding: "2rem",
        background: "#f6f7fb",
        color: "#1f2937",
      }}
    >
      <header style={{ marginBottom: "2rem" }}>
        <h1 style={{ marginBottom: "0.5rem" }}>SalesOps Frontend Console</h1>
        <p style={{ margin: 0, color: "#6b7280" }}>
          Orchestrate pipeline updates, outreach sequences, and qualification
          signals in one view.
        </p>
      </header>

      <section
        aria-label="text console"
        style={{
          background: "white",
          padding: "1.5rem",
          borderRadius: "16px",
          boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Text Console</h2>
        <p style={{ marginTop: 0, color: "#6b7280" }}>
          Enter natural language requests and track the most recent intents.
        </p>
        <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
          <textarea
            aria-label="Natural language input"
            value={consoleInput}
            onChange={(event) => setConsoleInput(event.target.value)}
            placeholder="e.g. Generate 5-step outreach sequence for Atlas Logistics"
            style={{
              flex: 1,
              minHeight: "96px",
              borderRadius: "12px",
              border: "1px solid #d1d5db",
              padding: "0.75rem",
              fontSize: "0.95rem",
            }}
          />
          <button
            type="button"
            onClick={handleConsoleSubmit}
            style={{
              background: "#4f46e5",
              color: "white",
              border: 0,
              borderRadius: "10px",
              padding: "0.75rem 1.25rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </div>
        <div style={{ marginTop: "1rem" }}>
          <h3 style={{ marginBottom: "0.5rem" }}>Recent intents</h3>
          <ul style={{ margin: 0, paddingLeft: "1.5rem", color: "#374151" }}>
            {consoleLog.map((entry, index) => (
              <li key={`${entry}-${index}`}>{entry}</li>
            ))}
          </ul>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div
          data-testid="company-list"
          style={{
            background: "white",
            padding: "1.5rem",
            borderRadius: "16px",
            boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Companies</h2>
          <p style={{ marginTop: 0, color: "#6b7280" }}>
            Select a company to view contacts, sequences, and BANT health.
          </p>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {companies.map((company) => (
              <button
                key={company.id}
                type="button"
                onClick={() => handleCompanyChange(company.id)}
                style={{
                  textAlign: "left",
                  borderRadius: "12px",
                  border:
                    selectedCompanyId === company.id
                      ? "2px solid #4f46e5"
                      : "1px solid #e5e7eb",
                  padding: "0.75rem",
                  background:
                    selectedCompanyId === company.id ? "#eef2ff" : "white",
                  cursor: "pointer",
                }}
              >
                <strong>{company.name}</strong>
                <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                  {company.industry} · {company.stage}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div
          data-testid="contact-panel"
          style={{
            background: "white",
            padding: "1.5rem",
            borderRadius: "16px",
            boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Contact Panel</h2>
          {selectedCompany ? (
            <>
              <p style={{ marginTop: 0, color: "#6b7280" }}>
                Primary contacts for {selectedCompany.name}.
              </p>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {selectedCompany.contacts.map((contact) => (
                  <button
                    key={contact.id}
                    type="button"
                    onClick={() => setSelectedContactId(contact.id)}
                    style={{
                      borderRadius: "999px",
                      border:
                        selectedContactId === contact.id
                          ? "2px solid #111827"
                          : "1px solid #d1d5db",
                      background:
                        selectedContactId === contact.id ? "#111827" : "white",
                      color:
                        selectedContactId === contact.id ? "white" : "#111827",
                      padding: "0.4rem 0.85rem",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    {contact.name}
                  </button>
                ))}
              </div>
              {selectedContact ? (
                <div
                  style={{
                    marginTop: "1rem",
                    padding: "1rem",
                    borderRadius: "12px",
                    background: "#f9fafb",
                    border: "1px solid #e5e7eb",
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>{selectedContact.name}</h3>
                  <p style={{ margin: 0, color: "#6b7280" }}>
                    {selectedContact.title}
                  </p>
                  <dl
                    style={{
                      display: "grid",
                      gridTemplateColumns: "auto 1fr",
                      gap: "0.5rem 1rem",
                      marginTop: "1rem",
                      fontSize: "0.9rem",
                    }}
                  >
                    <dt>Email</dt>
                    <dd style={{ margin: 0 }}>{selectedContact.email}</dd>
                    <dt>Phone</dt>
                    <dd style={{ margin: 0 }}>{selectedContact.phone}</dd>
                    <dt>Pipeline stage</dt>
                    <dd style={{ margin: 0 }}>{selectedCompany.stage}</dd>
                  </dl>
                </div>
              ) : null}
            </>
          ) : (
            <p>No company selected.</p>
          )}
        </div>

        <div
          data-testid="sequence-panel"
          style={{
            background: "white",
            padding: "1.5rem",
            borderRadius: "16px",
            boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Email Sequence (5-step)</h2>
          {selectedCompany ? (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {selectedCompany.sequences.map((step, index) => (
                <div
                  key={step.id}
                  style={{
                    padding: "0.75rem",
                    borderRadius: "12px",
                    border: "1px solid #e5e7eb",
                    background: "#f9fafb",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <strong>
                      Step {index + 1}: {step.subject}
                    </strong>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        padding: "0.25rem 0.5rem",
                        borderRadius: "999px",
                        background: "#e0e7ff",
                        color: "#4338ca",
                      }}
                    >
                      {step.version}
                    </span>
                  </div>
                  <p style={{ margin: "0.35rem 0 0", color: "#6b7280" }}>
                    {step.summary}
                  </p>
                  <p style={{ margin: "0.35rem 0 0", fontSize: "0.85rem" }}>
                    Status: <strong>{step.status}</strong>
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p>Select a company to view sequences.</p>
          )}
        </div>
      </section>

      <section
        style={{
          background: "white",
          padding: "1.5rem",
          borderRadius: "16px",
          boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Pipeline Kanban</h2>
        <p style={{ marginTop: 0, color: "#6b7280" }}>
          Required stages: Identified → Contacted → Follow-up → Engaged →
          Qualified → Dropped.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "1rem",
          }}
        >
          {PIPELINE_STAGES.map((stage) => (
            <div
              key={stage}
              style={{
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
                background: "#f9fafb",
                padding: "0.75rem",
                minHeight: "160px",
              }}
            >
              <h3 style={{ marginTop: 0 }}>{stage}</h3>
              <div style={{ display: "grid", gap: "0.5rem" }}>
                {companies
                  .filter((company) => company.stage === stage)
                  .map((company) => (
                    <div
                      key={company.id}
                      style={{
                        background: "white",
                        padding: "0.5rem",
                        borderRadius: "10px",
                        border: "1px solid #e5e7eb",
                        fontSize: "0.9rem",
                      }}
                    >
                      <strong>{company.name}</strong>
                      <div style={{ color: "#6b7280" }}>
                        {company.industry}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div
          data-testid="bant-panel"
          style={{
            background: "white",
            padding: "1.5rem",
            borderRadius: "16px",
            boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>BANT Qualification</h2>
          <p style={{ marginTop: 0, color: "#6b7280" }}>
            Edit qualification signals and filter by readiness.
          </p>
          <label
            htmlFor="bant-filter"
            style={{ display: "block", marginBottom: "0.5rem" }}
          >
            Filter
          </label>
          <select
            id="bant-filter"
            aria-label="BANT filter"
            value={bantFilter}
            onChange={(event) =>
              setBantFilter(event.target.value as typeof bantFilter)
            }
            style={{
              width: "100%",
              padding: "0.5rem",
              borderRadius: "10px",
              border: "1px solid #d1d5db",
              marginBottom: "1rem",
            }}
          >
            <option value="All">All</option>
            <option value="Needs attention">Needs attention</option>
            <option value="Complete">Complete</option>
          </select>
          <div style={{ display: "grid", gap: "1rem" }}>
            {filteredBant.map((record) => {
              const company = companies.find(
                (entry) => entry.id === record.companyId,
              );
              return (
                <div
                  key={record.companyId}
                  style={{
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                    padding: "0.75rem",
                    background: "#f9fafb",
                  }}
                >
                  <strong>{company?.name ?? record.companyId}</strong>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(2, minmax(120px, 1fr))",
                      gap: "0.5rem",
                      marginTop: "0.5rem",
                    }}
                  >
                    {(
                      [
                        ["budget", record.budget],
                        ["authority", record.authority],
                        ["need", record.need],
                        ["timeline", record.timeline],
                      ] as const
                    ).map(([fieldKey, value]) => (
                      <label
                        key={fieldKey}
                        style={{
                          display: "grid",
                          gap: "0.25rem",
                          fontSize: "0.85rem",
                        }}
                      >
                        {fieldKey.toUpperCase()}
                        <select
                          aria-label={`${company?.name ?? "Company"} ${
                            fieldKey
                          }`}
                          value={value}
                          onChange={(event) =>
                            updateBantRecord(
                              record.companyId,
                              fieldKey,
                              event.target.value as BantField,
                            )
                          }
                          style={{
                            padding: "0.35rem",
                            borderRadius: "8px",
                            border: "1px solid #d1d5db",
                            background: "white",
                          }}
                        >
                          {fieldOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div
          style={{
            background: "white",
            padding: "1.5rem",
            borderRadius: "16px",
            boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>DeadLetter Queue</h2>
          <p style={{ marginTop: 0, color: "#6b7280" }}>
            Failed orchestration tasks that require manual review.
          </p>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {deadLetterTasks.length === 0 ? (
              <p style={{ margin: 0, color: "#6b7280" }}>
                No deadletter tasks in the queue.
              </p>
            ) : (
              deadLetterTasks.map((task) => (
                <div
                  key={task.id}
                  style={{
                    border: "1px solid #fecaca",
                    background: "#fef2f2",
                    borderRadius: "12px",
                    padding: "0.75rem",
                  }}
                >
                  <strong>{task.task}</strong>
                  <p style={{ margin: "0.35rem 0", color: "#b91c1c" }}>
                    {task.reason}
                  </p>
                  <p style={{ margin: 0, fontSize: "0.85rem" }}>
                    Attempted: {task.attemptedAt}
                    {typeof task.retryCount === "number"
                      ? ` · Retries: ${task.retryCount}`
                      : ""}
                    {" · "}ID: {task.id}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
