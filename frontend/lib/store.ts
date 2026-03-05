import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Report {
  id: string;
  topic: string;
  report: string;
  citations: string[];
  createdAt: string;
}

interface Store {
  reports: Report[];
  saveReport: (r: Omit<Report, 'id' | 'createdAt'>) => void;
  deleteReport: (id: string) => void;
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      reports: [],
      saveReport: (r) => set((s) => ({
        reports: [{
          ...r,
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
        }, ...s.reports]
      })),
      deleteReport: (id) => set((s) => ({
        reports: s.reports.filter(r => r.id !== id)
      })),
    }),
    { name: 'research-reports' }
  )
);
