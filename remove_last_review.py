import sqlite3

def remove_last_review():
    try:
        # Connect to the database
        conn = sqlite3.connect('faculty_ratings.db')
        cursor = conn.cursor()
        
        # Get the most recent review id
        cursor.execute('''
            SELECT id FROM reviews 
            WHERE source_type = 'screenshot_analysis'
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        last_review = cursor.fetchone()
        if last_review:
            # Delete the most recent review
            cursor.execute('DELETE FROM reviews WHERE id = ?', (last_review[0],))
            conn.commit()
            print(f"Successfully removed the last review (ID: {last_review[0]})")
        else:
            print("No reviews found to remove")
        
    except Exception as e:
        print(f"Error removing review: {str(e)}")
        conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    remove_last_review() 