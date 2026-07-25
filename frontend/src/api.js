// ponytail: empty-string fallback means relative paths (e.g. "/api/calls"), which is what
// the Vercel rewrite proxy (vercel.json) relies on when VITE_API_URL isn't set in production.
const BASE_URL = import.meta.env.VITE_API_URL || "";

function getApiKey() {
  return localStorage.getItem("apiKey") || "";
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      "x-api-key": getApiKey(),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listCalls: () => request("/api/calls"),
  listInboundCalls: () => request("/api/inbound-calls"),
  createCalls: (payload) => request("/api/calls", { method: "POST", body: JSON.stringify(payload) }),
  cancelCall: (id) => request(`/api/calls/${id}`, { method: "DELETE" }),
  clearCallHistory: () => request("/api/calls", { method: "DELETE" }),
  deleteCallsBulk: async (outcome, audience) => {
    const params = new URLSearchParams({ outcome });
    if (audience) params.set("audience", audience);
    const res = await fetch(`${BASE_URL}/api/calls/bulk?${params}`, {
      method: "DELETE",
      headers: { "x-api-key": getApiKey() },
    });
    if (!res.ok) throw new Error((await res.text()) || `Request failed: ${res.status}`);
    return res.json();
  },
  exportCalls: async (filter) => {
    const res = await fetch(`${BASE_URL}/api/calls/export?filter=${filter}`, {
      headers: { "x-api-key": getApiKey() },
    });
    if (!res.ok) throw new Error((await res.text()) || `Request failed: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `calls_${filter}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
  exportInboundCalls: async (filter) => {
    const res = await fetch(`${BASE_URL}/api/inbound-calls/export?filter=${filter}`, {
      headers: { "x-api-key": getApiKey() },
    });
    if (!res.ok) throw new Error((await res.text()) || `Request failed: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `callbacks_${filter}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
  parseUpload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/parse-upload", { method: "POST", body: form });
  },
  login: (email, password) => request("/api/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  getScriptSettings: () => request("/api/settings/scripts"),
  saveScriptSettings: (payload) => request("/api/settings/scripts", { method: "PUT", body: JSON.stringify(payload) }),
  listScripts: () => request("/api/scripts"),
  createScript: (payload) => request("/api/scripts", { method: "POST", body: JSON.stringify(payload) }),
  updateScript: (id, payload) => request(`/api/scripts/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteScript: (id) => request(`/api/scripts/${id}`, { method: "DELETE" }),
  getApiKey,
  setApiKey: (key) => localStorage.setItem("apiKey", key),
  logout: () => localStorage.removeItem("apiKey"),
};
