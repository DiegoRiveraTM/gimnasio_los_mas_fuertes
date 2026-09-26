import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { api } from "../lib/api";
import { Link, useNavigate } from "react-router";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const savedEmail = localStorage.getItem("gym_remembered_email");
    if (savedEmail) { setEmail(savedEmail); setRemember(true); }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  }, [isDark]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;
    setError("");
    setIsLoading(true);
    try {
      const result = await api.login(email, password);
      // El JWT nunca se imprime ni se guarda junto con la contraseña.
      sessionStorage.setItem("gym_access_token", result.access_token);
      // Por ahora "Recordarme" recuerda solo el correo, no prolonga la sesión.
      if (remember) localStorage.setItem("gym_remembered_email", email.trim());
      else localStorage.removeItem("gym_remembered_email");
      setPassword("");
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{ background: "var(--bg-app)" }}
      className="min-h-screen flex transition-colors duration-300"
    >
      {/* Theme toggle */}
      <button
        type="button"
        onClick={() => setIsDark((v) => !v)}
        aria-label="Toggle theme"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-color)",
          color: "var(--text-primary)",
        }}
        className="fixed top-5 right-5 z-10 w-10 h-10 rounded-full flex items-center justify-center hover:scale-105 transition"
      >
        {isDark ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>

      {/* Left panel */}
      <div
        style={{ background: "var(--panel-dark)" }}
        className="hidden lg:flex flex-col justify-center px-16 w-[52%] relative overflow-hidden"
      >
        {/* Decorative glow blobs */}
        <div
          style={{ background: "var(--accent)" }}
          className="absolute -top-24 -left-24 w-72 h-72 rounded-full opacity-20 blur-3xl"
        />
        <div
          style={{ background: "var(--accent)" }}
          className="absolute bottom-0 right-0 w-96 h-96 rounded-full opacity-10 blur-3xl"
        />

        <div className="relative z-[1]">
          <div className="flex items-center gap-2.5 mb-16">
            <div
              style={{ background: "var(--accent)" }}
              className="w-9 h-9 rounded-xl flex items-center justify-center"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1c1400" strokeWidth="2.2">
                <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span className="text-white font-semibold text-xl tracking-tight">
              Gym-LMF
            </span>
          </div>

          <h2 className="text-white text-3xl font-semibold leading-tight mb-3 max-w-sm">
            Tu Gimnasio{" "}
            <span style={{ color: "var(--accent)" }}>en un solo lugar</span>
          </h2>
          <p className="text-[#9c9a8e] text-sm mb-14 max-w-sm">
            Inicia sesión y entra a tu gimnasio con nuestros QR's.
          </p>


        </div>
      </div>

      {/* Right panel — form card */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div
          style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}
          className="w-full max-w-[420px] border rounded-2xl p-8 transition-colors duration-300"
        >
          <div className="flex items-center gap-2 mb-1 lg:hidden">
            <div
              style={{ background: "var(--accent)" }}
              className="w-7 h-7 rounded-lg flex items-center justify-center"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c1400" strokeWidth="2.4">
                <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span style={{ color: "var(--text-primary)" }} className="font-semibold text-base">
              Sitemark
            </span>
          </div>

          <h1 style={{ color: "var(--text-primary)" }} className="text-3xl font-semibold mb-1 mt-4 lg:mt-0">
            Bienvenido de vuelta
          </h1>
          <p style={{ color: "var(--text-secondary)" }} className="text-sm mb-6">
            Ingresa tus datos para continuar
          </p>

          <form onSubmit={handleSubmit} className="space-y-4" aria-busy={isLoading}>
            <fieldset disabled={isLoading} className="space-y-4">
            <div>
              <label style={{ color: "var(--text-primary)" }} className="block text-sm font-medium mb-1.5" htmlFor="email">
                Correo
              </label>
              <input
                id="email"
                type="email"
                placeholder="tucorreo@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  background: "var(--bg-input)",
                  borderColor: "var(--border-color)",
                  color: "var(--text-primary)",
                }}
                className="w-full border rounded-lg px-3 py-2.5 text-sm outline-none transition focus:ring-2"
                onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-color)")}
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label style={{ color: "var(--text-primary)" }} className="text-sm font-medium" htmlFor="password">
                  Contraseña
                </label>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{
                    background: "var(--bg-input)",
                    borderColor: "var(--border-color)",
                    color: "var(--text-primary)",
                  }}
                  className="w-full border rounded-lg px-3 py-2.5 text-sm outline-none transition pr-10"
                  onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                  onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-color)")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  style={{ color: "var(--text-muted)" }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 hover:opacity-70 transition"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <label className="flex items-center gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                style={{ accentColor: "var(--accent)" }}
                className="w-4 h-4 rounded cursor-pointer"
              />
              <span style={{ color: "var(--text-primary)" }} className="text-sm">
                Recordarme
              </span>
            </label>

            {error && <p role="alert" className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={isLoading}
              style={{ background: "var(--accent)", color: "var(--accent-text)" }}
              className="w-full font-semibold text-sm py-2.5 rounded-lg transition hover:brightness-95 active:scale-[0.99] mt-2"
            >
              {isLoading ? "Iniciando sesión…" : "Iniciar sesión"}
            </button>
            </fieldset>
          </form>

          <p style={{ color: "var(--text-secondary)" }} className="text-center text-sm mt-4">
            ¿No tienes cuenta?{" "}
            <Link to="/register" style={{ color: "var(--accent-hover)" }} className="font-semibold hover:underline">
              Regístrate
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
