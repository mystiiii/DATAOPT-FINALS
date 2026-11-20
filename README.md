# AdventureWorks analytics and reporting system

Course: DATAOPT | Team: Group 2 (BTIS1)
Role: Data optimization consultants
Stack: Django 5.x, SQL Server (AdventureWorks2019 via SSMS), HTML5, Tailwind, Chart.js

## Windows setup (SSMS + local SQL Server)

### 1. Prerequisites
- Python 3.10 or higher (check **Add Python to PATH** during installation)
- Microsoft SQL Server (Developer or Express Edition) and **SQL Server Management Studio (SSMS)**
- **Microsoft ODBC Driver 18 for SQL Server (x64)** (or Driver 17):
  Download and install from Microsoft Learn (`ODBC Driver for SQL Server`).

### 2. Restore `AdventureWorks2019` in SSMS
1. Open **SSMS** and connect to your local SQL Server instance.
   - Note the **Server name** shown in the Connect dialog (usually `localhost`, `.`, or `localhost\SQLEXPRESS` / `YOURPC\SQLEXPRESS`).
   - Note the **Authentication** mode you use (`Windows Authentication` or `SQL Server Authentication`).
2. In **Object Explorer**, right-click **Databases** and select **Restore Database...**.
3. Under **Source**, choose **Device** -> click `...` -> **Add** -> select `AdventureWorks2019.bak`.
4. Click **OK** to restore, then confirm `AdventureWorks2019` appears under **Databases**.

### 3. Virtual environment and dependencies
Open PowerShell in the project folder:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and retry (or use `.\.venv\Scripts\activate.bat` in Command Prompt).

### 4. Configure `.env`
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Update `.env` to match how you connect in SSMS:

**Option A: Windows Authentication (SSMS default — no username/password)**
```env
DB_HOST=localhost
DB_PORT=
DB_NAME=AdventureWorks2019
DB_TRUSTED_CONNECTION=yes
DB_USER=
DB_PASSWORD=
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_CERT=yes
```

**Option B: SQL Server Authentication (`sa` or custom SQL login)**
```env
DB_HOST=localhost
DB_PORT=
DB_NAME=AdventureWorks2019
DB_TRUSTED_CONNECTION=no
DB_USER=sa
DB_PASSWORD=YourSqlServerPassword
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_CERT=yes
```

Notes for `.env`:
- If SSMS connects to SQL Server Express (e.g. `YOURPC\SQLEXPRESS`), set `DB_HOST=localhost\SQLEXPRESS` and leave `DB_PORT=` empty.
- If you only have ODBC Driver 17 installed, set `DB_DRIVER=ODBC Driver 17 for SQL Server`.

### 5. Database setup and initial seed
Run migrations for the local SQLite database (used for authentication, RBAC, and logs):
```powershell
python manage.py migrate
```

Seed the default roles and demo accounts:
```powershell
python manage.py setup_roles
```

Default demo accounts:
| Role | Username | Password | Access scope |
| :--- | :--- | :--- | :--- |
| Administrator | `admin` | `Admin123!` | Full admin and governance |
| Manager | `manager` | `Manager123!` | All four reporting modules and preset management |
| Supervisor | `supervisor` | `Supervisor123!` | Sales and customer profile modules |
| Employee | `employee` | `Employee123!` | Assigned reporting modules |

### 6. Start the development server
```powershell
python manage.py runserver
```
Open http://127.0.0.1:8000 in your browser.

### Troubleshooting Windows SQL Server connections
- **Connection error with `localhost\SQLEXPRESS` or `localhost`**: Open **SQL Server Configuration Manager** -> **SQL Server Network Configuration** -> **Protocols for MSSQLSERVER** (or **SQLEXPRESS**) -> enable **TCP/IP**, then restart the SQL Server service (and ensure **SQL Server Browser** is running for named instances).
- **Driver not found (`IM002`)**: Confirm `Microsoft ODBC Driver 18 for SQL Server` (x64) is installed, or change `DB_DRIVER` in `.env` to `ODBC Driver 17 for SQL Server`.
- **Login failed for `sa`**: Verify Mixed Mode authentication is enabled in SSMS (Server Properties -> Security -> **SQL Server and Windows Authentication mode**), or switch to Windows Authentication (`DB_TRUSTED_CONNECTION=yes`).

---

## macOS / Linux (Docker SQL Server)
If running SQL Server in Docker on macOS/Linux:
1. Install the ODBC driver (`brew install unixodbc msodbcsql18` on macOS) or `pymssql`.
2. Create a venv (`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`).
3. In `.env`, set `DB_HOST=localhost`, `DB_PORT=1434`, `DB_TRUSTED_CONNECTION=no`, `DB_USER=sa`, and `DB_PASSWORD=<your container password>`.
