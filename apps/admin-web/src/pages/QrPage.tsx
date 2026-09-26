import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ApiError, generateAccessQr, getAccessQrStatus, logout } from '../lib/api'
import type { AccessQr } from '../lib/api'

export default function QrPage() {
  const navigate = useNavigate()
  const [qr, setQr] = useState<AccessQr | null>(null)
  const [seconds, setSeconds] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [deadline, setDeadline] = useState(0)
  const [qrState, setQrState] = useState<'pending' | 'expired' | 'unknown'>('pending')
  const [statusWarning, setStatusWarning] = useState('')
  const requestRef = useRef<AbortController | null>(null)

  useEffect(() => () => { requestRef.current?.abort() }, [])

  useEffect(() => {
    if (!deadline) return
    const update = () => setSeconds(Math.max(0, Math.ceil((deadline - performance.now()) / 1000)))
    update()
    const timer = window.setInterval(update, 250)
    return () => window.clearInterval(timer)
  }, [deadline])


  useEffect(() => {
    if (!qr) return
    const controller = new AbortController()
    let timer: number | undefined
    let stopped = false
    const stopAt = performance.now() + 120_000

    async function poll() {
      if (stopped || controller.signal.aborted) return
      try {
        const state = await getAccessQrStatus(qr!.qr_id, controller.signal)
        if (stopped || controller.signal.aborted) return
        setStatusWarning('')
        if (state === 'used') {
          stopped = true
          navigate('/dashboard', { replace: true })
          return
        }
        if (state === 'expired') {
          stopped = true
          setQrState('expired')
          setSeconds(0)
          setDeadline(0)
          return
        }
      } catch (err: unknown) {
        if (stopped || controller.signal.aborted) return
        if (err instanceof ApiError && err.status === 401) {
          stopped = true
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err instanceof ApiError && err.status === 404) {
          stopped = true
          setQrState('unknown')
          setSeconds(0)
          setDeadline(0)
          setStatusWarning('Ya no se encuentra el estado de este QR. Genera uno nuevo.')
          return
        }
        setStatusWarning('No se pudo consultar el estado. Volveremos a intentar.')
      }
      if (performance.now() >= stopAt) {
        stopped = true
        setQrState('unknown')
        setSeconds(0)
        setDeadline(0)
        setStatusWarning('No se pudo confirmar el resultado. Vuelve a tu cuenta o genera otro QR.')
        return
      }
      timer = window.setTimeout(() => { void poll() }, 2000)
    }
    void poll()
    return () => {
      stopped = true
      controller.abort()
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [qr, navigate])

  async function generate() {
    if (requestRef.current) return
    const controller = new AbortController()
    requestRef.current = controller
    setLoading(true)
    setError('')
    setStatusWarning('')
    setQrState('pending')
    setQr(null)
    setSeconds(0)
    setDeadline(0)
    const requestedAt = performance.now()
    try {
      const result = await generateAccessQr(controller.signal)
      if (controller.signal.aborted) return
      // Restar el tiempo de la petición evita reiniciar los 60 s al recibirla.
      // Redis y el backend son la autoridad final sobre validez y uso único.
      const localDeadline = requestedAt + result.expires_in_seconds * 1000
      const remaining = Math.max(0, Math.ceil((localDeadline - performance.now()) / 1000))
      if (!remaining) {
        setError('El QR expiró antes de poder mostrarse. Intenta generar otro.')
        return
      }
      setQr(result)
      setDeadline(localDeadline)
      setSeconds(remaining)
    } catch (err: unknown) {
      if (controller.signal.aborted) return
      if (err instanceof ApiError && err.status === 401) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setError(err instanceof Error ? err.message : 'No se pudo generar el QR.')
    } finally {
      if (requestRef.current === controller) requestRef.current = null
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  const visible = qr !== null && seconds > 0 && qrState === 'pending'
  return (
    <main className="flex min-h-screen items-center justify-center px-5 py-10"
      style={{ background: 'var(--bg-app)', color: 'var(--text-primary)' }}>
      <section className="w-full max-w-md rounded-2xl border p-8"
        style={{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--accent-hover)' }}>Gym-LMF</p>
        <h1 className="text-2xl font-semibold">Mi QR de acceso</h1>
        <p className="mt-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Genera tu código cuando estés listo para entrar. Es de un solo uso.
        </p>

        <div className="my-6 flex min-h-64 items-center justify-center rounded-xl border p-4"
          style={{ borderColor: 'var(--border-color)' }}>
          {loading ? <p role="status" className="text-sm">Generando QR…</p> :
            visible ? <div className="rounded-lg bg-white p-3">
              <img src={qr.qr_code} alt="Código QR para acceder al gimnasio"
                className="h-56 w-56 max-w-full object-contain" />
            </div> :
            <p className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
              {qr ? qrState === 'expired' ? 'Tu QR ha expirado. Genera uno nuevo.' : qrState === 'unknown' ? 'No se pudo confirmar el estado del QR.' : 'Comprobando el estado final del QR…' : 'Pulsa el botón para generar tu QR.'}
            </p>}
        </div>

        {visible && <div className="mb-5 text-center">
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Tiempo restante</p>
          <p className="mt-1 text-3xl font-bold" style={{ color: 'var(--accent-hover)' }}>{seconds} s</p>
          <p className="mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>Cuando recepción lo valide, volverás automáticamente a tu cuenta.</p>
        </div>}

        {statusWarning && <p role="status" className="mb-4 text-sm" style={{ color: 'var(--text-secondary)' }}>{statusWarning}</p>}
        {error && <p role="alert" className="mb-4 text-sm text-red-500">{error}</p>}
        <button type="button" onClick={() => void generate()} disabled={loading || (qr !== null && qrState === 'pending')}
          className="w-full rounded-lg px-5 py-3 text-sm font-semibold transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
          style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}>
          {loading ? 'Generando…' : (qr !== null && qrState === 'pending') ? 'Esperando validación' : qr ? 'Generar nuevo QR' : 'Generar mi QR'}
        </button>
        <Link to="/dashboard" className="mt-5 block text-center text-sm font-semibold" style={{ color: 'var(--accent-hover)' }}>
          Volver a mi cuenta
        </Link>
      </section>
    </main>
  )
}
