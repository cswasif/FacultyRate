import sqlite3

def cleanup_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('faculty_ratings.db')
        cursor = conn.cursor()
        
        # First, let's identify unique reviews by creating a temporary table
        cursor.execute('''
            CREATE TEMPORARY TABLE temp_reviews AS
            SELECT MIN(id) as id
            FROM reviews
            WHERE source_type = 'screenshot_analysis'
            GROUP BY course_code, teaching_effectiveness, student_engagement, 
                     clarity, professionalism, feedback
        ''')
        
        # Delete all screenshot analysis reviews that are not in our temp table
        cursor.execute('''
            DELETE FROM reviews 
            WHERE source_type = 'screenshot_analysis'
            AND id NOT IN (SELECT id FROM temp_reviews)
        ''')
        
        # Commit the changes
        conn.commit()
        
        # Get the count of remaining reviews
        cursor.execute('''
            SELECT COUNT(*) 
            FROM reviews 
            WHERE source_type = 'screenshot_analysis'
        ''')
        remaining_count = cursor.fetchone()[0]
        
        print(f"Cleanup completed successfully!")
        print(f"Number of screenshot analysis reviews after cleanup: {remaining_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    cleanup_database() 