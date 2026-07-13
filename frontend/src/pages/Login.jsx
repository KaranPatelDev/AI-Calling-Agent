import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api.js";

export default function Login({ onLoggedIn }) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    const form = new FormData(e.target);
    const email = form.get("email");
    const password = form.get("password");
    setLoading(true);
    setError("");
    try {
      const { api_key } = await api.login(email, password);
      api.setApiKey(api_key);
      onLoggedIn();
    } catch (err) {
      setError("Invalid email or username / password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-bg" aria-hidden="true" />
      <Link to="/" className="back-link">
        ← Back to home
      </Link>
      <div className="login-card">
        <span className="brand">CallFlow</span>
        <h2>Welcome back</h2>
        <p className="login-sub">Log in to manage your calls</p>
        <form onSubmit={submit}>
          <label>
            Email or username
            <input name="email" type="text" placeholder="you@company.com" autoFocus required />
          </label>
          <label>
            Password
            <input name="password" type="password" placeholder="••••••••" required />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>
        {error && <p className="login-error">{error}</p>}
      </div>
    </div>
  );
}
