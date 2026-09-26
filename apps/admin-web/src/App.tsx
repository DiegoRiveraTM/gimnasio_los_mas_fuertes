import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import QrPage from './pages/QrPage'
import { getAccessToken } from './lib/api'
import type { ReactNode } from 'react'

function RequireSession({ children }: { children: ReactNode }) {
  return getAccessToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<RequireSession><DashboardPage /></RequireSession>} />
        <Route path="/qr" element={<RequireSession><QrPage /></RequireSession>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
