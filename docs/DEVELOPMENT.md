# Development Guide

This guide covers the development workflow for both backend and frontend.

## Before You Start

1. Clone the repository
2. Set up environment variables (see [SETUP.md](./SETUP.md))
3. Choose either Docker or local development setup
4. Ensure you have the prerequisites installed

## Project Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed project structure.

## Backend Development

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

### Running Services

Start PostgreSQL and Redis (via Docker or locally):

```bash
# Via Docker (optional, if not using full docker-compose)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16
docker run -d -p 6379:6379 redis:latest
```

Then start the FastAPI server:

```bash
# Terminal 1: API Server
uvicorn app.v1.main:app --reload

# Terminal 2: Celery Worker
celery -A app.v1.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery Beat Scheduler
celery -A app.v1.tasks.celery_app beat --loglevel=info
```

### Code Organization

- **routes/** — API endpoint handlers (one file per resource)
- **schemas/** — Pydantic request/response models
- **models/** — SQLAlchemy database models
- **services/** — Business logic (separated from routes)
- **core/** — Configuration, security, exceptions
- **db/** — Database session management
- **tasks/** — Celery task definitions

### Adding a New Route

1. Create a new file in `app/v1/api/routes/` (e.g., `my_feature.py`)
2. Define route handlers:

```python
from fastapi import APIRouter, Depends
from app.v1.schemas import MySchema
from app.v1.services import my_service

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.get("/")
async def list_items(
    page: int = 1,
    page_size: int = 20,
    db = Depends(get_db)
):
    items = await my_service.list_items(db, page, page_size)
    return items

@router.post("/")
async def create_item(
    data: MySchema,
    db = Depends(get_db)
):
    item = await my_service.create_item(db, data)
    return item
```

3. Register router in `app/v1/main.py`:

```python
from app.v1.api.routes import my_feature

app.include_router(my_feature.router, prefix="/api/v1")
```

### Adding a New Service

1. Create `app/v1/services/my_service.py`:

```python
from app.v1.models import models
from sqlalchemy.ext.asyncio import AsyncSession

async def list_items(db: AsyncSession, page: int, page_size: int):
    query = select(models.MyModel)
    result = await db.execute(query.offset((page-1)*page_size).limit(page_size))
    return result.scalars().all()

async def create_item(db: AsyncSession, data):
    item = models.MyModel(**data.dict())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
```

2. Import and use in routes

### Adding a New Model

1. Add to `app/v1/models/models.py`:

```python
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. Create database migration:

```bash
alembic revision --autogenerate -m "Add MyModel table"
alembic upgrade head
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/v1/test_unit_alerts.py

# Specific test function
pytest tests/v1/test_unit_alerts.py::test_alert_window_logic

# With coverage
pytest --cov=app tests/

# With verbose output
pytest -v tests/

# Watch mode (requires pytest-watch)
ptw tests/
```

### Testing Best Practices

- **Unit Tests** — Test services in isolation (mock database)
- **Integration Tests** — Test routes with real database (fixtures in conftest.py)
- **Fixtures** — Reusable test data in `tests/conftest.py`
- **Mocking** — Use `unittest.mock` for external APIs
- **Assertions** — Clear, specific assertions

Example test:

```python
import pytest
from app.v1.services import user_service

@pytest.mark.asyncio
async def test_create_user(db, user_service):
    data = UserCreate(email="test@example.com", password="secure")
    user = await user_service.create_user(db, data)
    
    assert user.email == "test@example.com"
    assert user.id is not None
```

### Database Migrations

```bash
# Create new migration (auto-generates from model changes)
alembic revision --autogenerate -m "Add email column to users"

# View migration file: alembic/versions/xxx.py
# Edit if needed, then apply:

alembic upgrade head  # Apply latest migration
alembic upgrade +1    # Apply next migration
alembic downgrade -1  # Revert last migration
alembic current       # Show current revision
alembic history       # Show all revisions

# Create migration without auto-generation
alembic revision -m "Manual migration"
```

### Debugging

#### Debug with Print Statements

```python
# In route or service
print(f"DEBUG: value={value}")  # Will appear in terminal
```

#### Debug with Logging

```python
from app.v1.core.logger import logger

logger.debug(f"Debug info: {value}")
logger.info(f"Information: {value}")
logger.warning(f"Warning: {value}")
logger.error(f"Error: {value}")
```

#### Debug with Debugger

```python
# In route
import pdb; pdb.set_trace()  # Breakpoint

# Or use IDE debugger (VS Code, PyCharm)
# Set breakpoint, run with debugger
```

### Code Style

Maintain consistency with:

- **Black** — Code formatter (auto)
  ```bash
  black app/
  ```
- **Isort** — Import sorting
  ```bash
  isort app/
  ```
- **Flake8** — Linting
  ```bash
  flake8 app/
  ```
- **Pylint** — Code analysis
  ```bash
  pylint app/
  ```

### Common Patterns

#### Async Database Query

```python
from sqlalchemy import select
from app.v1.models import models

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()
```

#### Pagination Response

```python
async def list_items(db, page: int, page_size: int):
    # Get total count
    count_query = select(func.count()).select_from(models.MyModel)
    total = await db.scalar(count_query)
    
    # Get paginated items
    query = select(models.MyModel).offset((page-1)*page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
```

#### Error Handling

```python
from app.v1.core.exceptions import NotFoundError, ValidationError

async def get_subscription(db, sub_id: int, user_id: int):
    sub = await db.get(models.Subscription, sub_id)
    if not sub:
        raise NotFoundError("Subscription not found")
    if sub.user_id != user_id:
        raise ValidationError("Not authorized")
    return sub
```

---

## Frontend Development

### Setup

```bash
cd frontend/v1

# Install dependencies
npm install

# Start development server
npm run dev
```

Development server runs at http://localhost:5173

### Project Structure

- **api/** — API client utilities
- **components/** — Reusable components
- **context/** — React Context providers
- **pages/** — Full-page components (one per route)
- **styles/** — CSS modules

### Adding a New Page

1. Create `src/pages/MyPage.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyData } from '../api/client';
import styles from '../styles/MyPage.module.css';

export default function MyPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getMyData();
        setData(result);
      } catch (error) {
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [navigate]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className={styles.container}>
      <h1>My Page</h1>
      {data && <div>{/* Render data */}</div>}
    </div>
  );
}
```

2. Add route in `src/App.jsx`:

```jsx
import MyPage from './pages/MyPage';

