// Cliente da API FastAPI. A base vem de VITE_API_URL (produção, ex.:
// https://api.seudominio.com) ou fica vazia (mesma origem / proxy do dev).
const BASE = import.meta.env.VITE_API_URL ?? "";

export type TrajectoryPoint = {
  range_m: number;
  drop_cm: number;
  drop_moa: number;
  drop_mil: number;
  velocity_fps: number;
  energy_ftlbs: number;
  time_of_flight_s: number;
  wind_drift_cm: number;
  spin_drift_cm: number;
};

export type DopeEntry = {
  range_m: number;
  unit: string;
  elevation: number;
  elevation_clicks: number;
  windage: number;
  windage_dir: string;
  windage_clicks: number;
  spin_drift_cm: number;
  velocity_fps: number;
  energy_ftlbs: number;
  time_of_flight_s: number;
};

export type TrajectoryResponse = {
  zero_range_m: number;
  max_point_blank_range_m: number;
  summary: Record<string, number>;
  points: TrajectoryPoint[];
  dope_card: DopeEntry[] | null;
};

export type LoadData = {
  min?: number;
  max?: number;
  unit?: string;
  velocity?: number;
  note?: string;
};
export type Caliber = {
  projectiles: Record<string, { powders: Record<string, LoadData> }>;
  max_oal?: string;
  max_case?: string;
  proj_dia?: string;
  base_dia?: string;
  [k: string]: unknown;
};
export type Catalog = { calibers: Record<string, Caliber> };

export type ReloadWarning = { severity: "erro" | "aviso"; message: string };
export type ReloadWarningsResponse = {
  caliber?: string | null;
  powder?: string | null;
  warnings: ReloadWarning[];
};
export type ChargeEstimate = {
  energy_j: number;
  energy_ftlbs: number;
  estimated_charge_grains: number;
};

export type User = {
  id: number;
  username: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  cpf?: string | null;
  is_premium: boolean;
};

export type InventoryItem = {
  id: number;
  category: string;
  name: string;
  quantity: number;
  unit: string;
  price_unit: number;
  batch_number?: string | null;
  expiration_date?: string | null;
};

export type Firearm = {
  id: number;
  model: string;
  serial?: string | null;
  sigma?: string | null;
  craf?: string | null;
  expiration?: string | null;
  image_url?: string | null;
};

export type Advice = { content: string; provider: string; confidence: string };

export type DopeCard = {
  id: number;
  name: string;
  firearm_id?: number | null;
  weight_grains?: number | null;
  bc_g1?: number | null;
  muzzle_velocity_fps?: number | null;
  diameter_mm?: number | null;
  bullet_length_in?: number | null;
  zero_range_m?: number | null;
  max_range_m?: number | null;
  step_m?: number | null;
  sight_height_cm?: number | null;
  twist_rate_in?: number | null;
  twist_dir?: string | null;
  unit?: string | null;
  click_value?: number | null;
};

export type TargetGroup = {
  id: number;
  shots: [number, number][];
  group_size_mm: number;
  poi_mm: [number, number];
};
export type TargetAnalysis = {
  shot_count: number;
  pixel_per_mm: number;
  groups: TargetGroup[];
  annotated_image: string; // data URL (PNG)
};
export type TargetParams = {
  targetWidthMm: number;
  sensitivity: number;
  centerX?: number | null;
  centerY?: number | null;
};

export type LogEntry = {
  id: number;
  caliber: string;
  date: string;
  quantity: number;
  projectile?: string | null;
  powder?: string | null;
  charge?: number | null;
  primer?: string | null;
  case?: string | null;
  velocity_avg?: number | null;
  velocity_sd?: number | null;
  grouping_mm?: number | null;
  firearm_id?: number | null;
  notes?: string | null;
};

// Resposta do POST /api/logbook: além do registro, o que saiu do estoque e o
// custo por munição — preenchidos só quando se pede a dedução (deduct=true).
export type LogCreateResult = LogEntry & {
  deductions: string[];
  unit_cost: number | null;
};

