# ReviewQR-AI

ReviewQR-AI helps businesses collect more Google reviews. Business owners
create a business profile and get a unique QR code. Customers scan the QR
code, receive a unique AI-generated review (via Google Gemini), copy it, and
manually post it to Google. **The app never auto-submits reviews or selects
star ratings — the customer is always in control.**

## Tech Stack

| Layer          | Technology                                  |
|----------------|----------------------------------------------|
| Frontend       | HTML5, CSS3, Vanilla JavaScript, Jinja2       |
| Backend        | Python, FastAPI                               |
| Database       | MongoDB (via Motor async driver)              |
| Auth           | JWT + passlib/bcrypt                          |
| AI             | Google Gemini API                             |
| QR Codes       | `qrcode` + Pillow                             |
| Configuration  | Pydantic Settings + python-dotenv             |

## Architecture

The backend follows a clean, layered architecture:

```
Router → Service → Repository → MongoDB
Router → Service → AI Module → Gemini API
```

- **Routers** (`app/routers/`) only handle HTTP request/response concerns.
- **Services** (`app/services/`) contain all business logic and validation.
- **Repositories** (`app/repositories/`) are the only layer that talks to MongoDB.
- **AI module** (`app/ai/`) is the only layer that talks to the Gemini API.
- **Utils** (`app/utils/`) hold small, reusable, stateless helpers.
- **Models** (`app/models/`) define the shape of MongoDB documents.
- **Schemas** (`app/schemas/`) define Pydantic request/response validation.

## Project Structure

```
reviewqr-ai/
├── app/
│   ├── main.py                  # FastAPI app, routers, static mount, lifespan
│   ├── config.py                # Pydantic Settings (.env loader)
│   ├── database.py              # MongoDB (Motor) connection + indexes
│   ├── dependencies.py          # Auth dependency + service factories
│   ├── routers/                 # HTTP endpoints (API + page routes)
│   │   ├── auth.py
│   │   ├── business.py
│   │   ├── qr.py
│   │   ├── customer.py
│   │   ├── settings.py
│   │   └── pages.py             # Server-rendered Jinja2 pages
│   ├── services/                # Business logic
│   │   ├── auth_service.py
│   │   ├── business_service.py
│   │   ├── qr_service.py
│   │   ├── customer_service.py
│   │   └── settings_service.py
│   ├── repositories/            # MongoDB data access
│   │   ├── user_repository.py
│   │   ├── business_repository.py
│   │   ├── qr_repository.py
│   │   └── review_repository.py
│   ├── models/                  # MongoDB document builders
│   │   ├── user.py
│   │   ├── business.py
│   │   ├── qr.py
│   │   └── review.py
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── auth_schema.py
│   │   ├── business_schema.py
│   │   ├── qr_schema.py
│   │   ├── settings_schema.py
│   │   └── review_schema.py
│   ├── ai/                      # Gemini integration
│   │   ├── gemini_client.py
│   │   ├── prompt_builder.py
│   │   └── review_generator.py
│   ├── utils/                   # Reusable helpers
│   │   ├── password_utils.py
│   │   ├── jwt_utils.py
│   │   ├── qr_generator.py
│   │   ├── validators.py
│   │   ├── logger.py
│   │   └── helper.py
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # CSS, JS, generated QR images, logos
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py
└── README.md
```

## Getting Started

1. **Clone and enter the project**
   ```bash
   cd reviewqr-ai
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate       # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and set at minimum:
   - `MONGO_URI` — your MongoDB connection string
   - `JWT_SECRET_KEY` — a long random secret
   - `GEMINI_API_KEY_1` (and optionally `GEMINI_API_KEY_2`, `_3`, ... for
     automatic failover) — your Google Gemini API key(s)

4. **Make sure MongoDB is running** (locally or a cloud instance such as
   MongoDB Atlas).

5. **Run the app**
   ```bash
   python run.py
   ```
   or
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open `https://aireview.movya.com` in your browser.

## Application Flow

**Business Owner:** Register → Login → Dashboard → Create Business
(QR auto-generated) → Display QR in-store → Manage/Edit/Delete businesses.

**Customer:** Scan QR → Land on business page → Generate AI review →
Copy review → Open Google Review page → Select stars → Paste review →
Submit manually.

## API Overview

| Method | Endpoint                              | Description                          |
|--------|----------------------------------------|---------------------------------------|
| POST   | `/api/auth/register`                  | Create a business-owner account       |
| POST   | `/api/auth/login`                     | Login, receive JWT (cookie + body)    |
| POST   | `/api/auth/logout`                    | Clear session cookie                  |
| GET    | `/api/auth/me`                        | Current logged-in user                |
| POST   | `/api/business`                       | Create a business (auto-generates QR) |
| GET    | `/api/business`                       | List the owner's businesses           |
| GET    | `/api/business/{id}`                  | Get one business                      |
| PUT    | `/api/business/{id}`                  | Update a business                     |
| DELETE | `/api/business/{id}`                  | Delete a business (+ its QR)          |
| GET    | `/api/qr/{business_id}`               | QR metadata                           |
| GET    | `/api/qr/{business_id}/download`      | Download QR image                     |
| POST   | `/api/qr/{business_id}/regenerate`    | Regenerate the QR code                |
| GET    | `/api/customer/{slug}`                | Public business info for customers    |
| POST   | `/api/customer/{slug}/generate-review`| Generate a unique AI review           |
| PUT    | `/api/settings/profile`               | Update profile                        |
| PUT    | `/api/settings/password`              | Change password                       |

Interactive API docs are available at `/docs` (Swagger UI) once the app is running.

## Design Principles

- Clean Architecture with strict separation of concerns.
- No duplicate logic — shared helpers live in `utils/`.
- Routers stay thin; all logic lives in services.
- Only repositories touch MongoDB; only the AI module touches Gemini.
- Configuration is always loaded from `.env`, never hardcoded.
- The app **never** auto-submits reviews or selects star ratings on the
  customer's behalf — every review is copied and submitted manually.

## Future Modules (Not Yet Implemented)

- Analytics dashboard
- Multi-language AI reviews
- Email notifications
- QR code customization (colors/logo overlay)
- Full review history UI
- Business branding options
- Admin panel