function App() {
  return (
    <Routes>
      <Route path="/my-page" element={<MyPage />} />
    </Routes>
  );
}
```

### Adding a New Component

1. Create `src/components/MyComponent.jsx`:

```jsx
import styles from '../styles/MyComponent.module.css';

export default function MyComponent({ title, children }) {
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>{title}</h2>
      <div className={styles.content}>{children}</div>
    </div>
  );
}
```

2. Create corresponding CSS module `src/styles/MyComponent.module.css`:

```css
.container {
  padding: 1rem;
  border-radius: 8px;
  background: #f5f5f5;
}

.title {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #333;
}

.content {
  color: #666;
}
```

3. Use in pages or other components:

```jsx
import MyComponent from '../components/MyComponent';

<MyComponent title="Example">
  <p>Content here</p>
</MyComponent>
```

### Using React Router

```jsx
import { useNavigate, useParams, useLocation } from 'react-router-dom';

export default function MyPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { pathname } = useLocation();

  const handleClick = () => {
    navigate(`/teams/${id}`, { state: { from: pathname } });
  };

  return <button onClick={handleClick}>Go to Team</button>;
}
```

### Using Context

Create context:

```jsx
// context/MyContext.jsx
import { createContext, useState } from 'react';

export const MyContext = createContext();

