import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, initialized } = useAuth()

  // Wait for the initial token check to complete before deciding anything.
  // Without this, the component renders with user=null during the getMe() call
  // and immediately redirects to /login.
  if (!initialized) return null

  if (!user) return <Navigate to="/login" replace />
  return children
}