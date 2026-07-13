import { Link } from "react-router-dom";

const STEPS = [
  { title: "Upload contacts", body: "Drop in a PDF, Excel, or CSV of names and numbers — or type them in by hand." },
  { title: "Write your script", body: "Type or paste exactly what should be said on the call." },
  { title: "Call now or schedule", body: "Place calls instantly, or set an exact time — even 15 hours from now." },
  { title: "Track results", body: "Watch call status update live: ringing, completed, or failed." },
];

const FEATURES = [
  { title: "Bulk contact import", body: "Parse PDF, Excel, or CSV files straight into a call list — no manual retyping." },
  { title: "Script editor", body: "Write once, reuse across every recipient in a batch." },
  { title: "Precise scheduling", body: "Queue a call for any future moment; it fires automatically, no babysitting." },
  { title: "Live call dashboard", body: "See every call's status in real time, from queued to completed." },
  { title: "Plivo-powered voice", body: "Reliable telephony infrastructure places and reads out every call." },
  { title: "Secure by default", body: "API-key protected access to your calling data." },
];

export default function Landing() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <span className="brand">CallFlow</span>
        <Link className="nav-cta" to="/app">
          Launch App
        </Link>
      </header>

      <section className="hero">
        <div className="hero-bg" aria-hidden="true" />
        <div className="hero-content">
          <span className="eyebrow">Automated voice calling</span>
          <h1>Place the call. On your schedule.</h1>
          <p>
            Upload your contacts, write your script, and let CallFlow handle the calls — instantly, or exactly
            when you need them.
          </p>
          <Link className="cta" to="/app">
            Get started
          </Link>
        </div>
      </section>

      <section className="how-it-works">
        <h2>How it works</h2>
        <div className="steps">
          {STEPS.map((step, i) => (
            <div className="step" key={step.title}>
              <span className="step-number">{i + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="features">
        <h2>Everything you need to run outbound calls</h2>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="closing-cta">
        <h2>Ready to place your first call?</h2>
        <p>No setup fuss — upload a list, write a script, and go.</p>
        <Link className="cta" to="/app">
          Get started
        </Link>
      </section>
    </div>
  );
}
