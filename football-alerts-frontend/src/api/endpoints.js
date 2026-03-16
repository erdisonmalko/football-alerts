import api from './client'

//health
export const checkHealth = () => api.get('/health').then(r => r.data)

// Auth
export const register = (email, password, fullName) =>
  api.post('/auth/register', { email, password, full_name: fullName })

export const login = async (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  // Returns the user object directly; cookie is set by the server
  const res = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get('/auth/me').then(r => r.data)

// Subscriptions
export const getSubscriptions = () =>
  api.get('/users/me/subscriptions').then(r => r.data)

export const addSubscription = (type, externalId, displayName) =>
  api.post('/users/me/subscriptions', {
    subscription_type: type,
    external_id: externalId,
    display_name: displayName,
  }).then(r => r.data)

export const removeSubscription = (id) =>
  api.delete(`/users/me/subscriptions/${id}`)

// Profile
export const updateProfile = (data) =>
  api.patch('/users/me', data).then(r => r.data)

export const deleteAccount = () =>
  api.delete('/users/me')

// Upcoming matches (browse)
export const getUpcomingMatches = (queryString = '') =>
  api.get(`/football/matches/upcoming${queryString}`).then(r => r.data)

// Football data
export const getLeagues = () =>
  api.get('/football/leagues').then(r => r.data)

export const getTeamsByLeague = (code) =>
  api.get(`/football/leagues/${code}/teams`).then(r => r.data)

// User matches (dashboard — live, upcoming, finished)
export const getMyMatches = () =>
  api.get('/users/me/matches').then(r => r.data)