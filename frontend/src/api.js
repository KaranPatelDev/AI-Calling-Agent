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
  createCalls: (payload) => request("/api/calls", { method: "POST", body: JSON.stringify(payload) }),
  cancelCall: (id) => request(`/api/calls/${id}`, { method: "DELETE" }),
  parseUpload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/parse-upload", { method: "POST", body: form });
  },
  login: (email, password) => request("/api/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  getScriptSettings: () => request("/api/settings/scripts"),
  saveScriptSettings: (payload) => request("/api/settings/scripts", { method: "PUT", body: JSON.stringify(payload) }),
  getApiKey,
  setApiKey: (key) => localStorage.setItem("apiKey", key),
  logout: () => localStorage.removeItem("apiKey"),
};
