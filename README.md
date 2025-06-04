# FacultyRate

A private, privacy-focused faculty rating system that uses AI to analyze student feedback while maintaining student confidentiality.

## Features

- 🔒 Privacy-First: All student information is automatically redacted
- 🤖 AI-Powered Analysis: Uses Google's Gemini AI for intelligent feedback analysis
- 📊 Comprehensive Rating System: Evaluates teaching effectiveness, student engagement, clarity, and professionalism
- 🖼️ Image Processing: Supports feedback submission through text and images using Gemini Vision AI
- 🌐 RESTful API: Complete API for managing faculty and reviews
- 🎯 Course-Specific Reviews: Support for course-specific faculty evaluations

## System Architecture

The system consists of two main components:
1. Main Application Server (`app.py`): Handles user interface and AI analysis
2. API Server (`api.py`): Manages data storage and retrieval

### Prerequisites

- Python 3.8+
- Google Gemini API Key
- SQLite3

### Installation

1. Clone the repository (requires access):
```bash
git clone https://github.com/yourusername/FacultyRate-Private.git
cd FacultyRate-Private
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Google API key
```

### Running the Application

1. Start the API server:
```bash
python api.py
```

2. In a new terminal, start the main application:
```bash
python app.py
```

The application will be available at:
- Main Application: http://localhost:5000
- API Server: http://localhost:5001

## API Documentation

### Faculty Endpoints

#### GET /api/faculty
Get all faculty members with their ratings.

#### POST /api/faculty/add
Add a new faculty member.
```json
{
    "name": "FACULTY_NAME",
    "department": "DEPARTMENT_NAME"
}
```

#### GET /api/faculty/{faculty_id}
Get detailed information about a specific faculty member.

#### POST /api/faculty/{faculty_id}/reviews
Add a review for a faculty member.
```json
{
    "course_code": "CS101",
    "ratings": {
        "teaching_effectiveness": 4.5,
        "student_engagement": 4.0,
        "clarity": 4.2,
        "professionalism": 4.8
    },
    "feedback": "Feedback text",
    "recommendation": "Recommendation text"
}
```

### Review Management

#### DELETE /api/faculty/{faculty_id}/reviews
Delete all reviews for a faculty member.

#### DELETE /api/reviews/course/{course_code}
Delete all reviews for a specific course.

## Privacy Features

- Automatic redaction of student names and personal information
- Replacement of identifiable information with placeholders
- Focus on academic content only
- Protection of class-specific details
- Secure handling of faculty information

## Development

### Project Structure
```
FacultyRate/
├── app.py              # Main application server
├── api.py              # API server
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── uploads/           # Temporary upload directory
```

### Database Schema

The system uses SQLite with SQLAlchemy ORM:
- Faculty table: Stores faculty information and aggregate ratings
- Review table: Stores individual reviews with privacy-safe content

## Notice

This is a private project. All rights reserved. Unauthorized copying, modification, distribution, or use of this software is strictly prohibited. 