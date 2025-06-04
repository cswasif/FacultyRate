from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Faculty, Review, init_db, DBSession
from statistics import mean
import logging
from flask_cors import CORS  # Add CORS support
from sqlalchemy.sql import func
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def error_response(message, status_code=400):
    """Standardized error response"""
    return jsonify({
        'error': True,
        'message': message
    }), status_code

# Database setup
engine = create_engine('sqlite:///faculty_ratings.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

# Ensure database and tables exist
init_db()

@contextmanager
def get_db_session():
    """Database session context manager"""
    session = DBSession()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

@app.route('/')
def index():
    """Root endpoint that shows API status"""
    return jsonify({
        'status': 'online',
        'message': 'Faculty Rating API is running',
        'endpoints': {
            'GET /': 'This help message',
            'GET /api/faculty': 'List all faculty members',
            'POST /api/faculty/add': 'Add a new faculty member',
            'GET /api/faculty/<id>': 'Get faculty details',
            'POST /api/faculty/<id>/reviews': 'Add a review for faculty',
            'GET /api/verify-data': 'Verify database contents'
        }
    })

def update_faculty_ratings(faculty_id):
    """Update aggregate ratings for a faculty member"""
    session = DBSession()
    try:
        faculty = session.get(Faculty, faculty_id)
        if faculty and faculty.reviews:
            faculty.avg_teaching_effectiveness = mean([r.teaching_effectiveness for r in faculty.reviews])
            faculty.avg_student_engagement = mean([r.student_engagement for r in faculty.reviews])
            faculty.avg_clarity = mean([r.clarity for r in faculty.reviews])
            faculty.avg_professionalism = mean([r.professionalism for r in faculty.reviews])
            faculty.overall_rating = mean([
                faculty.avg_teaching_effectiveness,
                faculty.avg_student_engagement,
                faculty.avg_clarity,
                faculty.avg_professionalism
            ])
            faculty.total_reviews = len(faculty.reviews)
            session.commit()
    finally:
        session.close()

def get_or_create_faculty(name, department=None):
    """Get existing faculty or create new one"""
    session = DBSession()
    try:
        # Try to find existing faculty
        faculty = session.query(Faculty).filter(Faculty.name == name).first()
        
        # If not found, create new faculty
        if not faculty:
            faculty = Faculty(
                name=name,
                department=department,
                avg_teaching_effectiveness=0.0,
                avg_student_engagement=0.0,
                avg_clarity=0.0,
                avg_professionalism=0.0,
                overall_rating=0.0,
                total_reviews=0
            )
            session.add(faculty)
            session.commit()
            print(f"Created new faculty: {name}")
        
        return faculty.id
    finally:
        session.close()

@app.route('/api/faculty', methods=['GET'])
def get_all_faculty():
    """Get list of all faculty with their aggregate ratings"""
    try:
        with get_db_session() as session:
            faculty_list = session.query(Faculty).all()
            return jsonify({
                'faculty': [{
                    'id': f.id,
                    'name': f.name,
                    'department': f.department,
                    'ratings': f.average_ratings,
                    'total_reviews': len(f.reviews)
                } for f in faculty_list]
            })
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/faculty/<faculty_id>', methods=['GET'])
def get_faculty_details(faculty_id):
    """Get detailed information about a specific faculty member"""
    session = DBSession()
    try:
        faculty = session.get(Faculty, faculty_id)
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
            
        ratings = faculty.average_ratings
        return jsonify({
            'id': faculty.id,
            'name': faculty.name,
            'department': faculty.department,
            'ratings': ratings,
            'total_reviews': len(faculty.reviews),
            'reviews': [{
                'course_code': r.course_code,
                'ratings': {
                    'teaching_effectiveness': r.teaching_effectiveness,
                    'student_engagement': r.student_engagement,
                    'clarity': r.clarity,
                    'professionalism': r.professionalism
                },
                'feedback': r.feedback,
                'recommendation': r.recommendation,
                'created_at': r.created_at.isoformat(),
                'source_type': r.source_type
            } for r in faculty.reviews]
        })
    finally:
        session.close()

@app.route('/api/faculty/add', methods=['POST'])
def add_faculty():
    """Add a new faculty member"""
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
        
    faculty_id = get_or_create_faculty(data['name'], data.get('department'))
    return jsonify({
        'message': 'Faculty added successfully',
        'faculty_id': faculty_id
    })

@app.route('/api/faculty/<faculty_id>/reviews', methods=['POST'])
def add_faculty_review(faculty_id):
    """Add a new review for a faculty member"""
    session = DBSession()
    try:
        # Check if faculty exists, if not and name is provided, create them
        faculty = session.get(Faculty, faculty_id)
        if not faculty:
            if 'faculty_name' in request.json:
                faculty_id = get_or_create_faculty(
                    request.json['faculty_name'],
                    request.json.get('department')
                )
                faculty = session.get(Faculty, faculty_id)
            else:
                return jsonify({'error': 'Faculty not found'}), 404
            
        data = request.json
        review = Review(
            faculty_id=faculty_id,
            course_code=data['course_code'],
            teaching_effectiveness=data['ratings']['teaching_effectiveness'],
            student_engagement=data['ratings']['student_engagement'],
            clarity=data['ratings']['clarity'],
            professionalism=data['ratings']['professionalism'],
            feedback=data.get('feedback'),
            recommendation=data.get('recommendation'),
            source_type=data.get('source_type', 'direct_submission')
        )
        
        session.add(review)
        session.commit()
        
        # Update aggregate ratings
        update_faculty_ratings(faculty_id)
        
        return jsonify({
            'message': 'Review added successfully',
            'review_id': review.id
        })
    finally:
        session.close()

@app.route('/api/verify-data', methods=['GET'])
def verify_data():
    """Endpoint to verify database contents"""
    try:
        session = DBSession()
        faculty_count = session.query(Faculty).count()
        review_count = session.query(Review).count()
        
        # Get latest review for verification
        latest_review = session.query(Review).order_by(Review.id.desc()).first()
        latest_faculty = session.query(Faculty).order_by(Faculty.id.desc()).first()
        
        data = {
            'faculty_count': faculty_count,
            'review_count': review_count,
            'latest_faculty': latest_faculty.name if latest_faculty else None,
            'latest_review_course': latest_review.course_code if latest_review else None
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/add-test-data', methods=['POST'])
def add_test_data():
    """Endpoint to add test data"""
    try:
        session = DBSession()
        
        # Add test faculty
        faculty = Faculty(name="ARD", department="Computer Science")
        session.add(faculty)
        session.flush()
        
        # Add test review
        review = Review(
            faculty_id=faculty.id,
            course_code="TEST101",
            teaching_effectiveness=3.5,
            student_engagement=3.0,
            clarity=3.2,
            professionalism=3.8,
            feedback="Test feedback",
            recommendation="Test recommendation",
            source_type="test_data"
        )
        session.add(review)
        session.commit()
        
        return jsonify({'message': 'Test data added successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/clear-test-data', methods=['POST'])
def clear_test_data():
    """Remove test data from the database"""
    session = DBSession()
    try:
        # Delete reviews with source_type 'test_data'
        test_reviews = session.query(Review).filter_by(source_type='test_data').all()
        for review in test_reviews:
            session.delete(review)
        
        # Delete faculty with no reviews
        faculty_no_reviews = session.query(Faculty).filter(~Faculty.reviews.any()).all()
        for faculty in faculty_no_reviews:
            session.delete(faculty)
            
        session.commit()
        return jsonify({'message': 'Test data cleared successfully'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/ARD/reviews', methods=['GET'])
def get_ard_reviews():
    """Get all reviews for ARD across all entries"""
    session = DBSession()
    try:
        # Get all faculty entries for ARD
        ard_entries = session.query(Faculty).filter_by(name="ARD").all()
        
        if not ard_entries:
            return jsonify({'error': 'No ARD entries found'}), 404
            
        # Combine all reviews
        all_reviews = []
        total_ratings = {
            'teaching_effectiveness': 0,
            'student_engagement': 0,
            'clarity': 0,
            'professionalism': 0
        }
        total_count = 0
        
        for faculty in ard_entries:
            for review in faculty.reviews:
                all_reviews.append({
                    'course_code': review.course_code,
                    'ratings': {
                        'teaching_effectiveness': review.teaching_effectiveness,
                        'student_engagement': review.student_engagement,
                        'clarity': review.clarity,
                        'professionalism': review.professionalism
                    },
                    'feedback': review.feedback,
                    'recommendation': review.recommendation,
                    'created_at': review.created_at.isoformat(),
                    'source_type': review.source_type
                })
                total_ratings['teaching_effectiveness'] += review.teaching_effectiveness
                total_ratings['student_engagement'] += review.student_engagement
                total_ratings['clarity'] += review.clarity
                total_ratings['professionalism'] += review.professionalism
                total_count += 1
        
        # Calculate averages
        avg_ratings = {
            k: round(v/total_count, 2) if total_count > 0 else 0 
            for k, v in total_ratings.items()
        }
        avg_ratings['overall'] = round(sum(avg_ratings.values()) / 4, 2)
        
        return jsonify({
            'name': "ARD",
            'department': "Computer Science",
            'total_reviews': total_count,
            'average_ratings': avg_ratings,
            'reviews': sorted(all_reviews, key=lambda x: x['created_at'], reverse=True)
        })
    finally:
        session.close()

@app.route('/api/consolidate-ard', methods=['POST'])
def consolidate_ard():
    """Consolidate all ARD entries into one"""
    session = DBSession()
    try:
        # Get all ARD entries
        ard_entries = session.query(Faculty).filter_by(name="ARD").all()
        
        if len(ard_entries) <= 1:
            return jsonify({'message': 'No consolidation needed'})
            
        # Keep the first entry and move all reviews to it
        main_ard = ard_entries[0]
        
        for faculty in ard_entries[1:]:
            # Move all reviews to main ARD entry
            for review in faculty.reviews:
                review.faculty_id = main_ard.id
            # Delete the duplicate faculty entry
            session.delete(faculty)
        
        session.commit()
        
        return jsonify({'message': f'Successfully consolidated {len(ard_entries)} ARD entries into one'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/reviews/clear', methods=['POST'])
def clear_all_reviews():
    """Remove all reviews from the database"""
    session = DBSession()
    try:
        # Delete all reviews
        deleted_count = session.query(Review).delete()
        session.commit()
        return jsonify({
            'message': 'All reviews cleared successfully',
            'reviews_deleted': deleted_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reviews/course/<course_code>', methods=['DELETE'])
def delete_course_reviews(course_code):
    """Delete all reviews for a specific course"""
    session = DBSession()
    try:
        # Delete all reviews for the specified course
        deleted_count = session.query(Review).filter_by(course_code=course_code).delete()
        session.commit()
        
        # Update ratings for affected faculty members
        affected_faculty = session.query(Faculty).filter(Faculty.reviews.any()).all()
        for faculty in affected_faculty:
            update_faculty_ratings(faculty.id)
            
        return jsonify({
            'message': f'Successfully deleted all reviews for course {course_code}',
            'reviews_deleted': deleted_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/<faculty_id>/reviews/course/<course_code>', methods=['DELETE'])
def delete_faculty_course_reviews(faculty_id, course_code):
    """Delete all reviews for a specific course from a specific faculty member"""
    session = DBSession()
    try:
        # Check if faculty exists
        faculty = session.get(Faculty, faculty_id)
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
            
        # Delete reviews for the specified course from this faculty
        deleted_count = session.query(Review).filter_by(
            faculty_id=faculty_id,
            course_code=course_code
        ).delete()
        session.commit()
        
        # Update ratings for the faculty member
        update_faculty_ratings(faculty_id)
            
        return jsonify({
            'message': f'Successfully deleted reviews for course {course_code} from faculty {faculty.name}',
            'reviews_deleted': deleted_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/<faculty_name>', methods=['GET'])
def get_faculty_by_name(faculty_name):
    """Get faculty details by name"""
    session = DBSession()
    try:
        # Case-insensitive search for faculty name
        faculty = session.query(Faculty).filter(Faculty.name == faculty_name).first()
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
            
        # Get all reviews for this faculty
        reviews = session.query(Review).filter_by(faculty_id=faculty.id).all()
        
        # Calculate ratings
        total_reviews = len(reviews)
        if total_reviews > 0:
            avg_teaching = sum(r.teaching_effectiveness for r in reviews) / total_reviews
            avg_engagement = sum(r.student_engagement for r in reviews) / total_reviews
            avg_clarity = sum(r.clarity for r in reviews) / total_reviews
            avg_prof = sum(r.professionalism for r in reviews) / total_reviews
            overall = (avg_teaching + avg_engagement + avg_clarity + avg_prof) / 4
        else:
            avg_teaching = avg_engagement = avg_clarity = avg_prof = overall = 0
            
        return jsonify({
            'id': faculty.id,
            'name': faculty.name,
            'department': faculty.department,
            'ratings': {
                'teaching_effectiveness': float(avg_teaching),
                'student_engagement': float(avg_engagement),
                'clarity': float(avg_clarity),
                'professionalism': float(avg_prof),
                'overall': float(overall)
            },
            'total_reviews': total_reviews,
            'reviews': [{
                'course_code': r.course_code,
                'teaching_effectiveness': float(r.teaching_effectiveness),
                'student_engagement': float(r.student_engagement),
                'clarity': float(r.clarity),
                'professionalism': float(r.professionalism),
                'feedback': r.feedback
            } for r in reviews]
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/<faculty_name>/reviews', methods=['GET'])
def get_faculty_reviews(faculty_name):
    """Get all reviews for a faculty member across all entries"""
    session = DBSession()
    try:
        # Get all faculty entries for the given name
        faculty_entries = session.query(Faculty).filter_by(name=faculty_name.upper()).all()
        
        if not faculty_entries:
            return jsonify({'error': f'No {faculty_name} entries found'}), 404
            
        # Combine all reviews
        all_reviews = []
        total_ratings = {
            'teaching_effectiveness': 0,
            'student_engagement': 0,
            'clarity': 0,
            'professionalism': 0
        }
        total_count = 0
        
        for faculty in faculty_entries:
            for review in faculty.reviews:
                all_reviews.append({
                    'course_code': review.course_code,
                    'ratings': {
                        'teaching_effectiveness': review.teaching_effectiveness,
                        'student_engagement': review.student_engagement,
                        'clarity': review.clarity,
                        'professionalism': review.professionalism
                    },
                    'feedback': review.feedback,
                    'recommendation': review.recommendation,
                    'created_at': review.created_at.isoformat(),
                    'source_type': review.source_type
                })
                total_ratings['teaching_effectiveness'] += review.teaching_effectiveness
                total_ratings['student_engagement'] += review.student_engagement
                total_ratings['clarity'] += review.clarity
                total_ratings['professionalism'] += review.professionalism
                total_count += 1
        
        # Calculate averages
        avg_ratings = {
            k: round(v/total_count, 2) if total_count > 0 else 0 
            for k, v in total_ratings.items()
        }
        avg_ratings['overall'] = round(sum(avg_ratings.values()) / 4, 2)
        
        # Get department from first entry
        department = faculty_entries[0].department if faculty_entries else None
        
        return jsonify({
            'name': faculty_name.upper(),
            'department': department,
            'total_reviews': total_count,
            'average_ratings': avg_ratings,
            'reviews': sorted(all_reviews, key=lambda x: x['created_at'], reverse=True)
        })
    finally:
        session.close()

@app.route('/api/faculty/<int:faculty_id>/reviews', methods=['DELETE'])
def delete_faculty_reviews(faculty_id):
    """Delete all reviews for a faculty member"""
    session = DBSession()
    try:
        reviews = session.query(Review).filter_by(faculty_id=faculty_id).all()
        for review in reviews:
            session.delete(review)
        session.commit()
        return jsonify({'message': f'All reviews for faculty {faculty_id} deleted.'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/<int:faculty_id>', methods=['DELETE'])
def delete_faculty(faculty_id):
    """Delete a faculty member"""
    session = DBSession()
    try:
        faculty = session.get(Faculty, faculty_id)
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
        session.delete(faculty)
        session.commit()
        return jsonify({'message': f'Faculty {faculty_id} deleted.'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/review/<int:review_id>', methods=['DELETE'])
def delete_review_by_id(review_id):
    """Delete a review by its ID"""
    session = DBSession()
    try:
        review = session.query(Review).get(review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        session.delete(review)
        session.commit()
        return jsonify({'message': f'Review {review_id} deleted.'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/routes')
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:30s} {methods:20s} {str(rule)}")
        output.append(line)
    return "<pre>" + "\n".join(output) + "</pre>"

@app.route('/api/faculty/<faculty_name>/reviews/delete', methods=['POST'])
def delete_faculty_reviews_by_name(faculty_name):
    """Delete all reviews for a faculty member by name"""
    session = DBSession()
    try:
        # Find faculty by name
        faculty = session.query(Faculty).filter(Faculty.name == faculty_name.upper()).first()
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
            
        # Delete all reviews for this faculty
        deleted_count = session.query(Review).filter_by(faculty_id=faculty.id).delete()
        session.commit()
        
        # Update faculty ratings
        update_faculty_ratings(faculty.id)
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} reviews for faculty {faculty_name}',
            'reviews_deleted': deleted_count
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/faculty/search/<faculty_name>', methods=['GET'])
def search_faculty_by_name(faculty_name):
    """Search for a faculty member by name"""
    session = DBSession()
    try:
        faculty = session.query(Faculty).filter(Faculty.name == faculty_name.upper()).first()
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
        return jsonify({
            'faculty_id': faculty.id,
            'name': faculty.name,
            'department': faculty.department
        })
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001) 