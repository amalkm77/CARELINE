# CARELINE Hospital Feedback System

## Technology stack

- **Front end:** HTML, CSS, and JavaScript
- **Back end:** Python with Flask REST API routes
- **Database:** SQLite, stored in `backend/careline.db`
- **Sentiment analysis:** VADER analyzes patient comments as positive, neutral, or negative
- **Charts:** Chart.js shows service rating averages and comment sentiment in the admin dashboard
- **Development tools:** VS Code for editing, Postman for API testing, and GitHub for source control

React, Django, Node.js, MySQL, MongoDB, and external NLP APIs are optional alternatives and are not required by this implementation.

## Run the application

1. Install Python 3.10 or newer.
2. From the project folder, install the dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Double-click `start_careline.bat`, or run `backend\app.py` with the `.venv` Python interpreter.
4. The site opens at <http://127.0.0.1:5000/>.

Flask serves the homepage, feedback form, static frontend files, images, and API from the same address. SQLite tables and compatible schema updates are created when the backend starts.

Patient comments are classified with VADER when feedback is submitted. The admin dashboard analyzes comments when records load and displays summary statistics, department and sentiment charts, rating distribution, feedback trends, and searchable and filterable records. Demo records are visibly marked as fictional sample data.

## Add fictional demo feedback

To populate a development database with 80 fictional feedback records, run:

```powershell
.\.venv\Scripts\python.exe backend\seed_demo_feedback.py
```

The seed script is safe to rerun: it adds records only when no demo records are
already present. Each seeded record is marked as demo data in the admin
dashboard. These examples are fictional and must not be presented as genuine
patient feedback.

## API testing with Postman

Import `CARELINE.postman_collection.json` into Postman. Set the `baseUrl`, `adminEmail`, and `adminPassword` collection variables, then run **Sign Up Admin** once and use **Log In Admin** before protected requests. Postman keeps the login session cookie for subsequent requests.

The collection includes signup, login, session, feedback submission/listing/deletion, and logout requests.

## Version control with GitHub

Open the project folder in VS Code and use its Source Control panel to initialize a Git repository, commit project changes, and publish the repository to GitHub. Do not commit credentials or production secrets.
