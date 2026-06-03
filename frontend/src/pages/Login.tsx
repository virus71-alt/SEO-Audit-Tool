import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [err, setErr] = useState<string | null>(null);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      if (mode === "register") await register(email, password);
      await login(email, password);
      navigate("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? "Failed");
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-12">
      <h1 className="text-2xl font-bold mb-6">
        {mode === "login" ? "Sign in" : "Create account"}
      </h1>
      <form onSubmit={submit} className="space-y-3">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent px-4 py-2"
        />
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent px-4 py-2"
        />
        {err && <div className="text-sm text-rose-500">{err}</div>}
        <button className="w-full rounded-lg bg-brand-600 text-white py-2 font-medium">
          {mode === "login" ? "Sign in" : "Register"}
        </button>
        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="text-xs text-slate-500"
        >
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
