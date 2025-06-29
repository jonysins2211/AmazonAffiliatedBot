# Amazon Affiliate Bot Dashboard

A modern, real-time dashboard for managing Amazon affiliate deals, users, and statistics. Built with Python (backend) and JavaScript (frontend), featuring a cyber-themed UI and live data updates.

---

## Features
- Real-time statistics and charts (deals, clicks, earnings, conversion rate)
- Recent deals table with status and metrics
- User management (CRUD-ready)
- Responsive cyber-themed UI
- Notification system
- Secure environment variable handling

---

## Prerequisites
- Python 3.10+
- Node.js (for frontend development, optional)
- PostgreSQL (or your configured database)
- Git

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd AmazonAFBot
```

### 2. Python Environment
Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```
Or, if using `pyproject.toml`:
```bash
pip install .
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_NAME=yourdb
SECRET_KEY=your_secret_key
# Add other required variables as needed
```
**Important:** Add `.env` to `.gitignore` to keep secrets safe:
```bash
echo ".env" >> .gitignore
```

### 5. Database Setup
- Ensure your database is running and accessible.
- Run any provided migrations or create tables as needed (see `database.py`).

### 6. Run the Backend
```bash
python web_dashboard_clean.py
```
- The dashboard will be available at `http://localhost:8000` (or your configured port).

### 7. Frontend (Static Files)
- All static assets are in `static/` and templates in `templates/`.
- No build step is required unless you modify or add frontend tooling.

---

## Usage
- Open your browser and go to `http://localhost:8000`.
- View real-time stats, deals, and charts.
- Manage users and deals (CRUD endpoints available; UI for full CRUD coming soon).
- The dashboard auto-refreshes every 30 seconds.

---

## User Management (CRUD)
- Backend endpoints for user CRUD are available at `/api/users` (see `web_dashboard_clean.py`).
- Frontend UI for full user management is planned; currently, you can list users.
- For API usage, use tools like `curl` or Postman:
    - List users: `GET /api/users`
    - Add user: `POST /api/users`
    - Update user: `PUT /api/users/<id>`
    - Delete user: `DELETE /api/users/<id>`

---

## Development
- Edit backend logic in Python files (e.g., `web_dashboard_clean.py`, `database.py`).
- Edit frontend logic in `static/js/dashboard.js` and templates in `templates/`.
- For live reload, restart the backend after code changes.

---

## Security
- Never commit your `.env` file or secrets.
- Use strong, unique secrets for production.
- Restrict API endpoints as needed (authentication/authorization recommended).

---

## Troubleshooting
- **.env parsing error:** Remove any trailing backslashes or invalid characters.
- **HTTP 304 responses:** These are normal and indicate browser caching.
- **Stats API error:** Ensure all stats values are valid numbers in the backend.
- **Database errors:** Check your connection settings and database status.

---

## License
See [LICENSE](LICENSE).

---

## Credits
- Dashboard UI: RafalW3bCraft
- Chart.js for charts
- Flask/FastAPI/Starlette (depending on backend)

---

## Contributing
Pull requests and suggestions are welcome!