export function MyProvider({ children }) {
  const [value, setValue] = useState('initial');

  return (
    <MyContext.Provider value={{ value, setValue }}>
      {children}
    </MyContext.Provider>
  );
}
```

Use context:

```jsx
import { useContext } from 'react';
import { MyContext } from '../context/MyContext';

export default function MyComponent() {
  const { value, setValue } = useContext(MyContext);

  return (
    <div>
      <p>{value}</p>
      <button onClick={() => setValue('new value')}>Update</button>
    </div>
  );
}
```

### Making API Calls

```jsx
import { useState, useEffect } from 'react';
import { getMatches } from '../api/client';

export default function Matches() {
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const data = await getMatches();
        setMatches(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchMatches();
  }, []);

  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {matches.map(match => (
        <div key={match.id}>{match.home_team} vs {match.away_team}</div>
      ))}
    </div>
  );
}
```

### Styling

Use CSS Modules for component styling:

```jsx
import styles from './MyComponent.module.css';

// Conditional styling
<div className={`${styles.base} ${isActive ? styles.active : ''}`}>
  Content
</div>

// Global classes
<div className={styles.container + ' some-global-class'}>
  Content
</div>
```

### Code Splitting and Lazy Loading

```jsx
import { lazy, Suspense } from 'react';

const MyComponent = lazy(() => import('./MyComponent'));

export default function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <MyComponent />
    </Suspense>
  );
}
```

### Performance Optimization

Use `useMemo` and `useCallback` for expensive operations:

```jsx
import { useMemo, useCallback } from 'react';

export default function Matches({ matches }) {
  // Memoize sorted list
  const sortedMatches = useMemo(() => {
    return [...matches].sort((a, b) => 
      new Date(a.kickoff_at) - new Date(b.kickoff_at)
    );
  }, [matches]);

  // Memoize callback
  const handleClick = useCallback((id) => {
    // Handle click
  }, []);

  return (
    <div>
      {sortedMatches.map(m => (
        <MatchCard key={m.id} match={m} onClick={handleClick} />
      ))}
    </div>
  );
}
```

### Building for Production

```bash
npm run build
```

Outputs optimized bundle to `dist/` directory. Files are minified and code-split for better performance.

### Testing Frontend

```bash
# With Vitest (configured in vite.config.js)
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

## Workflow

### Feature Development

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes, commit frequently:
   ```bash
   git add .
   git commit -m "Add specific feature"
   ```

3. Test locally (both backend and frontend)

4. Push branch and create Pull Request:
   ```bash
   git push origin feature/my-feature
   ```

5. After approval, merge to main:
   ```bash
   git merge feature/my-feature
   git push origin main
   ```

### Code Review Checklist

- [ ] Code follows project style guide
- [ ] Tests are included and passing
- [ ] No hardcoded values or secrets
- [ ] Database migrations created (if needed)
- [ ] API documentation updated (if endpoints changed)
- [ ] Error handling implemented
- [ ] Comments added for complex logic

### Git Commit Messages

Use clear, descriptive commit messages:

```
feat: Add email verification endpoint
fix: Resolve pagination bug in subscriptions list
docs: Update API documentation
refactor: Extract common validation logic
test: Add tests for alert window calculation
```

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Check virtual environment
source venv/bin/activate

# Check dependencies
pip install -r requirements.txt

# Check database connection
alembic current
```

### Frontend won't build

```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Rebuild
npm run build
```

### Database sync issues

```bash
# Check Celery worker logs
# Check that Redis is running
redis-cli ping  # Should return PONG

# Manually trigger sync
curl -X POST http://localhost:8000/api/v1/admin/sync-matches \
  -H "x-admin-key: your-admin-key"
```

### API authentication issues

```bash
# Check token is being sent
# Look at network tab in browser DevTools
# Verify Authorization header is present

# Check backend logs for token validation errors
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org)
- [Celery Documentation](https://docs.celeryq.dev)
- [Vite Documentation](https://vitejs.dev)
