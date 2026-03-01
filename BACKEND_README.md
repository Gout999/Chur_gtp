# ChurGPT Backend API

A complete, reliable backend platform for the ChurGPT intelligent learning system.

## Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (Teacher/Student)
- Secure password hashing with bcrypt
- Token-based API protection

### Teacher Features
- **Class Management**: Create, update, delete classes
- **Material Management**: Upload and organize learning materials
- **Assignment Management**: Create assignments and grade submissions
- **Student Enrollment**: Add/remove students from classes
- **AI Enhancement**: Request AI-powered material enhancement
- **Dashboard Analytics**: View class and student statistics

### Student Features
- **Class Access**: View enrolled classes and materials
- **Assignment Submission**: Submit work and track grades
- **Mistake Tracking**: Log and review learning mistakes
- **AI Chat**: Interactive homework help with AI tutor
- **Dashboard**: Track assignments and learning progress

### AI Integration
- **Chat Assistant**: OpenAI-powered homework helper
- **Material Enhancement**: AI-generated study notes
- **Mock Mode**: Works without API keys for development

## Technology Stack

- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT + OAuth2
- **AI**: OpenAI API (optional)
- **Container**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (optional, SQLite works for development)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone and navigate to the project**
```bash
cd /Users/gout/Chur_gtp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up -d
```

This will start:
- API server on port 8000
- PostgreSQL database on port 5432
- Redis cache on port 6379

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user info

### Teachers
- `GET /api/v1/teachers/classes` - List all classes
- `POST /api/v1/teachers/classes` - Create new class
- `GET /api/v1/teachers/classes/{id}` - Get class details
- `PUT /api/v1/teachers/classes/{id}` - Update class
- `DELETE /api/v1/teachers/classes/{id}` - Delete class
- `POST /api/v1/teachers/classes/{id}/students/{student_id}` - Enroll student
- `GET /api/v1/teachers/materials` - List materials
- `POST /api/v1/teachers/materials` - Create material
- `GET /api/v1/teachers/assignments` - List assignments
- `POST /api/v1/teachers/assignments` - Create assignment
- `GET /api/v1/teachers/dashboard/stats` - Get statistics

### Students
- `GET /api/v1/students/classes` - List enrolled classes
- `GET /api/v1/students/materials` - List accessible materials
- `GET /api/v1/students/assignments` - List assignments
- `POST /api/v1/students/assignments/{id}/submissions` - Submit assignment
- `GET /api/v1/students/mistakes` - List mistakes
- `POST /api/v1/students/mistakes` - Add mistake
- `GET /api/v1/students/mistakes/stats` - Get mistake statistics
- `GET /api/v1/students/dashboard/stats` - Get statistics

### Chat
- `GET /api/v1/chat/sessions` - List chat sessions
- `POST /api/v1/chat/sessions` - Create session
- `POST /api/v1/chat/send` - Send message and get AI response
- `GET /api/v1/chat/sessions/{id}/messages` - Get messages

### AI Enhancement
- `POST /api/v1/ai/enhance` - Request material enhancement
- `GET /api/v1/ai/enhance/{id}` - Check enhancement status

## Database Schema

### Core Tables
- **users** - Authentication and user info
- **teacher_profiles** - Teacher-specific data
- **student_profiles** - Student-specific data
- **classes** - Course/class information
- **class_enrollments** - Student-class relationships
- **materials** - Learning materials
- **enhanced_notes** - AI-generated enhancements
- **assignments** - Homework and assessments
- **submissions** - Student work submissions
- **mistakes** - Student mistake tracking
- **chat_sessions** - AI chat sessions
- **chat_messages** - Chat history

## Configuration

### Environment Variables

```env
# Application
APP_ENV=development
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///./churgpt.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/churgpt

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Security Notes

- **Change SECRET_KEY** in production
- Use strong database passwords
- Enable HTTPS in production
- Set up proper CORS origins
- Use environment-specific configurations

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Project Structure
```
app/
├── api/v1/           # API routes
├── core/             # Security and config
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── database.py       # Database connection
└── main.py           # Application entry
```

## Production Deployment

### Using Docker
```bash
docker-compose -f docker-compose.yml up -d
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure environment variables
3. Run migrations: `alembic upgrade head`
4. Start with gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`

### Environment Checklist
- [ ] Change SECRET_KEY
- [ ] Set up PostgreSQL
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up logging
- [ ] Configure backup strategy

## License

MIT License

## Support

For issues and questions, please refer to the GitHub repository or contact the development team.
