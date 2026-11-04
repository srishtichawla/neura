"use client";
import { useState } from "react";
import { useStore } from "../lib/store";

export default function AuthScreen() {
  const { login, register } = useStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setError("");
    if (mode === "register" && password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setBusy(true);
    try {
      await (mode === "login" ? login(email, password) : register(email, password));
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const input: React.CSSProperties = {
    width: "100%", padding: "12px 14px", borderRadius: "10px", fontSize: "14px",
    background: "rgba(255,255,255,0.04)", color: "#e5e7eb",
    border: "1px solid rgba(255,255,255,0.1)", outline: "none", boxSizing: "border-box",
  };

  return (
    <div className="relative min-h-screen z-10" style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "1.5rem" }}>
      <form onSubmit={submit} style={{
        width: "100%", maxWidth: "400px", padding: "2.25rem", borderRadius: "20px",
        background: "rgba(13,17,23,0.92)", border: "1px solid rgba(139,92,246,0.25)",
        display: "flex", flexDirection: "column", gap: "14px",
      }}>
        <div style={{ textAlign: "center", marginBottom: "6px" }}>
          <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 900, fontSize: "26px", color: "#fff" }}>
            Neura <span style={{ fontSize: "11px", color: "#4b5563", letterSpacing: "0.15em" }}>AI</span>
          </div>
          <p style={{ fontSize: "13px", color: "#6b7280", marginTop: "6px" }}>
            {mode === "login" ? "Sign in to see your saved reports and documents" : "Create an account to save your research"}
          </p>
        </div>

        <input style={input} type="email" placeholder="Email" autoComplete="email" required
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <input style={input} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required
          placeholder={mode === "register" ? "Password (min 8 characters)" : "Password"}
          value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && (
          <div style={{ fontSize: "13px", padding: "9px 12px", borderRadius: "8px", background: "rgba(239,68,68,0.1)", color: "#f87171", border: "1px solid rgba(239,68,68,0.25)" }}>
            {error}
          </div>
        )}

        <button type="submit" disabled={busy} style={{
          padding: "12px", borderRadius: "10px", border: "none", fontWeight: 700, fontSize: "14px",
          cursor: busy ? "wait" : "pointer", color: "#fff", opacity: busy ? 0.7 : 1,
          background: "linear-gradient(135deg,#8b5cf6,#00d4ff)",
        }}>
          {busy ? "Please wait… (the server may take a minute to wake up)" : mode === "login" ? "Sign in" : "Create account"}
        </button>

        <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
          style={{ background: "none", border: "none", color: "#a78bfa", fontSize: "13px", cursor: "pointer" }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
