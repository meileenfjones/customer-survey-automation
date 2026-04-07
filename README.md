# Customer Survey Automation

__Background__  
Automates the process of sending customer data to a survey vendor to gather feedback and insights for product and operational improvements on a recurring schedule.

__Deliverables__  
A Python script that prepares data and securely transfers it via SFTP, scheduled to run automatically at specified intervals, ensuring timely and accurate survey distribution.

## Prerequisites

List all items needed for the program to work

- Windows OS
- Task Scheduler
- KeePass database
  - SQL database credentials stored securely
  - SFTP credentials in format:
    - title = customers
    - username = username
    - password = password
    - url = host
    - in Additional attributes
      - add hoskey and remote_directory
- Python (3.11.3)
  - Pandas (>=2.0.0)
  - PyKeePass (>=4.0.3)
  - prefect (>=2.10.3)
  - SQLAlchemy (>=2.0.8)
  - psycopg2 (>=2.9.6)
  - openpyxl (>=3.1.2)
  - requests (>=2.28.2)
  - lxml (>=4.9.2)
  - paramiko (>=3.2.0)


### Setup

1. Download most recent python on C drive [latest version for Windows](https://www.python.org/downloads/)
2. Download the [latest release] and unzip.
3. Open a Windows Command Prompt Terminal
4. Change directory to the script folder
  ```
  cd project_directory
  ```
5. Create virtual environment
  ```
  python -m venv venv
  ```
6. Activate the virtual environment
  ```
  venv\Scripts\activate.bat
  ```

7. Install Python packages
  ```
  pip install -r requirements.txt
  ```

8. Create config.py and fill out with following paths
```
from pathlib import Path

# specified keepass file and key path for this project
KDBX_FILE = ...
KEY_PATH = ...

FILE_OUTPUT_DIRECTORY = Path(...)
```
9. Create/verify log
10. To automate project, create task with Windows Task Scheduler directed at the bat file


### Files

List important files to know about and how they work together

`config.py`
- Contains paths for KeePass file, key path, and end file directory

`analytics_platform_connection.py`
- Given kdbx file access, pulls credentials to create, test, and kill the database connection

`'sftp_connection.py'`
- Given kdbx file access with known_hosts.txt in attachments, pulls credentials and sends exported file via SFTP

`'Customers-Survey-Automation.py'`
- Creates connection, query database, save data in an Excel file, and uploads using sftp_connection function
- will log automation status in SQL database (customers_automation_log table) if connection occurs


### Methodology

List out steps of how the program works

1. uses PyKeePass to connect to kdbx database for database and SFTP credentials
2. Connect to SQL database
3. if there is no missing daily data, queries for customers data and saves to Excel file in appropriate directory
4. uses paramiko to upload file via SFTP
5. Uploads log to database and closes connection (will also log and close if any error occurs in script)

