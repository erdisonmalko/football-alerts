# Frontend Overview

The frontend is a React 19 application built with Vite that provides a responsive web interface for managing football match subscriptions, viewing live scores, and integrating with Google Calendar.

## Features

- **Match Alerts** — Email notifications at 1 week, 3 days, and 6 hours before kickoff
- **Google Calendar Integration** — Add matches directly to Google Calendar with automatic reminders
- **Live Scores** — Match statuses and scores updated every 15 minutes during match days
- **Flexible Subscriptions** — Subscribe to entire leagues, specific teams, or individual matches
- **Personalised Dashboard** — View live, upcoming, and today's results for your subscriptions
- **Smart Filtering** — Filter matches by league on dashboard and subscriptions pages
- **User Profile** — Manage account settings, view statistics, and activity history
- **Challenge System** — Create and participate in prediction challenges with other users
- **Responsive Design** — Works seamlessly on desktop, tablet, and mobile devices

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | [React 19](https://react.dev/) |
| Build Tool | [Vite](https://vitejs.dev/) |
| Routing | [React Router](https://reactrouter.com/) |
| HTTP Client | [Axios](https://axios-http.com/) |
| Styling | CSS Modules |
| Deployment | Railway (managed Node.js) |

## Project Structure

```
frontend/v1/
├── src/
│   ├── App.jsx              # Root component
│   ├── main.jsx             # Entry point
│   ├── api/                 # API client utilities
│   │   └── client.js        # Axios instance + helper methods
│   ├── components/          # Reusable React components
│   │   ├── Dashboard.jsx
│   │   ├── MatchCard.jsx
│   │   ├── SubscriptionsList.jsx
│   │   ├── FilterChips.jsx
│   │   ├── Pagination.jsx
│   │   └── ...
│   ├── context/             # React Context providers
│   │   ├── AuthContext.jsx
│   │   ├── UserContext.jsx
│   │   └── ...
│   ├── pages/               # Page components (one per route)
│   │   ├── Home.jsx
│   │   ├── Dashboard.jsx
│   │   ├── SubscriptionsPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── UserProfile.jsx
│   │   ├── ChallengesPage.jsx
│   │   └── ...
│   ├── styles/              # Global CSS and modules
│   │   ├── index.css
│   │   ├── Dashboard.module.css
│   │   └── ...
│   └── public/              # Static assets
├── index.html               # HTML template
├── vite.config.js           # Vite configuration
├── package.json             # Dependencies
└── nginx.conf              # Nginx config for production
```

## Authentication Flow

1. User registers with email/password or logs in
2. Backend returns JWT token
3. Token stored in browser (localStorage or session storage)
4. Token included in `Authorization` header for protected requests
5. Logout clears token and redirects to home

### Google Calendar OAuth

1. User clicks "Connect Google Calendar"
2. Redirected to Google consent screen
3. After authorization, token stored in backend database
4. User can now add/remove matches from calendar
5. Logout disconnects calendar

## Key Pages

### Home
- Landing page with feature overview
- Quick links to login/register

### Dashboard
- View upcoming, live, and today's matches for subscriptions
- Filter by league
- Add/remove matches from calendar
- Real-time score updates

### Subscriptions
- View all user subscriptions (leagues, teams, matches)
- Add new subscriptions
- Remove existing subscriptions
- Paginated list view

### Match Browse
- Browse all upcoming matches
- Filter by league
- Subscribe to specific matches
- View team details

### User Profile
- View/edit account email
- Delete account
- View activity history
- View statistics

### Challenges
- View active challenges
- Create new challenge
- Submit predictions
- View leaderboard

### Login/Register
- Email and password authentication
- Form validation
- Error handling

## State Management

State is managed via React Context:

- **AuthContext** — User authentication state (token, user info)
- **UserContext** — User profile and settings
- **Subscription data** — Fetched on demand with pagination

For complex component state, `useState` hooks are used locally.

## API Integration

The frontend uses an Axios client (`api/client.js`) that:

- Manages base URL and default headers
- Automatically includes JWT token in requests
- Handles request/response interceptors
- Provides error handling and logging

Common API methods:

```javascript
// Auth
login(email, password)
register(email, password)
logout()

// Users
getUser()
updateUser(data)
deleteUser()

// Subscriptions
getSubscriptions(page, pageSize)
createSubscription(data)
deleteSubscription(id)

// Matches
getUpcomingMatches(page, pageSize)
getMyMatches(page, pageSize)

// Football Data
getLeagues()
getTeams(leagueCode)

// Google Calendar
checkCalendarStatus()
addMatchToCalendar(matchId)
removeMatchFromCalendar(matchId)
disconnectCalendar()

// Challenges
getChallenges(page, pageSize)
createChallenge(data)
submitChallengeEntry(challengeId, data)
```

## Styling Approach

The frontend uses **CSS Modules** for scoped styling:

- Each component has a `.module.css` file
- Global styles in `styles/index.css`
- No CSS framework (Tailwind, Bootstrap, etc.)
- Responsive design using CSS flexbox and grid
- Mobile-first approach

Example:

```jsx
// Dashboard.jsx
import styles from './Dashboard.module.css';

export default function Dashboard() {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Dashboard</h1>
    </div>
  );
}
```

## Components

### Reusable Components

- **MatchCard** — Displays single match with score, teams, time
- **SubscriptionsList** — Lists user subscriptions with delete option
- **FilterChips** — League filter selector
- **Pagination** — Page navigation for paginated lists
- **LoadingSpinner** — Loading state indicator
- **ErrorMessage** — Error message display
- **Modal** — Generic modal dialog
- **Button** — Styled button component

### Page Components

Each page is a full-screen view:

- **Home** — Marketing/landing page
- **Dashboard** — Main user hub showing subscriptions
- **Subscriptions** — Manage subscriptions
- **Matches** — Browse and filter all matches
- **UserProfile** — Account settings and stats
- **Challenges** — Create and join challenges
- **Login/Register** — Authentication pages

## Development Workflow

### Install Dependencies

```bash
cd frontend/v1
npm install
```

### Start Development Server

```bash
npm run dev
```

Server runs on http://localhost:5173 with hot module replacement.

### Build for Production

```bash
npm run build
```

Outputs optimized bundle to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Run Tests

```bash
npm test
```

## Deployment

The frontend is deployed on Railway:

1. Source code pushed to GitHub
2. Railway detects Node.js project
3. Runs `npm run build`
4. Serves from `dist/` with Nginx
5. Nginx configured to handle client-side routing

Environment variables:

- `VITE_API_URL` — Backend API base URL
- `VITE_FRONTEND_URL` — Frontend public URL (for redirects)

## Performance Optimizations

- **Code Splitting** — Vite automatically code-splits route components
- **Lazy Loading** — React Router lazy loads page components
- **Image Optimization** — Small images inlined, large images lazy-loaded
- **Caching** — API responses cached with appropriate TTL
- **Debouncing** — Search and filter inputs debounced

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Color contrast compliance
- Focus management

## Error Handling

- User-friendly error messages
- API error boundaries
- Retry logic for failed requests
- Graceful degradation

## Next Steps

See [SETUP.md](./SETUP.md) for detailed setup and development instructions.
