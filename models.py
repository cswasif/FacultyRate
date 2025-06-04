from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///faculty_ratings.db')
DBSession = sessionmaker(bind=engine)

class Faculty(Base):
    __tablename__ = 'faculty'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    department = Column(String)
    avg_teaching_effectiveness = Column(Float, default=0.0)
    avg_student_engagement = Column(Float, default=0.0)
    avg_clarity = Column(Float, default=0.0)
    avg_professionalism = Column(Float, default=0.0)
    overall_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    reviews = relationship("Review", back_populates="faculty")
    
    @property
    def average_ratings(self):
        if not self.reviews:
            return {
                'teaching_effectiveness': 0,
                'student_engagement': 0,
                'clarity': 0,
                'professionalism': 0,
                'overall': 0
            }
        
        total = {
            'teaching_effectiveness': 0,
            'student_engagement': 0,
            'clarity': 0,
            'professionalism': 0
        }
        
        count = 0
        for review in self.reviews:
            if review.source_type == 'screenshot_analysis':
                total['teaching_effectiveness'] += review.teaching_effectiveness
                total['student_engagement'] += review.student_engagement
                total['clarity'] += review.clarity
                total['professionalism'] += review.professionalism
                count += 1
        
        if count == 0:
            return {
                'teaching_effectiveness': 0,
                'student_engagement': 0,
                'clarity': 0,
                'professionalism': 0,
                'overall': 0
            }
        
        avg = {k: round(v/count, 2) for k, v in total.items()}
        avg['overall'] = round(sum(avg.values()) / 4, 2)
        
        return avg

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey('faculty.id'))
    course_code = Column(String, nullable=False)
    teaching_effectiveness = Column(Float, nullable=False)
    student_engagement = Column(Float, nullable=False)
    clarity = Column(Float, nullable=False)
    professionalism = Column(Float, nullable=False)
    feedback = Column(String)
    recommendation = Column(String)
    source_type = Column(String, default='direct_submission')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="reviews")

# Create tables
def init_db():
    Base.metadata.create_all(engine) 