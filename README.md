# AdventureWorks analytics and reporting system

Course: DATAOPT | Team: Group 2 (BTIS1)
Role: Data optimization consultants
Stack: Django 5.x, SQL Server (AdventureWorks2019), HTML5, Tailwind, Chart.js

## Quick setup

### Prerequisites
- Python 3.10 or higher
- SQL Server: AdventureWorks2019 running locally or in Docker
- ODBC Driver for SQL Server:
  - macOS: `brew install unixodbc msodbcsql18`
  - Windows: install Microsoft ODBC Driver 18 for SQL Server (x64)

### Virtual environment and dependencies

macOS and Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env     # Mac/Linux
copy .env.example .env   # Windows
```

Update `.env` with your SQL Server connection details:
- Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`.
- Confirm `DB_DRIVER` matches your installed driver (`ODBC Driver 18 for SQL Server` or `ODBC Driver 17 for SQL Server`).

### Database setup and initial seed
Run migrations for the local SQLite database (used for authentication, RBAC, and logs):
```bash
python manage.py migrate
```

Seed the default roles and demo accounts:
```bash
python manage.py setup_roles
```

Default demo accounts:
| Role | Username | Password | Access scope |
| :--- | :--- | :--- | :--- |
| Administrator | `admin` | `Admin123!` | Full admin and governance |
| Manager | `manager` | `Manager123!` | All four reporting modules and preset management |
| Supervisor | `supervisor` | `Supervisor123!` | Sales and customer profile modules |
| Employee | `employee` | `Employee123!` | Assigned reporting modules |

### Start the development server
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000 in your browser.
