import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Subscriptions from './pages/Subscriptions'
import Servers from './pages/Servers'
import './styles/global.css'

// Root redirects logged-in users to dashboard, others see landing page
function Root() {
  const { user, initialized } = useAuth()
  if (!initialized) return null
  return user ? <Navigate to="/dashboard" replace /> : <Landing />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Root />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          } />
          <Route path="/servers" element={
            <ProtectedRoute><Servers /></ProtectedRoute>
          } />
          <Route path="/subscriptions" element={
            <ProtectedRoute><Subscriptions /></ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}