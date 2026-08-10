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
};

export type DopeEntry = {
  range_m: number;
  unit: string;
  elevation: number;
  elevation_clicks: number;
  windage: number;
  windage_dir: string;
  windage_clicks: number;
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

export type Caliber = {
  projectiles: Record<string, { powders: Record<string, unknown> }>;
  [k: string]: unknown;
};
export type Catalog = { calibers: Record<string, Caliber> };

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

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  catalog: () => request<Catalog>("/api/catalog"),
  trajectory: (body: unknown) =>
    request<TrajectoryResponse>("/api/trajectory", {
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
  createLog: (body: Partial<LogEntry> & { caliber: string; quantity: number }) =>
    request<LogEntry>("/api/logbook", { method: "POST", body: JSON.stringify(body) }),
  deleteLog: (id: number) =>
    request<void>(`/api/logbook/${id}`, { method: "DELETE" }),
};
