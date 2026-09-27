import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ApiError, getAccessToken, getCurrentUser, getMyMembership, logout } from '../lib/api'
import type { CurrentUser, Membership } from '../lib/api'

function formatDate(value: string | null) {
  if (!value) return 'No disponible'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'No disponible' :
    date.toLocaleDateString('es', { day: 'numeric', month: 'long', year: 'numeric' })
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [membership, setMembership] = useState<Membership | null>(null)
  const [userError, setUserError] = useState('')
  const [membershipError, setMembershipError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  const [now, setNow] = useState(() => Date.now())
  const [isDark, setIsDark] = useState(() => document.documentElement.dataset.theme === 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light'
  }, [isDark])

  useEffect(() => {
    if (!getAccessToken()) {
      navigate('/login', { replace: true })
      return
    }
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setUser(null)
      setMembership(null)
      setUserError('')
      setMembershipError('')
      const results = await Promise.allSettled([
        getCurrentUser(controller.signal),
        getMyMembership(controller.signal),
      ])
      if (controller.signal.aborted) return
      const expired = results.some(result =>
        result.status === 'rejected' && result.reason instanceof ApiError && result.reason.status === 401)
      if (expired) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      const [userResult, membershipResult] = results
      if (userResult.status === 'fulfilled') setUser(userResult.value)
      else setUserError(userResult.reason instanceof Error ? userResult.reason.message : 'No se pudo cargar el usuario.')
      if (membershipResult.status === 'fulfilled') setMembership(membershipResult.value)
      else setMembershipError(membershipResult.reason instanceof Error ? membershipResult.reason.message : 'No se pudo cargar la membresía.')
      setLoading(false)
    }
    void load()
    return () => controller.abort()
  }, [navigate, retry])

  // Actualiza la vigencia incluso si el usuario deja abierto el dashboard.
  useEffect(() => {
    const update = () => setNow(Date.now())
    update()
    const timer = window.setInterval(update, 1000)
    window.addEventListener('focus', update)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('focus', update)
    }
  }, [])

  const cardStyle = { background: 'var(--bg-card)', borderColor: 'var(--border-color)' }
  const expiresAt = membership?.next_payment_at
    ? Date.parse(membership.next_payment_at) : Number.NaN
  const validExpiry = Number.isFinite(expiresAt)
  const effectiveStatus = membership?.status === 'active'
    ? !validExpiry ? 'unknown' : expiresAt <= now ? 'expired' : 'active'
    : membership?.status ?? 'unknown'
  // El backend es la autoridad; esta comprobación solo ajusta la interfaz.
  const active = Boolean(user && effectiveStatus === 'active' && !loading)
  const planLabels: Record<string, string> = { bronze: 'Bronce', silver: 'Plata', gold: 'Oro' }
  const statusLabels: Record<string, string> = { active: 'Activa', inactive: 'Inactiva', expired: 'Vencida', suspended: 'Suspendida', unknown: 'No disponible' }

  return (
    <div className="min-h-screen transition-colors" style={{ background: 'var(--bg-app)', color: 'var(--text-primary)' }}>
      <header className="border-b" style={{ borderColor: 'var(--border-color)' }}>
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-5 py-5">
          <Link to="/dashboard" className="text-xl font-bold">Gym<span style={{ color: 'var(--accent-hover)' }}>-LMF</span></Link>
          <div className="flex items-center gap-4">
            <button type="button" onClick={() => setIsDark(value => !value)} className="text-sm">
              {isDark ? 'Modo claro' : 'Modo oscuro'}
            </button>
            <button type="button" className="text-sm font-medium" onClick={() => {
              logout()
              navigate('/login', { replace: true })
            }}>Cerrar sesión</button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-5 py-10">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--accent-hover)' }}>Tu gimnasio, en un solo lugar</p>
          <h1 className="text-3xl font-semibold">{user ? `Hola, ${user.username}` : 'Mi cuenta'}</h1>
          <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>Consulta tu membresía y accede a tu código QR.</p>
        </div>

        {loading && <p role="status" className="text-sm">Cargando tu información…</p>}

        <div className="grid gap-6 md:grid-cols-2">
          <section className="rounded-2xl border p-6" style={cardStyle}>
            <h2 className="mb-5 text-lg font-semibold">Información del usuario</h2>
            {userError && <p role="alert" className="text-sm text-red-500">{userError}</p>}
            {user && (
              <dl className="space-y-5">
                <div><dt className="text-sm" style={{ color: 'var(--text-secondary)' }}>Nombre de usuario</dt><dd className="mt-1 font-medium">{user.username}</dd></div>
                <div><dt className="text-sm" style={{ color: 'var(--text-secondary)' }}>Correo electrónico</dt><dd className="mt-1 break-all font-medium">{user.email}</dd></div>
              </dl>
            )}
          </section>

          <section className="rounded-2xl border p-6" style={cardStyle}>
            <h2 className="mb-5 text-lg font-semibold">Mi membresía</h2>
            {membershipError && <p role="alert" className="text-sm text-red-500">{membershipError}</p>}
            {!loading && !membershipError && !membership && <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Todavía no tienes una membresía. Contacta a recepción para activarla.</p>}
            {membership && (
              <>
                <div className="mb-6 flex items-center justify-between gap-3">
                  <p className="text-2xl font-bold">{planLabels[membership.membership_type] || membership.membership_type}</p>
                  <span className="rounded-full border px-3 py-1 text-xs font-semibold" style={{
                    borderColor: effectiveStatus === 'active' ? 'var(--accent)' : 'var(--border-color)',
                    color: effectiveStatus === 'active' ? 'var(--accent-hover)' : 'var(--text-secondary)',
                  }}>{statusLabels[effectiveStatus] || effectiveStatus}</span>
                </div>
                <dl className="space-y-4 text-sm">
                  <div className="flex justify-between gap-4"><dt style={{ color: 'var(--text-secondary)' }}>Costo mensual</dt><dd className="font-semibold">{Number.isFinite(Number(membership.monthly_cost)) ? Number(membership.monthly_cost).toLocaleString('es', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : membership.monthly_cost}</dd></div>
                  <div><dt style={{ color: 'var(--text-secondary)' }}>Activa desde</dt><dd className="mt-1 font-medium">{formatDate(membership.active_since)}</dd></div>
                  <div><dt style={{ color: 'var(--text-secondary)' }}>Próximo pago</dt><dd className="mt-1 font-medium">{formatDate(membership.next_payment_at)}</dd></div>
                </dl>
              </>
            )}
          </section>
        </div>

        {(userError || membershipError) && <button type="button" onClick={() => setRetry(value => value + 1)} className="text-sm font-semibold underline" style={{ color: 'var(--accent-hover)' }}>Reintentar consulta</button>}

        <section className="rounded-2xl border p-6" style={cardStyle}>
          <h2 className="text-lg font-semibold">Tu acceso al gimnasio</h2>
          <p className="mb-5 mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>Abre la pantalla de QR cuando estés listo para entrar.</p>
          <button type="button" disabled={!active} onClick={() => navigate('/qr')}
            className="w-full rounded-lg px-6 py-3 text-sm font-semibold transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}>Mostrar mi QR</button>
          {!loading && !active && <p className="mt-3 text-xs" style={{ color: 'var(--text-secondary)' }}>{effectiveStatus === 'expired' ? 'Tu membresía está vencida. Contacta a recepción para renovarla.' : 'Necesitas una sesión válida y una membresía vigente para continuar.'}</p>}
        </section>
      </main>
    </div>
  )
}
