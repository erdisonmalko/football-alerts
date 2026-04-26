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

// Add match to user's calendar
export const addMatchToCalendar = (matchId) =>
  api.post(`/calendar/matches/add-match/${matchId}`)

export const removeMatchFromCalendar = (matchId) =>
  api.delete(`/calendar/matches/remove-match/${matchId}`)

// User matches (dashboard — live, upcoming, finished)
export const getMyMatches = () =>
  api.get('/users/me/matches').then(r => r.data)

// Google Calendar

export const getGoogleStatus = () =>
  api.get('/auth/google/status').then(r => r.data)

export const connectGoogle = () => {
  // Redirect browser to backend OAuth flow
  window.location.href = `${import.meta.env.VITE_API_URL}/auth/google/connect`
}

export const disconnectGoogle = () =>
  api.delete('/auth/google/disconnect')

// Servers
export const getMyServers = () =>
  api.get('/servers/my-servers').then(r => r.data)

export const getPublicServers = () =>
  api.get('/servers/').then(r => r.data)

export const requestToJoin = (serverId) =>
  api.post(`/servers/${serverId}/request-join`).then(r => r.data)

export const joinByInvite = (inviteCode, serverId) =>
  api.post(`/servers/${serverId}/request-join-by-code`, {
    invite_code: inviteCode
  }).then(r => r.data)

export const getJoinRequests = (serverId) =>
  api.get(`/servers/${serverId}/join-requests/list`).then(r => r.data)

export const handleJoinRequest = (serverId, requestId, action) =>
  api.post(`/servers/${serverId}/join-requests/${requestId}`, 
    { accept: action }
  ).then(r => r.data) 

export const getPendingRequestsCount = () =>
  api.get('/servers/pending-requests-count').then(r => r.data)
 
export const createServer = (name, isPublic) =>
  api.post('/servers/', { name, is_public: isPublic }).then(r => r.data)

export const getServer = (serverId) =>
  api.get(`/servers/${serverId}`).then(r => r.data)

export const leaveServer = (serverId) =>
  api.delete(`/servers/${serverId}/leave`).then(r => r.data)

export const updateServer = (serverId, name, isPublic) =>
  api.patch(`/servers/${serverId}`, { name, is_public: isPublic }).then(r => r.data)

export const regenerateInviteCode = (serverId) =>
  api.post(`/servers/${serverId}/regenerate-invite-code`).then(r => r.data)

export const getServerLeaderboard = (serverId) =>
  api.get(`/servers/${serverId}/leaderboard`).then(r => r.data)

export const getServerChallenges = (serverId) =>
  api.get(`/servers/${serverId}/challenges`).then(r => r.data)