import os
import csv

def create_faculty_list():
    """Create a CSV file with faculty information"""
    faculty_data = [
        ["Name", "Department", "Drive_Folder_Link", "Courses"],
        ["ARD", "Computer Science", "", "CSE330, CSE101, CSE440"],
        # Add more faculty here
    ]
    
    with open('faculty_tracking.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(faculty_data)
        
def print_folder_structure():
    """Print the recommended Google Drive folder structure"""
    structure = """
📁 FacultyRate Screenshots
├── 📁 ARD
│   ├── 📄 README.txt
│   ├── 📸 CSE330_2024_01.png
│   ├── 📸 CSE330_2024_02.png
│   ├── 📸 CSE101_2024_01.png
│   └── 📸 CSE440_2024_01.png
├── 📁 [Another Faculty Name]
│   ├── 📄 README.txt
│   ├── 📸 COURSE1_2024_01.png
│   └── 📸 COURSE2_2024_01.png
└── 📁 [Other Faculty]

Naming Convention:
- Screenshots: COURSECODE_YEAR_NUMBER.png
- Example: CSE330_2024_01.png

README.txt content for each faculty folder:
-------------------------------------------
Faculty Name: [Name]
Department: [Department]

Courses Found:
1. [Course Code] - [Semester/Year]
2. [Course Code] - [Semester/Year]
3. [Course Code] - [Semester/Year]

Total Screenshots: [Number]
Last Updated: [Date]

Progress:
□ Screenshots collected
□ Uploaded to system
□ Reviews verified
-------------------------------------------
"""
    print(structure)

def create_sample_structure():
    """Create a sample local folder structure"""
    base_dir = "drive_structure_sample"
    
    # Create base directory
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # Create faculty folder
    faculty_dir = os.path.join(base_dir, "ARD")
    if not os.path.exists(faculty_dir):
        os.makedirs(faculty_dir)
    
    # Create README
    readme_content = """Faculty Name: ARD
Department: Computer Science

Courses Found:
1. CSE330 - Spring 2024
2. CSE101 - Spring 2024
3. CSE440 - Spring 2024

Total Screenshots: 4
Last Updated: 2024-03-20

Progress:
□ Screenshots collected
□ Uploaded to system
□ Reviews verified
"""
    
    with open(os.path.join(faculty_dir, "README.txt"), 'w') as f:
        f.write(readme_content)
    
    # Create sample screenshot files (just create empty files)
    sample_files = [
        "CSE330_2024_01.png",
        "CSE330_2024_02.png",
        "CSE101_2024_01.png",
        "CSE440_2024_01.png"
    ]
    
    for file in sample_files:
        open(os.path.join(faculty_dir, file), 'a').close()
    
    print(f"\nSample structure created in '{base_dir}' folder!")

if __name__ == "__main__":
    print("Creating folder structure for FacultyRate Screenshots...")
    create_faculty_list()
    print_folder_structure()
    create_sample_structure()
    print("\nDone! You can use this structure to organize your Google Drive folders.")
    print("A tracking CSV file 'faculty_tracking.csv' has been created to help monitor progress.") 