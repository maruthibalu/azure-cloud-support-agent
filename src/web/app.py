from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from src.agent import SupportAgent

app = FastAPI(title="Azure Cloud Support Agent API", version="1.0.0")
agent = SupportAgent()


class TicketRequest(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: EmailStr
    subject: str
    message: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/tickets/process")
def process_ticket(payload: TicketRequest) -> dict:
    return agent.process_raw_ticket(
        ticket_id=payload.ticket_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        message=payload.message,
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Azure Cloud Ticket Agent</title>
  <style>
    :root {
      --bg-a: #f2f7ff;
      --bg-b: #dcecff;
      --card: #ffffff;
      --ink: #10233f;
      --muted: #4b627f;
      --accent: #0b63ce;
      --accent-2: #1b9aaa;
      --line: #c6d9f5;
      --ok: #0a8a4b;
      --warn: #c77700;
      --err: #b42318;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 20% 0%, rgba(11, 99, 206, 0.16), transparent 40%),
        radial-gradient(circle at 100% 20%, rgba(27, 154, 170, 0.18), transparent 38%),
        linear-gradient(140deg, var(--bg-a), var(--bg-b));
      min-height: 100vh;
    }

    .wrap {
      max-width: 1100px;
      margin: 24px auto;
      padding: 0 16px 24px;
    }

    .hero {
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px 20px;
      backdrop-filter: blur(3px);
      box-shadow: 0 12px 32px rgba(16, 35, 63, 0.08);
      animation: rise 0.45s ease-out;
    }

    .hero h1 {
      margin: 0 0 8px;
      font-size: 1.65rem;
      letter-spacing: 0.2px;
    }

    .hero p {
      margin: 0;
      color: var(--muted);
    }

    .grid {
      margin-top: 16px;
      display: grid;
      gap: 16px;
      grid-template-columns: 1.05fr 0.95fr;
    }

    .panel {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 10px 26px rgba(16, 35, 63, 0.08);
      animation: rise 0.55s ease-out;
    }

    h2 {
      margin: 0 0 12px;
      font-size: 1.15rem;
    }

    label {
      font-size: 0.92rem;
      color: var(--muted);
      display: block;
      margin-bottom: 6px;
    }

    input, textarea {
      width: 100%;
      border-radius: 10px;
      border: 1px solid #b8cbea;
      padding: 10px 12px;
      margin-bottom: 10px;
      font-size: 0.95rem;
      color: var(--ink);
      background: #fbfdff;
    }

    textarea { min-height: 140px; resize: vertical; }

    .row {
      display: grid;
      gap: 10px;
      grid-template-columns: 1fr 1fr;
    }

    button {
      border: 0;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: white;
      font-weight: 600;
      padding: 10px 14px;
      border-radius: 10px;
      cursor: pointer;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      box-shadow: 0 8px 20px rgba(11, 99, 206, 0.25);
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.6; cursor: not-allowed; }

    .status {
      margin-top: 10px;
      min-height: 22px;
      font-size: 0.92rem;
      color: var(--muted);
    }

    .pill {
      display: inline-block;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      margin-right: 6px;
      margin-bottom: 6px;
      background: #edf4ff;
      border: 1px solid #ccdcf8;
    }

    .action-resolve_with_kb { color: var(--ok); font-weight: 700; }
    .action-send_followup { color: var(--warn); font-weight: 700; }
    .action-escalate_to_specialist { color: var(--err); font-weight: 700; }

    .block {
      border: 1px solid #d7e5fa;
      border-radius: 12px;
      padding: 10px;
      margin-top: 10px;
      background: #f9fcff;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.84rem;
      color: #1a3557;
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <h1>Azure Cloud Support Agent</h1>
      <p>Submit a cloud ticket and get AI-driven analysis, runbook matches, and routing decisions.</p>
    </section>

    <section class=\"grid\">
      <article class=\"panel\">
        <h2>New Ticket</h2>
        <div class=\"row\">
          <div>
            <label for=\"ticket_id\">Ticket ID</label>
            <input id=\"ticket_id\" value=\"WEB-1001\" />
          </div>
          <div>
            <label for=\"email\">Customer Email</label>
            <input id=\"email\" type=\"email\" value=\"cloud.ops@contoso.com\" />
          </div>
        </div>
        <label for=\"name\">Customer Name</label>
        <input id=\"name\" value=\"Cloud Ops Team\" />

        <label for=\"subject\">Subject</label>
        <input id=\"subject\" value=\"AKS pods failing in production\" />

        <label for=\"message\">Message</label>
        <textarea id=\"message\">Critical: AKS checkout pods are in CrashLoopBackOff and users cannot place orders. Need urgent remediation guidance.</textarea>

        <button id=\"submit_btn\">Analyze Ticket</button>
        <div class=\"status\" id=\"status\"></div>
      </article>

      <article class=\"panel\">
        <h2>Agent Response</h2>
        <div id=\"result\">Submit a ticket to view analysis.</div>
      </article>
    </section>
  </div>

  <script>
    const btn = document.getElementById("submit_btn");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");

    function esc(value) {
      return String(value || "").replace(/[&<>\"']/g, function(c) {
        return ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[c];
      });
    }

    function pills(items) {
      if (!Array.isArray(items) || !items.length) return "<span class='pill'>none</span>";
      return items.map(function(item) { return "<span class='pill'>" + esc(item) + "</span>"; }).join("");
    }

    function render(data) {
      if (data.error) {
        resultEl.innerHTML = "<div class='block'><strong>Error:</strong> " + esc(data.error) + "</div>";
        return;
      }

      const analysis = data.analysis || {};
      const routing = data.routing || {};
      const kb = data.kb_search || {};
      const sols = kb.solutions || [];

      const solutionHtml = sols.length
        ? sols.map(function(s) {
            const source = s.source_url ? "<div><a href='" + esc(s.source_url) + "' target='_blank' rel='noreferrer'>Source</a></div>" : "";
            return "<div class='block'><strong>" + esc(s.title) + "</strong><div>Score: " + esc(s.relevance_score) + "</div>" + source + "</div>";
          }).join("")
        : "<div class='block'>No KB matches</div>";

      resultEl.innerHTML = ""
        + "<div class='block'><strong>Category:</strong> " + esc(analysis.category) + "<br/>"
        + "<strong>Severity:</strong> " + esc(analysis.severity) + "<br/>"
        + "<strong>Sentiment:</strong> " + esc(analysis.sentiment) + "</div>"
        + "<div class='block'><strong>Key Issues:</strong><br/>" + pills(analysis.key_issues) + "</div>"
        + "<div class='block'><strong>Routing Action:</strong> <span class='action-" + esc(routing.action) + "'>" + esc(routing.action) + "</span><br/>"
        + "<strong>Confidence:</strong> " + esc(routing.confidence) + "<br/>"
        + "<strong>Specialist:</strong> " + esc(routing.specialist_type || "-") + "<br/>"
        + "<strong>Reason:</strong> " + esc(routing.reason || "") + "</div>"
        + "<div class='block'><strong>Recommended Action:</strong><pre>" + esc(data.recommended_action || "") + "</pre></div>"
        + "<h3>Knowledge Base Matches</h3>"
        + solutionHtml;
    }

    async function submit() {
      btn.disabled = true;
      statusEl.textContent = "Analyzing ticket...";

      const payload = {
        ticket_id: document.getElementById("ticket_id").value,
        customer_name: document.getElementById("name").value,
        customer_email: document.getElementById("email").value,
        subject: document.getElementById("subject").value,
        message: document.getElementById("message").value
      };

      try {
        const res = await fetch("/api/tickets/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const txt = await res.text();
          throw new Error("HTTP " + res.status + ": " + txt);
        }

        const data = await res.json();
        render(data);
        statusEl.textContent = "Done";
      } catch (err) {
        statusEl.textContent = "Failed";
        resultEl.innerHTML = "<div class='block'><strong>Request failed:</strong> " + esc(err.message) + "</div>";
      } finally {
        btn.disabled = false;
      }
    }

    btn.addEventListener("click", submit);
  </script>
</body>
</html>
"""
