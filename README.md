# 🌍 Travel Helper

A comprehensive web application for planning, managing, and organizing your travel adventures. Track trips, manage budgets, discover attractions, create checklists, and document your journey with photos—all in one place.

![Python](https://img.shields.io/badge/Python-3.12.3%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.0%2B-green)
![SQLite](https://img.shields.io/badge/SQLite-Latest-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 🗺️ **Trip Management**
- Create and organize multiple trips with detailed information
- Set trip dates and budget limits
- Track trips by destination (city & country)
- View all your past and upcoming adventures

### 💰 **Budget Tracking**
- Monitor trip-specific budgets
- Track expenses across different categories
- Get visual overview of spending

### 🏛️ **Attractions & Places**
- Discover and save attractions in your destinations
- Browse places by city and country
- View detailed descriptions and ratings
- See attractions aggregated by location

### ✅ **Trip Checklists**
- Create and manage task checklists for each trip
- Track preparation and travel tasks
- Mark items as completed
- Stay organized before and during your journey

### 📸 **Photo Gallery**
- Upload and organize photos for trips, places, and attractions
- Store image metadata (size, dimensions, format)
- Visual documentation of your travels

### 👥 **User Management**
- Secure user authentication with JWT tokens
- User profiles with preferences
- Email notification settings
- Admin capabilities

### 🏷️ **Tagging System**
- Tag trips, places, and attractions for better organization
- Easy categorization and filtering

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SteppingCode/travel-helper.git
   cd travel-helper
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Initialize the database**
   
   The database will be automatically initialized when you start the application.

6. **Run the application**
   ```bash
   uvicorn app:app --reload
   ```

   The application will be available at `http://localhost:8000`

---

## 📁 Project Structure

```
travel-helper/
├── app.py                 # Main FastAPI application
├── auth.py               # Authentication & JWT handling
├── config.py             # Configuration management
├── models.py             # Pydantic data models
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
│
├── database/
│   ├── database.py       # SQLite database wrapper
│   └── sql/              # SQL schema files
│       ├── users.sql
│       ├── trips.sql
│       ├── places.sql
│       ├── attractions.sql
│       ├── checklists.sql
│       ├── budget.sql
│       ├── images.sql
│       └── images_links.sql
│
├── static/
│   ├── assets/           # Images, icons, etc.
│   ├── scripts/          # JavaScript files
│   │   ├── checklists.js
│   │   └── profile.js
│   └── styles/           # CSS stylesheets
│       ├── base.css
│       ├── index.css
│       ├── profile.css
│       └── [other styles]
│
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── profile.html
│   ├── trips.html
│   ├── trip_details.html
│   ├── places.html
│   ├── place_page.html
│   ├── budget.html
│   ├── checklists.html
│   └── create_*.html
│
└── uploads/              # User-uploaded images
```

---

## 🔧 Technology Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- **Database**: SQLite - Lightweight SQL database
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic models for data validation

### Frontend
- **Templates**: Jinja2 HTML templates
- **Styling**: CSS with responsive design
- **Interactivity**: Vanilla JavaScript

### Security
- Password hashing with bcrypt
- JWT-based authentication
- Secure token management
- CORS support

---

## 🔐 Authentication

The application uses JWT (JSON Web Tokens) for authentication:

1. Users register with email and password
2. Password is hashed using bcrypt
3. JWT tokens are issued upon login
4. Tokens are stored in HTTP-only cookies
5. Middleware validates tokens on each request

---

## 📚 API Endpoints

The application provides a comprehensive REST API:

### Users & Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile

### Trips
- `GET /api/trips` - List user's trips
- `POST /api/trips` - Create new trip
- `GET /api/trips/{id}` - Get trip details
- `PUT /api/trips/{id}` - Update trip
- `DELETE /api/trips/{id}` - Delete trip

### Places & Attractions
- `GET /api/places` - Browse all places
- `GET /api/places/{id}` - Get place details
- `GET /api/attractions` - List attractions
- `POST /api/attractions` - Create attraction

### Budget
- `GET /api/budget/{trip_id}` - Get trip budget
- `POST /api/budget` - Add budget entry

### Checklists
- `GET /api/checklists/{trip_id}` - Get checklist
- `POST /api/checklists` - Create checklist item
- `PUT /api/checklists/{item_id}` - Update item
- `DELETE /api/checklists/{item_id}` - Delete item

### Images
- `POST /api/upload` - Upload image
- `GET /api/images/{id}` - Get image

---

## 🎨 Features in Detail

### Trip Planning
Create trips with destination details and date ranges. Set budgets and track all aspects of your journey in one place.

### Smart Budget Tracking
Monitor expenses by category, compare against your budget, and get insights into your spending patterns.

### Photo Documentation
Upload and organize photos for each trip. The system stores metadata and automatically processes images.

### Interactive Checklists
Manage preparation tasks and activities for each trip with an interactive checklist system.

---

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙋 Support & Contact

- 📧 Email: steppingcode.github@gmail.com
- 🐛 Issues: Report bugs via GitHub Issues
- 💬 Discussions: Use GitHub Discussions for feature requests

---

## 🗺️ Roadmap

- [ ] Multi-language support (i18n)
- [ ] Mobile app (React Native)
- [ ] Integration with mapping services (Google Maps API)
- [ ] Expense splitting between travelers
- [ ] Collaborative trip planning
- [ ] Real-time notifications
- [ ] Export trip data (PDF, JSON)
- [ ] Weather integration

---

## 📊 Statistics

- 🐍 Built with Python & FastAPI
- 💾 SQLite database for reliable data storage
- 🔒 Secure authentication with JWT
- 📱 Responsive web design
- ⚡ Fast and lightweight

---

**Made with ❤️ for travel enthusiasts**
