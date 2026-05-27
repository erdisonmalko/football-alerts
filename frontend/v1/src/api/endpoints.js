import api from './client'

// ==========================================
// SYSTEM / HEALTH
// ==========================================

export const checkHealth = () => api.get('/health').then(r => r.data)


// ==========================================
// AUTHENTICATION
// ==========================================

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


// ==========================================
// USER & PROFILE
// ==========================================

export const updateProfile = (data) =>
  api.patch('/users/me', data).then(r => r.data)

export const deleteAccount = () =>
  api.delete('/users/me')

export const getUserProfileStats = () => 
  api.get('/users/me/profile-stats').then(r => r.data)

// User matches (dashboard — live, upcoming, finished)
export const getMyMatches = () =>
  api.get('/users/me/matches').then(r => r.data)

export const getMyMatchesPaged = ({ section = 'upcoming', page = 1, pageSize = 10 } = {}) => {
  const params = new URLSearchParams()
  params.append('section', section)
  params.append('page', page)
  params.append('page_size', pageSize)
  return api.get(`/users/me/matches/paged?${params.toString()}`).then(r => r.data)
}


// ==========================================
// SUBSCRIPTIONS
// ==========================================

export const getSubscriptions = ({ page = 1, pageSize = 15, subscriptionType = null } = {}) => {
  const params = new URLSearchParams()
  params.append('page', page)
  params.append('page_size', pageSize)
  if (subscriptionType) params.append('subscription_type', subscriptionType)
  return api.get(`/users/me/subscriptions?${params.toString()}`).then(r => r.data)
}

export const addSubscription = (type, externalId, displayName) =>
  api.post('/users/me/subscriptions', {
    subscription_type: type,
    external_id: externalId,
    display_name: displayName,
  }).then(r => r.data)

export const removeSubscription = (id) =>
  api.delete(`/users/me/subscriptions/${id}`)


// ==========================================
// FOOTBALL DATA
// ==========================================

// Upcoming matches (browse) - change the query string to static page and page number
export const getUpcomingMatches = (queryString = '') =>
  api.get(`/football/matches/upcoming${queryString}`).then(r => r.data)

export const getLeagues = () =>
  api.get('/football/leagues').then(r => r.data)

export const getTeamsByLeague = (code) =>
  api.get(`/football/leagues/${code}/teams`).then(r => r.data)


// ==========================================
// CALENDAR INTEGRATIONS
// ==========================================

// In-App Match Calendar
export const addMatchToCalendar = (matchId) =>
  api.post(`/calendar/matches/add-match/${matchId}`)

export const removeMatchFromCalendar = (matchId) =>
  api.delete(`/calendar/matches/remove-match/${matchId}`)

// Google Calendar OAuth
export const getGoogleStatus = () =>
  api.get('/auth/google/status').then(r => r.data)

export const connectGoogle = () => {
  // Redirect browser to backend OAuth flow
  window.location.href = `${import.meta.env.VITE_API_URL}/auth/google/connect`
}

export const disconnectGoogle = () =>
  api.delete('/auth/google/disconnect')


// ==========================================
// SERVERS
// ==========================================

export const getMyServers = ({ page = 1, pageSize = 15 } = {}) =>
  api.get(`/servers/my-servers?page=${page}&page_size=${pageSize}`).then(r => r.data)

export const getPublicServers = ({ page = 1, pageSize = 15 } = {}) =>
  api.get(`/servers/?page=${page}&page_size=${pageSize}`).then(r => r.data)

export const createServer = (name, isPublic) =>
  api.post('/servers/', { name, is_public: isPublic }).then(r => r.data)

export const getServer = (serverId) =>
  api.get(`/servers/${serverId}`).then(r => r.data)

export const updateServer = (serverId, name, isPublic) =>
  api.patch(`/servers/${serverId}`, { name, is_public: isPublic }).then(r => r.data)

export const leaveServer = (serverId) =>
  api.delete(`/servers/${serverId}/leave`).then(r => r.data)

export const regenerateInviteCode = (serverId) =>
  api.post(`/servers/${serverId}/regenerate-invite-code`).then(r => r.data)

export const getServerLeaderboard = (serverId) =>
  api.get(`/servers/${serverId}/leaderboard`).then(r => r.data)

// Server Join Requests
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


// ==========================================
// CHALLENGES
// ==========================================

// Request deduplication mechanism for server-specific feeds
const pendingRequests = new Map()

const dedupeGet = (url) => {
  if (pendingRequests.has(url)) {
    return pendingRequests.get(url)
  }

  const request = api
    .get(url)
    .then((r) => r.data)
    .finally(() => pendingRequests.delete(url))

  pendingRequests.set(url, request)
  return request
}

export const getChallengeFeed = () =>
  api.get('/challenges/feed').then(r => r.data)

export const getServerChallenges = (serverId, { page = 1, pageSize = 15, status = null } = {}) => {
  const url = `/servers/${serverId}/challenges?page=${page}&page_size=${pageSize}${status ? `&status=${status}` : ''}`
  return dedupeGet(url)
}

export const createChallenge = (serverId, payload) =>
  api.post(`/servers/${serverId}/challenges`, payload).then(r => r.data)

export const acceptChallenge = (serverId, challengeId, prediction) =>
  api.post(`/servers/${serverId}/challenges/${challengeId}/accept`, {
    prediction,
  }).then(r => r.data)

export const declineChallenge = (serverId, challengeId) =>
  api.post(`/servers/${serverId}/challenges/${challengeId}/decline`).then(r => r.data)


// ==========================================
// NOTIFICATIONS
// ==========================================

// export const markNotificationRead = (notificationId) =>
//   api.post(`/notifications/${notificationId}/mark-read`).then(r => r.data)

// export const markAllNotificationsRead = () =>
//   api.post('/notifications/mark-all-read').then(r => r.data)