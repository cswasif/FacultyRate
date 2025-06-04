import os
from flask import Flask, request, render_template, jsonify
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
import logging
import time
import requests
from werkzeug.exceptions import RequestEntityTooLarge
import re
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"],
        "expose_headers": ["Content-Type"]
    }
})

# Increase maximum file size to 32MB
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size
# Set maximum file count
app.config['MAX_FILES'] = 10  # Maximum number of files per upload

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Add error handler for file too large
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        'error': 'File too large',
        'message': 'The uploaded file exceeds the maximum size limit (32MB)',
        'max_size_mb': 32
    }), 413

# Add error handler for general exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

def validate_faculty_name(name):
    """Validate faculty name"""
    if not name or not isinstance(name, str):
        return False, "Faculty name is required and must be a string"
    if len(name.strip()) < 2:
        return False, "Faculty name must be at least 2 characters long"
    return True, None

def validate_course_codes(codes):
    """Validate course codes"""
    if not codes:
        return True, None  # Course codes are optional
    if not isinstance(codes, list):
        return False, "Course codes must be a list"
    if any(not isinstance(code, str) for code in codes):
        return False, "All course codes must be strings"
    return True, None

def analyze_feedback(text, faculty_name, course_codes=None):
    """Analyze feedback text using Gemini"""
    try:
        # Use gemini-1.5-flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        course_filter = ""
        if course_codes:
            course_list = ", ".join(course_codes)
            course_filter = f"Look ONLY for reviews of {faculty_name}'s courses: {course_list}."
        
        # Create prompt for analysis
        prompt = f"""
        You are analyzing student feedback about faculty member {faculty_name}.
        Some feedback may be short, meme-like, or use slang. Interpret all comments, even if brief or informal, as genuine feedback and extract as much meaning as possible. Do not use the word 'Professor' in your response, as the faculty member's title is unknown.
        {course_filter if course_filter else f"Look ONLY for mentions and reviews of {faculty_name}."}
        
        PRIVACY AND CONFIDENTIALITY REQUIREMENTS:
        1. NEVER include or mention any student names in your analysis
        2. REDACT or REMOVE any personally identifiable information about students
        3. If you encounter student names or personal details, replace them with "[Student]"
        4. Focus only on the academic feedback content
        5. Do not include specific dates, class times, or other details that could identify students
        6. If feedback mentions other faculty members, refer to them as "[Other Faculty]"
        
        IMPORTANT GUIDELINES:
        1. Focus on DIRECT STUDENT EXPERIENCES, not second-hand accounts
        2. Consider RECENT feedback more heavily than older feedback
        3. Look for SPECIFIC examples and incidents (while maintaining privacy)
        4. Pay attention to both POSITIVE and NEGATIVE comments
        5. Consider CONSISTENCY across multiple reviews
        6. If feedback is mixed, it should be reflected in the ratings
        7. Default to 3.0 ONLY if there's no clear evidence
        
        REQUIRED OUTPUT FORMAT:
        Faculty Review Analysis
        ===========================
        FACULTY REVIEW: {faculty_name}
        Course: {course_list if course_codes else "All Courses"}
        ===========================

        DETAILED RATINGS FOR {faculty_name}:
        1. Teaching effectiveness: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        2. Student engagement: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        3. Clarity of presentation: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        4. Overall professionalism: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        ===========================
        OVERALL RATING FOR {faculty_name}: [X]/5
        ===========================

        STUDENT FEEDBACK SUMMARY FOR {faculty_name}:
        Positive Points:
        - [List specific positive points with evidence, ensuring student privacy]

        Areas for Improvement:
        - [List specific areas needing improvement with evidence, ensuring student privacy]

        FINAL RECOMMENDATION:
        [Clear advice for future students about taking courses with this faculty, maintaining privacy and confidentiality]
        """
        
        response = model.generate_content(prompt)
        
        # Check if response contains actual feedback
        if "NO_FEEDBACK_FOUND" in response.text:
            return None, None, None
            
        # Extract ratings using regex
        ratings = {
            'teaching_effectiveness': None,
            'student_engagement': None,
            'clarity': None,
            'professionalism': None,
            'overall': None
        }
        
        # Extract ratings with patterns
        effectiveness_match = re.search(r'Teaching effectiveness:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        engagement_match = re.search(r'Student engagement:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        clarity_match = re.search(r'Clarity of presentation:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        professionalism_match = re.search(r'Overall professionalism:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        overall_match = re.search(r'OVERALL RATING.*?:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        
        # Set ratings from matches
        if effectiveness_match:
            ratings['teaching_effectiveness'] = float(effectiveness_match.group(1))
        if engagement_match:
            ratings['student_engagement'] = float(engagement_match.group(1))
        if clarity_match:
            ratings['clarity'] = float(clarity_match.group(1))
        if professionalism_match:
            ratings['professionalism'] = float(professionalism_match.group(1))
        if overall_match:
            ratings['overall'] = float(overall_match.group(1))
        else:
            # Calculate overall as average if not explicitly provided
            valid_ratings = [v for v in ratings.values() if v is not None]
            if valid_ratings:
                ratings['overall'] = sum(valid_ratings) / len(valid_ratings)
        
        # Extract recommendation
        recommendation_match = re.search(r'FINAL RECOMMENDATION:\s*(.+?)(?=={3,}|$)', response.text, re.DOTALL)
        recommendation = recommendation_match.group(1).strip() if recommendation_match else None
            
        return ratings, response.text, recommendation
        
    except Exception as e:
        logging.error(f"Error in analyze_feedback: {str(e)}")
        return None, None, None

def analyze_images_with_gemini(image_paths, faculty_name, course_codes=None):
    """Analyze multiple screenshots using Gemini Vision model directly (no OCR)"""
    try:
        # Use gemini-1.5-flash model with vision
        model = genai.GenerativeModel('gemini-1.5-flash')
        course_filter = ""
        if course_codes:
            course_list = ", ".join(course_codes)
            course_filter = f"Look ONLY for reviews of {faculty_name}'s courses: {course_list}."
        prompt = f"""
        You are analyzing student feedback about faculty member {faculty_name}.
        Some feedback may be short, meme-like, or use slang. Interpret all comments, even if brief or informal, as genuine feedback and extract as much meaning as possible. Do not use the word 'Professor' in your response, as the faculty member's title is unknown.
        {course_filter if course_filter else f"Look ONLY for mentions and reviews of {faculty_name}."}
        
        PRIVACY AND CONFIDENTIALITY REQUIREMENTS:
        1. NEVER include or mention any student names in your analysis
        2. REDACT or REMOVE any personally identifiable information about students
        3. If you encounter student names or personal details, replace them with "[Student]"
        4. Focus only on the academic feedback content
        5. Do not include specific dates, class times, or other details that could identify students
        6. If feedback mentions other faculty members, refer to them as "[Other Faculty]"
        
        IMPORTANT GUIDELINES:
        1. Focus on DIRECT STUDENT EXPERIENCES, not second-hand accounts
        2. Consider RECENT feedback more heavily than older feedback
        3. Look for SPECIFIC examples and incidents (while maintaining privacy)
        4. Pay attention to both POSITIVE and NEGATIVE comments
        5. Consider CONSISTENCY across multiple reviews
        6. If feedback is mixed, it should be reflected in the ratings
        7. Default to 3.0 ONLY if there's no clear evidence
        
        REQUIRED OUTPUT FORMAT:
        Faculty Review Analysis
        ===========================
        FACULTY REVIEW: {faculty_name}
        Course: {course_list if course_codes else "All Courses"}
        ===========================

        DETAILED RATINGS FOR {faculty_name}:
        1. Teaching effectiveness: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        2. Student engagement: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        3. Clarity of presentation: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        4. Overall professionalism: [X]/5
        - [Detailed evidence and quotes from student feedback, with all personal information redacted]

        ===========================
        OVERALL RATING FOR {faculty_name}: [X]/5
        ===========================

        STUDENT FEEDBACK SUMMARY FOR {faculty_name}:
        Positive Points:
        - [List specific positive points with evidence, ensuring student privacy]

        Areas for Improvement:
        - [List specific areas needing improvement with evidence, ensuring student privacy]

        FINAL RECOMMENDATION:
        [Clear advice for future students about taking courses with this faculty, maintaining privacy and confidentiality]
        """
        # Prepare images for Gemini
        gemini_images = [Image.open(path) for path in image_paths]
        response = model.generate_content([prompt] + gemini_images)
        # Use the same regex extraction as before
        ratings = {
            'teaching_effectiveness': None,
            'student_engagement': None,
            'clarity': None,
            'professionalism': None,
            'overall': None
        }
        effectiveness_match = re.search(r'Teaching effectiveness:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        engagement_match = re.search(r'Student engagement:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        clarity_match = re.search(r'Clarity of presentation:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        professionalism_match = re.search(r'Overall professionalism:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        overall_match = re.search(r'OVERALL RATING.*?:\s*([\d.]+)/5', response.text, re.IGNORECASE)
        if effectiveness_match:
            ratings['teaching_effectiveness'] = float(effectiveness_match.group(1))
        if engagement_match:
            ratings['student_engagement'] = float(engagement_match.group(1))
        if clarity_match:
            ratings['clarity'] = float(clarity_match.group(1))
        if professionalism_match:
            ratings['professionalism'] = float(professionalism_match.group(1))
        if overall_match:
            ratings['overall'] = float(overall_match.group(1))
        else:
            valid_ratings = [v for v in ratings.values() if v is not None]
            if valid_ratings:
                ratings['overall'] = sum(valid_ratings) / len(valid_ratings)
        recommendation_match = re.search(r'FINAL RECOMMENDATION:\s*(.+?)(?=={3,}|$)', response.text, re.DOTALL)
        recommendation = recommendation_match.group(1).strip() if recommendation_match else None
        return response.text, ratings, recommendation
    except Exception as e:
        logging.error(f"Error in analyze_images_with_gemini: {str(e)}")
        raise e

@app.route('/')
def index():
    """Redirect to API documentation"""
    return """
    <h1>Faculty Rating System</h1>
    <p>This is the main application server. For API documentation, visit:</p>
    <ul>
        <li><a href="http://localhost:5001/routes">API Routes Documentation</a></li>
    </ul>
    """

@app.route('/delete-review')
def delete_review_page():
    """Serve the delete review page"""
    return render_template('delete_review.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle image upload and analysis"""
    try:
        # Get faculty name and validate
        faculty_name = request.form.get('faculty_name', '').strip().upper()
        is_valid, error_msg = validate_faculty_name(faculty_name)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
            
        # Get and validate course codes
        course_codes = []
        for key in request.form:
            if key.startswith('course_codes['):
                code = request.form[key].strip().upper()
                if code:
                    course_codes.append(code)
        
        is_valid, error_msg = validate_course_codes(course_codes)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Log inputs
        logging.debug(f"Faculty name: {faculty_name}")
        if course_codes:
            logging.debug(f"Course codes: {course_codes}")
            
        # Get uploaded files
        files = request.files.getlist('images')
        logging.debug(f"Files in request: {files}")
        logging.debug(f"Form data: {request.form}")
        
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400
            
        if len(files) > app.config['MAX_FILES']:
            return jsonify({
                'error': 'Too many files',
                'message': f'Maximum {app.config["MAX_FILES"]} files allowed per upload'
            }), 400
        
        # Save uploaded files
        saved_files = []
        logging.debug(f"Number of files received: {len(files)}")
        
        for i, file in enumerate(files):
            if file.filename:
                # Ensure filename is safe
                filename = f"upload_{i}_{file.filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                logging.debug(f"Saving file to: {filepath}")
                file.save(filepath)
                saved_files.append(filepath)
        
        logging.debug(f"Successfully saved {len(saved_files)} files")
        
        if not saved_files:
            return jsonify({'error': 'No valid files uploaded'}), 400
            
        # Analyze images
        try:
            analysis, ratings, recommendation = analyze_images_with_gemini(saved_files, faculty_name, course_codes if course_codes else None)
            if not analysis:
                return jsonify({'error': 'Failed to analyze images'}), 500
                
            # Add faculty to database
            response = requests.post('http://localhost:5001/api/faculty/add', 
                json={
                    'name': faculty_name,
                    'department': 'Computer Science'  # You can make this configurable if needed
                }
            )
            
            if response.status_code == 200:
                faculty_id = response.json()['faculty_id']
                
                # Add review
                review_data = {
                    'course_code': course_codes[0] if course_codes else 'UNKNOWN',  # Default to UNKNOWN if no course code
                    'ratings': ratings,
                    'feedback': analysis,
                    'recommendation': recommendation,
                    'source_type': 'gemini_analysis'
                }
                
                review_response = requests.post(
                    f'http://localhost:5001/api/faculty/{faculty_id}/reviews',
                    json=review_data
                )
                
                if review_response.status_code != 200:
                    logging.error(f"Error adding review: {review_response.text}")
                    return jsonify({'error': 'Failed to add review'}), 500
            else:
                logging.error(f"Error adding faculty: {response.text}")
                return jsonify({'error': 'Failed to add faculty'}), 500
            
            # Format the analysis for display
            formatted_analysis = f"""Faculty Review Analysis
===========================
FACULTY REVIEW: {faculty_name}
Course: {course_codes[0] if course_codes else 'All Courses'}
===========================

DETAILED RATINGS FOR {faculty_name}:
1. Teaching effectiveness: {ratings['teaching_effectiveness']}/5
2. Student engagement: {ratings['student_engagement']}/5
3. Clarity of presentation: {ratings['clarity']}/5
4. Overall professionalism: {ratings['professionalism']}/5

===========================
OVERALL RATING FOR {faculty_name}: {ratings['overall']}/5
===========================

{analysis}

FINAL RECOMMENDATION:
{recommendation}
==========================="""
                    
            # Return the formatted analysis
            return jsonify({'analysis': formatted_analysis})
            
        except Exception as e:
            logging.error(f"Error analyzing images: {str(e)}")
            return jsonify({'error': f'Error analyzing images: {str(e)}'}), 500
        finally:
            # Clean up saved files
            for filepath in saved_files:
                try:
                        os.remove(filepath)
                except Exception as e:
                    logging.error(f"Error removing file {filepath}: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error in analyze route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_reviews/<faculty_name>', methods=['POST'])
def delete_reviews(faculty_name):
    """Delete all reviews for a faculty member"""
    try:
        # Delete reviews using the new endpoint
        delete_response = requests.post(f'http://localhost:5001/api/faculty/{faculty_name}/reviews/delete')
        
        if delete_response.status_code == 404:
            return jsonify({'error': 'Faculty not found'}), 404
        elif delete_response.status_code != 200:
            return jsonify({'error': 'Failed to delete reviews'}), 500
            
        return jsonify(delete_response.json())
        
    except Exception as e:
        logging.error(f"Error deleting reviews: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_faculty/<faculty_name>', methods=['POST'])
def delete_faculty(faculty_name):
    """Delete a faculty member and all their reviews"""
    try:
        # Get faculty ID from the database
        response = requests.get(f'http://localhost:5001/api/faculty/search/{faculty_name}')
        if response.status_code != 200:
            return jsonify({'error': 'Faculty not found'}), 404
            
        faculty_id = response.json()['faculty_id']
        
        # Delete the faculty (this will cascade delete all reviews)
        delete_response = requests.delete(f'http://localhost:5001/api/faculty/{faculty_id}')
        if delete_response.status_code != 200:
            return jsonify({'error': 'Failed to delete faculty'}), 500
            
        return jsonify({'message': f'Successfully deleted faculty {faculty_name} and all their reviews'})
        
    except Exception as e:
        logging.error(f"Error deleting faculty: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete-faculty')
def delete_faculty_page():
    """Serve the delete faculty page"""
    return render_template('delete_faculty.html')

@app.route('/api/faculty/<int:fid>/delete', methods=['GET', 'DELETE'])
def delete_faculty_by_id(fid):
    """Delete a faculty member by ID"""
    faculty_id = fid
    try:
        if request.method == 'GET':
            # For GET requests, show a confirmation page
            return render_template('confirm_delete.html', faculty_id=faculty_id)
        # For DELETE requests, delete the faculty
        # First verify the faculty exists
        check_response = requests.get(f'http://localhost:5001/api/faculty/{faculty_id}')
        if check_response.status_code == 404:
            return jsonify({'error': f'Faculty with ID {faculty_id} not found'}), 404
        # Delete the faculty's reviews first
        try:
            reviews_response = requests.delete(f'http://localhost:5001/api/faculty/{faculty_id}/reviews')
            if reviews_response.status_code != 200:
                logging.error(f"Failed to delete reviews: {reviews_response.text}")
                # Continue with faculty deletion even if reviews deletion fails
                logging.warning("Continuing with faculty deletion despite review deletion failure")
        except Exception as e:
            logging.error(f"Error deleting reviews: {str(e)}")
            # Continue with faculty deletion even if reviews deletion fails
            logging.warning("Continuing with faculty deletion despite review deletion error")
        # Then delete the faculty
        delete_response = requests.delete(f'http://localhost:5001/api/faculty/{faculty_id}')
        logging.info(f"Delete response: {delete_response.status_code} - {delete_response.text}")
        if delete_response.status_code == 404:
            return jsonify({'error': f'Faculty with ID {faculty_id} not found'}), 404
        elif delete_response.status_code != 200:
            error_msg = f"Failed to delete faculty: {delete_response.text}"
            logging.error(error_msg)
            return jsonify({'error': error_msg}), 500
        return jsonify({
            'success': True,
            'message': f'Successfully deleted faculty with ID {faculty_id}',
            'faculty_id': faculty_id
        })
    except Exception as e:
        error_msg = f"Error deleting faculty: {str(e)}"
        logging.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/faculty', methods=['GET'])
def list_faculty():
    """List all faculty members"""
    try:
        # Get faculty list from the database
        response = requests.get('http://localhost:5001/api/faculty')
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch faculty list'}), 500
            
        return jsonify(response.json())
            
    except Exception as e:
        logging.error(f"Error listing faculty: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/faculty/<int:faculty_id>', methods=['GET'])
def get_faculty(faculty_id):
    """Get a specific faculty member by ID"""
    try:
        # Get faculty from the database
        response = requests.get(f'http://localhost:5001/api/faculty/{faculty_id}')
        
        if response.status_code == 404:
            return jsonify({'error': f'Faculty with ID {faculty_id} not found'}), 404
        elif response.status_code != 200:
            return jsonify({'error': f'Failed to fetch faculty with ID {faculty_id}'}), 500
            
        return jsonify(response.json())
        
    except Exception as e:
        logging.error(f"Error getting faculty: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/routes')
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:30s} {methods:20s} {str(rule)}")
        output.append(line)
    return "<pre>" + "\n".join(output) + "</pre>"

if __name__ == '__main__':
    app.run(debug=True) 