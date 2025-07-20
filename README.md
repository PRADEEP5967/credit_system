# Credit Approval System

## Running the System

1. **Build and start all services:**
   ```
   docker compose up --build
   ```
   This will start Django, PostgreSQL, and Redis.

2. **Apply migrations and create a superuser (in a new terminal):**
   ```
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

3. **Start the Celery worker (in a new terminal):**
   ```
   docker compose exec web celery -A credit_system worker --loglevel=info
   ```

4. **Place your Excel files** (`customer_data.xlsx` and `loan_data.xlsx`) in the `/app` directory inside the container (or in the project root before building).

5. **Trigger the ingestion task from Django shell:**
   ```
   docker compose exec web python manage.py shell
   >>> from core.tasks import ingest_customer_and_loan_data
   >>> ingest_customer_and_loan_data.delay('/app/customer_data.xlsx', '/app/loan_data.xlsx')
   ```

## Notes
- The ingestion will run in the background and populate the database.
- You can monitor the Celery worker logs for progress/errors. 

## API Modern Logic & Features Summary

| Feature                        | Modern/Best Practice | Notes                                      |
|--------------------------------|---------------------|--------------------------------------------|
| DRF ViewSets & APIViews         | Yes                 | Clean separation of CRUD and custom logic  |
| Credit Score Logic              | Yes                 | Weighted, extensible, policy-driven        |
| Tiered Approval/Interest Logic  | Yes                 | Flexible, business-friendly                |
| EMI Calculation                 | Yes                 | Standard financial formula                 |
| Error Handling                  | Yes                 | User-friendly, clear reasons               |
| Celery Integration              | Yes                 | For background tasks                       |
| Static File Handling            | Yes                 | (recently fixed)                           |
| Permissions/Auth                | No                  | Should be added for production             |
| Pagination/Filtering            | No                  | Add for scalability                        | 

## API Features Overview

Your API now includes the following modern features:

- **Authentication & Permissions:** All endpoints require authentication by default (`IsAuthenticated`).
- **Pagination:** All list endpoints are paginated (10 items per page by default). Use `?page=2` for additional pages.
- **Filtering:** Filter results by query parameters. Example: `/api/customers/?age=30&monthly_salary=50000`
- **Searching:** Search by fields using the `search` parameter. Example: `/api/customers/?search=John`
- **Ordering:** Order results by fields. Example: `/api/customers/?ordering=age` or `/api/customers/?ordering=-monthly_salary`
- **Throttling:** User rate limit set to 1000 requests per day.
- **API Documentation:** Interactive docs available at `/swagger/` (Swagger UI) and `/redoc/` (Redoc).

### Example Usage

- **Filter customers by age and salary:**
  `/api/customers/?age=30&monthly_salary=50000`
- **Search customers by name:**
  `/api/customers/?search=John`
- **Order customers by salary descending:**
  `/api/customers/?ordering=-monthly_salary`
- **Paginate results:**
  `/api/customers/?page=2`

See the API documentation endpoints for more details and to try out these features interactively. 


If you want to test admin features:
Log in as an admin user and try the endpoints under /api/v1/admin/.

## Getting Started

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd credit_system
```

### 2. Build and start all services
```sh
docker-compose up --build
```

### 3. Apply migrations and create a superuser
```sh
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 4. Access the application
- Home: [http://localhost:8000/](http://localhost:8000/)
- Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- API root: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
- Swagger docs: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- Redoc docs: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
- Registration UI: [http://localhost:8000/register-ui/](http://localhost:8000/register-ui/)


## API Usage

- All endpoints are listed at `/api/v1/`.
- Use Swagger or Redoc for interactive API documentation and testing.
- Most endpoints require authentication (register and login to get a token).
- Example endpoints:
  - `POST /api/v1/register/` — Register a new user
  - `POST /api/v1/login/` — Obtain an auth token
  - `GET /api/v1/profile/` — Get user profile (token required)
  - `POST /api/v1/check-eligibility` — Check loan eligibility (token required)
  - `POST /api/v1/create-loan` — Create a loan (token required)
  - Admin endpoints: `/api/v1/admin/users/`, `/api/v1/admin/dashboard/`, etc. (admin token required)

### Example: Register a User
```json
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "strongpassword123",
  "phone_number": "+12345678901",
  "first_name": "Test",
  "last_name": "User"
}
```

### Example: Check Eligibility (with token)
```json
{
  "customer_id": 1,
  "loan_amount": 10000,
  "interest_rate": 12,
  "tenure": 12
}
```

## Features
- User registration, login, and profile
- Admin dashboard and user management
- Customer, loan, transaction, and credit application management
- Filtering, searching, pagination, and rate limiting
- API versioning and documentation
- Logging and monitoring
- Simple backend UI for registration

## Sample UI Screenshot
![Registration UI](images/register_ui_sample.png)

> _Replace the above image with an actual screenshot of your UI. Place the image in a folder named `images` in your repo._

## Project Screenshots

### Docker Desktop - Running Containers
![Docker Desktop Screenshot](images/docker_desktop_screenshot.png)

> _To add more screenshots, place your images in the `images` folder and reference them here using markdown: ![Description](images/your_image.png)_

If you want to add more specific images or need help with image formatting, let me know!