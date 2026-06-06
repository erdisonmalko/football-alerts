# API Reference

All API endpoints are prefixed with `/api/v1`.

## Authentication Endpoints

### Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response** (201 Created)
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response** (200 OK)
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "message": "Logged out successfully"
}
```

### Get Current User

```http
GET /auth/me
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Google OAuth - Start Flow

```http
GET /auth/google/connect
```

Redirects to Google consent screen.

### Google OAuth - Callback (handled automatically)

```http
GET /auth/google/callback?code={code}&state={state}
```

Handles redirect from Google, stores token, and redirects to frontend.

---

## User Endpoints

### Get User Profile

```http
GET /users/me
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

### Update User Profile

```http
PATCH /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "newemail@example.com"
}
```

**Response** (200 OK)
```json
{
  "id": "uuid",
  "email": "newemail@example.com",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

### Delete Account

```http
DELETE /users/me
Authorization: Bearer {token}
```

**Response** (204 No Content)

---

## Subscription Endpoints

### Get User's Subscriptions

```http
GET /users/me/subscriptions?page=1&page_size=20
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "subscription_type": "league",
      "league_code": "PL",
      "team_id": null,
      "match_id": null,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Create Subscription

```http
POST /users/me/subscriptions
Authorization: Bearer {token}
Content-Type: application/json

{
  "subscription_type": "league",
  "league_code": "PL",
  "team_id": null,
  "match_id": null
}
```

**Response** (201 Created)
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "subscription_type": "league",
  "league_code": "PL",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Delete Subscription

```http
DELETE /users/me/subscriptions/{id}
Authorization: Bearer {token}
```

**Response** (204 No Content)

### Get User's Personalised Match Feed

```http
GET /users/me/matches?page=1&page_size=20&status=upcoming
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20)
- `status` — Filter by status: `upcoming`, `live`, `finished` (optional)

**Response** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "home_team": "Manchester United",
      "away_team": "Liverpool",
      "kickoff_at": "2024-01-15T15:00:00Z",
      "status": "SCHEDULED",
      "home_score": null,
      "away_score": null,
      "league_code": "PL",
      "subscribed": true
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

## Football Data Endpoints

### Get Supported Leagues

```http
GET /football/leagues
```

**Response** (200 OK)
```json
[
  {
    "code": "PL",
    "name": "Premier League",
    "country": "England"
  },
  {
    "code": "PD",
    "name": "La Liga",
    "country": "Spain"
  }
]
```

### Get Teams in a League

```http
GET /football/leagues/{code}/teams
```

**Example:** `GET /football/leagues/PL/teams`

**Response** (200 OK)
```json
[
  {
    "id": 1,
    "name": "Manchester United",
    "short_name": "Man United",
    "crest_url": "https://..."
  },
  {
    "id": 2,
    "name": "Liverpool",
    "short_name": "Liverpool",
    "crest_url": "https://..."
  }
]
```

### Get Upcoming Matches

```http
GET /football/matches/upcoming?page=1&page_size=20
```

**Response** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "home_team": "Manchester United",
      "away_team": "Liverpool",
      "kickoff_at": "2024-01-15T15:00:00Z",
      "status": "SCHEDULED",
      "league_code": "PL"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## Google Calendar Endpoints

### Check Calendar Connection Status

```http
GET /auth/google/status
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "connected": true,
  "email": "user@gmail.com"
}
```

### Disconnect Google Calendar

```http
DELETE /auth/google/disconnect
Authorization: Bearer {token}
```

**Response** (204 No Content)

### Add Match to Calendar

```http
POST /calendar/matches/add-match/{match_id}
Authorization: Bearer {token}
```

**Response** (201 Created)
```json
{
  "calendar_event_id": "event-id",
  "match_id": "match-id",
  "calendar_url": "https://..."
}
```

### Remove Match from Calendar

```http
DELETE /calendar/matches/remove-match/{match_id}
Authorization: Bearer {token}
```

**Response** (204 No Content)

---

## Challenge Endpoints

### Get Challenges

```http
GET /challenges?page=1&page_size=20
Authorization: Bearer {token}
```

**Response** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Week 10 Predictions",
      "created_by": "user-id",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "entries_count": 5
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Create Challenge

```http
POST /challenges
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Week 10 Predictions",
  "description": "Predict match outcomes for the week",
  "league_codes": ["PL"],
  "ends_at": "2024-01-21T23:59:59Z"
}
```

**Response** (201 Created)
```json
{
  "id": "uuid",
  "name": "Week 10 Predictions",
  "created_by": "user-id",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Submit Challenge Entry

```http
POST /challenges/{challenge_id}/entries
Authorization: Bearer {token}
Content-Type: application/json

{
  "predictions": [
    {
      "match_id": "match-1",
      "predicted_home_score": 2,
      "predicted_away_score": 1
    }
  ]
}
```

**Response** (201 Created)
```json
{
  "id": "uuid",
  "challenge_id": "challenge-id",
  "user_id": "user-id",
  "score": 0,
  "submitted_at": "2024-01-10T10:00:00Z"
}
```

---

## Admin Endpoints

All admin endpoints require `X-Admin-Key` header with the admin key.

```http
X-Admin-Key: your-admin-key
```

### Trigger Match Sync

```http
POST /admin/sync-matches
X-Admin-Key: {admin-key}
```

**Response** (200 OK)
```json
{
  "message": "Sync started",
  "task_id": "task-uuid"
}
```

### Trigger Alert Dispatch

```http
POST /admin/dispatch-alerts
X-Admin-Key: {admin-key}
```

**Response** (200 OK)
```json
{
  "message": "Alert dispatch started",
  "task_id": "task-uuid"
}
```

### Update Match Statuses

```http
POST /admin/update-match-statuses
X-Admin-Key: {admin-key}
```

**Response** (200 OK)
```json
{
  "message": "Status update started",
  "task_id": "task-uuid"
}
```

### Sync Google Calendars

```http
POST /admin/sync-calendars
X-Admin-Key: {admin-key}
```

**Response** (200 OK)
```json
{
  "message": "Calendar sync started",
  "task_id": "task-uuid"
}
```

### Get Upcoming Alerts Preview

```http
GET /admin/upcoming-alerts?hours=24
X-Admin-Key: {admin-key}
```

**Query Parameters:**
- `hours` — Preview alerts for next N hours (default: 24)

**Response** (200 OK)
```json
{
  "alerts": [
    {
      "user_email": "user@example.com",
      "match": "Manchester United vs Liverpool",
      "alert_type": "6_hours",
      "scheduled_for": "2024-01-15T14:00:00Z"
    }
  ],
  "total": 8
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid input: email format is incorrect"
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict

```json
{
  "detail": "Subscription already exists"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Interactive API Documentation

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`

Both endpoints provide interactive API exploration and testing.
