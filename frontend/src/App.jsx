import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { api } from "./api.js";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import NewCall from "./pages/NewCall.jsx";
import Scheduler from "./pages/Scheduler.jsx";
import Settings from "./pages/Settings.jsx";

function ProtectedShell() {
  const [apiKey, setApiKeyState] = useState(api.getApiKey());

  if (!apiKey) {
    return <Login onLoggedIn={() => setApiKeyState(api.getApiKey())} />;
  }

  return <Layout onLogout={() => setApiKeyState("")} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<ProtectedShell />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="new-call" element={<NewCall />} />
        <Route path="scheduler" element={<Scheduler />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
