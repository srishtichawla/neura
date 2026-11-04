import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "https://neura-e4cg.onrender.com").replace(/\/$/, "");

export interface Report {
  id: string;
  topic: string;
  report: string;
  citations: string[];
  createdAt: string;
}

export interface User { id: number; email: string; }

interface Store {
  // auth (persisted in localStorage so you stay logged in across tabs/refreshes)
  token: string | null;
  user: User | null;
  hydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;

  // saved reports (stored on the server, per account)
  reports: Report[];
  fetchReports: () => Promise<void>;
  saveReport: (r: Pick<Report, 'topic' | 'report' | 'citations'>) => Promise<void>;
  deleteReport: (id: string) => Promise<void>;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
  } catch { /* not JSON */ }
  if (res.status === 502 || res.status === 503 || res.status === 504)
    return "Server is waking up — please try again in a minute";
  return `Request failed (HTTP ${res.status})`;
}

async function post(path: string, body: unknown) {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection or try again in a minute.");
  }
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export const useStore = create<Store>()(
  persist(
    (set, get) => {
      // fetch with the login token; a 401 means the session is over -> log out
      const authed = async (path: string, init: RequestInit = {}) => {
        const res = await fetch(`${API_URL}${path}`, {
          ...init,
          headers: {
            "Content-Type": "application/json",
            ...(init.headers || {}),
            Authorization: `Bearer ${get().token}`,
          },
        });
        if (res.status === 401) get().logout();
        return res;
      };

      return {
        token: null,
        user: null,
        hydrated: false,
        reports: [],

        login: async (email, password) => {
          const data = await post("/api/auth/login", { email, password });
          set({ token: data.token, user: data.user, reports: [] });
        },
        register: async (email, password) => {
          const data = await post("/api/auth/register", { email, password });
          set({ token: data.token, user: data.user, reports: [] });
        },
        logout: () => set({ token: null, user: null, reports: [] }),

        fetchReports: async () => {
          if (!get().token) return;
          try {
            const res = await authed("/api/reports");
            if (res.ok) set({ reports: (await res.json()).reports });
          } catch (e) { console.error("Could not load reports", e); }
        },
        saveReport: async (r) => {
          try {
            const res = await authed("/api/reports", { method: "POST", body: JSON.stringify(r) });
            if (res.ok) {
              const saved: Report = await res.json();
              set((s) => ({ reports: [saved, ...s.reports] }));
            }
          } catch (e) { console.error("Could not save report", e); }
        },
        deleteReport: async (id) => {
          const before = get().reports;
          set({ reports: before.filter((r) => r.id !== id) });  // instant in the UI
          try {
            const res = await authed(`/api/reports/${id}`, { method: "DELETE" });
            if (!res.ok && res.status !== 404) set({ reports: before });  // undo on failure
          } catch { set({ reports: before }); }
        },
      };
    },
    {
      name: "neura-auth",
      partialize: (s) => ({ token: s.token, user: s.user }),  // only the login is kept locally
      skipHydration: true,  // page rehydrates after mount (avoids SSR mismatch)
    }
  )
);
