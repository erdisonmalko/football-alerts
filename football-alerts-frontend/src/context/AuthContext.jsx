import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, logout as apiLogout } from '../api/endpoints'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [initialized, setInitialized] = useState(false)

  // On mount, check if we have a valid session cookie by calling /auth/me
  // The cookie is sent automatically — we never touch the token directly
  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => {}) // no session, that's fine
      .finally(() => setInitialized(true))
  }, [])

  const signIn = (userData) => {
    setUser(userData)
  }

  const signOut = async () => {
    await apiLogout().catch(() => {})  // tell server to clear cookie
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, initialized, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)