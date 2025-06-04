from models import init_db, Faculty, Review
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def create_sample_data():
    # Initialize database
    engine = create_engine('sqlite:///faculty_ratings.db')
    init_db()
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create faculty member (with lower ratings)
        ard = Faculty(
            name="ARD",
            department="Computer Science"
        )
        session.add(ard)
        session.flush()  # This will assign an ID to ard
        
        # Add sample reviews with lower ratings
        reviews = [
            Review(
                faculty_id=ard.id,
                course_code="CSE330",
                teaching_effectiveness=2.5,
                student_engagement=2.2,
                clarity=2.0,
                professionalism=2.8,
                feedback="Difficult to follow lectures. Content is not well organized.",
                recommendation="Consider other professors if possible.",
                source_type="screenshot_analysis",
                created_at=datetime.utcnow()
            ),
            Review(
                faculty_id=ard.id,
                course_code="BUS221",
                teaching_effectiveness=2.3,
                student_engagement=2.0,
                clarity=2.2,
                professionalism=2.7,
                feedback="Teaching style needs improvement. Hard to understand concepts.",
                recommendation="Not recommended for this course.",
                source_type="screenshot_analysis",
                created_at=datetime.utcnow()
            )
        ]
        
        session.add_all(reviews)
        session.commit()
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_sample_data() 