function tokenHeader(): Record<string, string> {
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...tokenHeader(),
      ...(opts.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* corpo não-JSON */
    }
    throw new Error(detail);
  }
  // 204 No Content (ex.: DELETE) não tem corpo para desserializar.
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Baixa um arquivo protegido por token (o header Authorization não cabe num
// <a href>, então buscamos como blob e disparamos o download). O nome vem do
// Content-Disposition quando presente.
async function downloadFile(path: string, fallbackName: string): Promise<void> {
  const res = await fetch(BASE + path, { headers: { ...tokenHeader() } });
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const b = await res.json();
      if (b?.detail) detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail);
    } catch {
      /* corpo não-JSON */
    }
    throw new Error(detail);
  }
  const cd = res.headers.get("Content-Disposition") ?? "";
  const m = cd.match(/filename="?([^";]+)"?/);
  const name = m ? m[1] : fallbackName;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  catalog: () => request<Catalog>("/api/catalog"),
  trajectory: (body: unknown) =>
    request<TrajectoryResponse>("/api/trajectory", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Dados de recarga (catálogo + segurança)
  reloadWarnings: (q: { caliber?: string; powder?: string; primer?: string; oal_mm?: number }) => {
    const p = new URLSearchParams();
    if (q.caliber) p.set("caliber", q.caliber);
    if (q.powder) p.set("powder", q.powder);
    if (q.primer) p.set("primer", q.primer);
    if (q.oal_mm != null) p.set("oal_mm", String(q.oal_mm));
    return request<ReloadWarningsResponse>(`/api/reloading/warnings?${p.toString()}`);
  },
  estimateCharge: (body: {
    projectile_grains: number; velocity_fps: number;
    calorific_j_per_g: number; efficiency_percent: number;
  }) => request<ChargeEstimate>("/api/reloading/estimate", {
    method: "POST",
    body: JSON.stringify(body),
  }),

  login: async (username: string, password: string) => {
    const r = await request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("token", r.access_token);
    return r;
  },
  register: (body: unknown) =>
    request<{ detail: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => request<User>("/api/auth/me"),

  // WebAuthn / passkeys (login por biometria)
  webauthnAvailable: () =>
    request<{ available: boolean }>("/api/auth/webauthn/available"),
  webauthnRegisterBegin: () =>
    request<unknown>("/api/auth/webauthn/register/begin", { method: "POST" }),
  webauthnRegisterComplete: (credential: unknown, label?: string) =>
    request<{ detail: string }>("/api/auth/webauthn/register/complete", {
      method: "POST",
      body: JSON.stringify({ credential, label: label ?? null }),
    }),
  webauthnLoginBegin: (username: string) =>
    request<unknown>("/api/auth/webauthn/login/begin", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  webauthnLoginComplete: async (username: string, credential: unknown) => {
    const r = await request<{ access_token: string }>("/api/auth/webauthn/login/complete", {
      method: "POST",
      body: JSON.stringify({ username, credential }),
    });
    localStorage.setItem("token", r.access_token);
    return r;
  },
  updateProfile: (body: Partial<Pick<User, "name" | "email" | "phone" | "cpf">>) =>
    request<User>("/api/auth/me", { method: "PUT", body: JSON.stringify(body) }),
  logout: () => localStorage.removeItem("token"),
  hasToken: () => !!localStorage.getItem("token"),

  // Inventário
  listInventory: () => request<InventoryItem[]>("/api/inventory"),
  createInventory: (body: Omit<InventoryItem, "id">) =>
    request<InventoryItem>("/api/inventory", { method: "POST", body: JSON.stringify(body) }),
  updateInventory: (id: number, body: Omit<InventoryItem, "id">) =>
    request<InventoryItem>(`/api/inventory/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteInventory: (id: number) =>
    request<void>(`/api/inventory/${id}`, { method: "DELETE" }),

  // Armas
  listFirearms: () => request<Firearm[]>("/api/firearms"),
  createFirearm: (body: Omit<Firearm, "id" | "image_url">) =>
    request<Firearm>("/api/firearms", { method: "POST", body: JSON.stringify(body) }),
  deleteFirearm: (id: number) =>
    request<void>(`/api/firearms/${id}`, { method: "DELETE" }),

  // Logbook
  listLogbook: () => request<LogEntry[]>("/api/logbook"),
  createLog: (
    body: Partial<LogEntry> & { caliber: string; quantity: number },
    deduct = false,
  ) =>
    request<LogCreateResult>(`/api/logbook${deduct ? "?deduct=true" : ""}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateLog: (id: number, body: Partial<LogEntry> & { caliber: string; quantity: number }) =>
    request<LogEntry>(`/api/logbook/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteLog: (id: number) =>
    request<void>(`/api/logbook/${id}`, { method: "DELETE" }),

  // PDFs (etiqueta da sessão, relatório de acervo)
  downloadLabel: (sessionId: number) =>
    downloadFile(`/api/logbook/${sessionId}/label`, `etiqueta_${sessionId}.pdf`),
  downloadInspectionReport: () =>
    downloadFile("/api/reports/inspection", "relatorio_acervo.pdf"),

  // Análise de alvo por foto (visão computacional)
  analyzeTarget: async (file: File, p: TargetParams): Promise<TargetAnalysis> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("target_width_mm", String(p.targetWidthMm));
    fd.append("sensitivity", String(p.sensitivity));
    if (p.centerX != null) fd.append("center_x", String(p.centerX));
    if (p.centerY != null) fd.append("center_y", String(p.centerY));
    const res = await fetch(BASE + "/api/targets/analyze", {
      method: "POST",
      headers: { ...tokenHeader() }, // sem Content-Type: o browser põe o boundary
      body: fd,
    });
    if (!res.ok) {
      let detail = `Erro ${res.status}`;
      try {
        const b = await res.json();
        if (b?.detail) detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail);
      } catch {
        /* corpo não-JSON */
      }
      throw new Error(detail);
    }
    return res.json() as Promise<TargetAnalysis>;
  },
  downloadTargetReport: async (file: File, p: TargetParams): Promise<void> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("target_width_mm", String(p.targetWidthMm));
    fd.append("sensitivity", String(p.sensitivity));
    if (p.centerX != null) fd.append("center_x", String(p.centerX));
    if (p.centerY != null) fd.append("center_y", String(p.centerY));
    const res = await fetch(BASE + "/api/targets/report", {
      method: "POST",
      headers: { ...tokenHeader() },
      body: fd,
    });
    if (!res.ok) {
      let detail = `Erro ${res.status}`;
      try {
        const b = await res.json();
        if (b?.detail) detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail);
      } catch {
        /* corpo não-JSON */
      }
      throw new Error(detail);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "relatorio_performance.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  // Cartões de DOPE salvos
  listDopeCards: () => request<DopeCard[]>("/api/dope-cards"),
  createDopeCard: (body: Omit<DopeCard, "id">) =>
    request<DopeCard>("/api/dope-cards", { method: "POST", body: JSON.stringify(body) }),
  deleteDopeCard: (id: number) =>
    request<void>(`/api/dope-cards/${id}`, { method: "DELETE" }),

  // Consultor (IA)
  adviseLoad: (body: {
    caliber: string; projectile?: string | null; powder?: string | null;
    charge?: number | null; velocity?: number | null; sd?: number | null; grouping?: number | null;
  }) => request<Advice>("/api/advisor/load", { method: "POST", body: JSON.stringify(body) }),
  adviseTrend: (sessions: { velocity_avg?: number | null; velocity_sd?: number | null; grouping_mm?: number | null }[]) =>
    request<Advice>("/api/advisor/trend", { method: "POST", body: JSON.stringify({ sessions }) }),
};
