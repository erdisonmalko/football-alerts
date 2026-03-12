import api from './client'

// Auth
export const register = (email, password, fullName) =>
  api.post('/auth/register', { email, password, full_name: fullName })

export const login = async (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

// User
export const getMe = () => api.get('/users/me').then(r => r.data)

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

// Football data
export const getLeagues = () =>
  api.get('/football/leagues').then(r => r.data)

export const getTeamsByLeague = (code) =>
  api.get(`/football/leagues/${code}/teams`).then(r => r.data)
