const API = "/api";
async function j(res) {
  if (!res.ok) {
    let message = res.statusText || "Request failed";
    try { message = (await res.json()).detail || message; } catch { /* plain response */ }
    throw new Error(message);
  }
  return res.json();
}
const post = (path, body) =>
  fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(j);

export const api = {
  upload: (file) => { const fd = new FormData(); fd.append("file", file); return fetch(`${API}/upload`, { method: "POST", body: fd }).then(j); },
  evaluate: (p) => post("/evaluate", p),
  demo: () => post("/demo/evaluate", {}),
  status: (id) => fetch(`${API}/evaluate/status/${id}`).then(j),
  evaluation: (id) => fetch(`${API}/evaluation/${id}`).then(j),
  evaluations: () => fetch(`${API}/evaluations`).then(j),
  stats: () => fetch(`${API}/stats`).then(j),
  rubrics: () => fetch(`${API}/rubrics`).then(j),
  createRubric: (r) => post("/rubric", r),
  suggest: (p) => post("/rubric/suggest", p),
  sentiment: (text) => post("/sentiment", { text }),
  train: (task) => post("/train", { task }),
  trainStatus: (id) => fetch(`${API}/train/status/${id}`).then(j),
  health: () => fetch(`${API}/health`).then(j),
};

export async function downloadReport(id, format) {
  const res = await fetch(`${API}/report/${id}?format=${format}`);
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const ct = res.headers.get("content-type") || "";
  const ext = format === "pdf" ? (ct.includes("html") ? "html" : "pdf") : format;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `edugrade-report-${id}.${ext}`;
  a.click();
  URL.revokeObjectURL(a.href);
}