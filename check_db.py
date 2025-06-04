import sqlite3

def check_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('faculty_ratings.db')
        cursor = conn.cursor()
        
        # Query for screenshot analysis reviews
        cursor.execute('''
            SELECT course_code, teaching_effectiveness, student_engagement, 
                   clarity, professionalism, feedback, source_type 
            FROM reviews 
            WHERE source_type = ?
        ''', ('screenshot_analysis',))
        
        rows = cursor.fetchall()
        
        print(f'Number of screenshot analysis reviews: {len(rows)}')
        
        for row in rows:
            print(f'\nReview for course {row[0]}:')
            print(f'Teaching: {row[1]}')
            print(f'Engagement: {row[2]}')
            print(f'Clarity: {row[3]}')
            print(f'Professionalism: {row[4]}')
            print(f'Feedback: {row[5]}')
            print(f'Source: {row[6]}')
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database() 