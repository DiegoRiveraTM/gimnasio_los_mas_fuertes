const AUTH_API_URL = (import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function post(path: string, payload: Record<string, string>): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`${AUTH_API_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error('No se pudo conectar con auth-service. Revisa el servidor y CORS.')
  }
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    let message = 'No se pudo completar la solicitud.'
    if (response.status === 401) message = 'Correo o contraseña incorrectos.'
    else if (response.status === 409) message = 'El correo o usuario ya está registrado.'
    else if (response.status === 429) message = 'Demasiados intentos. Espera y vuelve a probar.'
    else if (body && typeof body === 'object' && 'detail' in body) {
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) {
        const messages = body.detail.flatMap((item: unknown) =>
          item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string'
            ? [item.msg] : [],
        )
        if (messages.length) message = messages.join(' ')
      }
    }
    throw new ApiError(response.status, message)
  }
  return body
}

export const api = {
  async register(username: string, email: string, password: string): Promise<void> {
    await post('/auth/register', { username: username.trim(), email: email.trim(), password })
  },
  async login(email: string, password: string): Promise<{ access_token: string }> {
    const body = await post('/auth/login', { email: email.trim(), password })
    if (!body || typeof body !== 'object' || !('access_token' in body) ||
        typeof body.access_token !== 'string' || !body.access_token) {
      throw new Error('El servidor no devolvió un token de acceso válido.')
    }
    return { access_token: body.access_token }
  },
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem('gym_access_token')
}

export function logout(): void {
  sessionStorage.removeItem('gym_access_token')
}


export interface CurrentUser {
  id: string
  username: string
  email: string
}

export interface Membership {
  id: string
  membership_type: string
  monthly_cost: string
  status: string
  active_since: string | null
  next_payment_at: string | null
}

const MEMBERSHIP_API_URL = (import.meta.env.VITE_MEMBERSHIP_API_URL || 'http://localhost:8001').replace(/\/$/, '')

async function authenticatedGet(base: string, path: string, signal?: AbortSignal): Promise<unknown> {
  const token = getAccessToken()
  if (!token) throw new ApiError(401, 'Inicia sesión para continuar.')
  let response: Response
  try {
    response = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      signal,
    })
  } catch (err) {
    if (signal?.aborted) throw err
    throw new Error('No se pudo conectar con el servicio. Revisa que esté encendido y permita CORS.')
  }
  if (!response.ok) {
    if (response.status === 401) throw new ApiError(401, 'Tu sesión expiró. Inicia sesión nuevamente.')
    if (response.status === 404) throw new ApiError(404, 'No se encontró la información solicitada.')
    throw new ApiError(response.status, 'El servicio no pudo completar la consulta.')
  }
  return response.json()
}

export async function getCurrentUser(signal?: AbortSignal): Promise<CurrentUser> {
  const data = await authenticatedGet(AUTH_API_URL, '/auth/me', signal)
  if (!data || typeof data !== 'object' ||
      !('id' in data) || typeof data.id !== 'string' ||
      !('username' in data) || typeof data.username !== 'string' ||
      !('email' in data) || typeof data.email !== 'string') {
    throw new Error('La respuesta del usuario no tiene el formato esperado.')
  }
  return { id: data.id, username: data.username, email: data.email }
}

export async function getMyMembership(signal?: AbortSignal): Promise<Membership | null> {
  let data: unknown
  try {
    data = await authenticatedGet(MEMBERSHIP_API_URL, '/memberships/me', signal)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null
    throw err
  }
  if (!data || typeof data !== 'object' ||
      !('id' in data) || typeof data.id !== 'string' ||
      !('membership_type' in data) || typeof data.membership_type !== 'string' ||
      !('monthly_cost' in data) || typeof data.monthly_cost !== 'string' ||
      !('status' in data) || typeof data.status !== 'string') {
    throw new Error('La respuesta de membresía no tiene el formato esperado.')
  }
  return {
    id: data.id,
    membership_type: data.membership_type,
    monthly_cost: data.monthly_cost,
    status: data.status,
    active_since: 'active_since' in data && typeof data.active_since === 'string' ? data.active_since : null,
    next_payment_at: 'next_payment_at' in data && typeof data.next_payment_at === 'string' ? data.next_payment_at : null,
  }
}


export interface AccessQr {
  qr_id: string
  qr_code: string
  expires_at: string
  expires_in_seconds: number
}

const QR_API_URL = (import.meta.env.VITE_QR_API_URL || 'http://localhost:8002').replace(/\/$/, '')

export async function generateAccessQr(signal?: AbortSignal): Promise<AccessQr> {
  const token = getAccessToken()
  if (!token) throw new ApiError(401, 'Inicia sesión para continuar.')
  let response: Response
  try {
    response = await fetch(`${QR_API_URL}/qr/me`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      signal,
    })
  } catch (err) {
    if (signal?.aborted) throw err
    throw new Error('No se pudo conectar con QR. Revisa el servicio y su configuración CORS.')
  }
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    let message = 'No se pudo generar el QR.'
    if (response.status === 401) message = 'Tu sesión no es válida. Inicia sesión nuevamente.'
    else if (response.status === 403) message = 'Necesitas una membresía activa para generar el QR.'
    else if (response.status === 404) message = 'No se encontró tu membresía.'
    else if (response.status === 429) message = 'Demasiados intentos. Espera antes de generar otro QR.'
    else if (response.status === 503) message = 'El servicio QR o una de sus dependencias no está disponible.'
    else if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') message = body.detail
    throw new ApiError(response.status, message)
  }
  if (!body || typeof body !== 'object' ||
      !('qr_id' in body) || typeof body.qr_id !== 'string' || !/^[0-9a-f]{64}$/.test(body.qr_id) ||
      !('qr_code' in body) || typeof body.qr_code !== 'string' ||
      !/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(body.qr_code) ||
      !('expires_at' in body) || typeof body.expires_at !== 'string' ||
      !Number.isFinite(Date.parse(body.expires_at)) ||
      !('expires_in_seconds' in body) || typeof body.expires_in_seconds !== 'number' ||
      !Number.isFinite(body.expires_in_seconds) || body.expires_in_seconds <= 0) {
    throw new Error('El servidor no devolvió un QR válido.')
  }
  return { qr_id: body.qr_id, qr_code: body.qr_code, expires_at: body.expires_at, expires_in_seconds: body.expires_in_seconds }
}


export async function getAccessQrStatus(qrId: string, signal?: AbortSignal): Promise<'pending' | 'used' | 'expired'> {
  const data = await authenticatedGet(QR_API_URL, `/qr/status/${encodeURIComponent(qrId)}`, signal)
  if (!data || typeof data !== 'object' || !('state' in data) ||
      (data.state !== 'pending' && data.state !== 'used' && data.state !== 'expired')) {
    throw new Error('El servidor devolvió un estado de QR inesperado.')
  }
  return data.state
}
