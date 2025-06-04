from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Faculty, Review
import sqlite3

def read_with_sqlalchemy():
    """Read database using SQLAlchemy"""
    print("\n=== Reading with SQLAlchemy ===")
    
    # Create database engine using URL
    engine = create_engine('sqlite:///faculty_ratings.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all faculty members
        faculty_members = session.query(Faculty).all()
        print(f"\nNumber of faculty members: {len(faculty_members)}")
        for faculty in faculty_members:
            print(f"\nFaculty: {faculty.name}")
            print(f"Department: {faculty.department}")
            print("Average Ratings:", faculty.average_ratings)
        
        # Get all reviews
        reviews = session.query(Review).all()
        print(f"\nNumber of reviews: {len(reviews)}")
        for review in reviews:
            print(f"\nCourse: {review.course_code}")
            print(f"Teaching Effectiveness: {review.teaching_effectiveness}")
            print(f"Source: {review.source_type}")
    finally:
        session.close()

def read_with_sqlite():
    """Read database using direct SQLite connection"""
    print("\n=== Reading with SQLite ===")
    
    # Connect to database using URL
    conn = sqlite3.connect('faculty_ratings.db')
    cursor = conn.cursor()
    
    try:
        # Get all faculty members
        cursor.execute('SELECT name, department FROM faculty')
        faculty_members = cursor.fetchall()
        print(f"\nNumber of faculty members: {len(faculty_members)}")
        for name, department in faculty_members:
            print(f"\nFaculty: {name}")
            print(f"Department: {department}")
        
        # Get all reviews
        cursor.execute('''
            SELECT course_code, teaching_effectiveness, source_type 
            FROM reviews
        ''')
        reviews = cursor.fetchall()
        print(f"\nNumber of reviews: {len(reviews)}")
        for course_code, teaching_effectiveness, source_type in reviews:
            print(f"\nCourse: {course_code}")
            print(f"Teaching Effectiveness: {teaching_effectiveness}")
            print(f"Source: {source_type}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Reading database using different methods...")
    read_with_sqlalchemy()
    read_with_sqlite() 