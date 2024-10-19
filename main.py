import pandas as pd
import os
import re
import cv2
import csv
import numpy as np
import glob

# Path to your Excel file
excel_file_path = 'dataset.xlsx'

# Read the Excel file
df = pd.read_excel(excel_file_path)

# Extract the repository URLs
urls = df['Repository URL'].tolist()

# Create a folder to store the projects
folder_name = 'JavaProjects'
os.makedirs(folder_name, exist_ok=True)

# Iterate over the project links and download the repository
for link in urls:
    # Extract the repository name from the URL
    repo_name = link.split('/')[-1].replace('.git', '')
    
    # Define the path to the project folder
    project_folder = os.path.join(folder_name, repo_name)
    
    # Clone the repository into the project folder
    os.system(f"git clone {link} {project_folder}")
    print(f"Downloaded: {link}")

print("All projects downloaded successfully!")

# -------------------------------------------------------------

def java_to_puml(java_file, output_directory):
    with open(java_file, 'r') as file:
        java_code = file.read()

    puml_code = "@startuml\n"

    # Extract class names
    class_names = re.findall(r"class\s+(\w+)", java_code)

    # Generate class diagrams
    for class_name in class_names:
        puml_code += f"class {class_name}\n"

    # Extract associations
    associations = re.findall(r"(\w+)\s+(\w+)\s*;", java_code)

    # Generate association relationships
    for association in associations:
        puml_code += f"{association[0]} -- {association[1]}\n"

    puml_code += "@enduml\n"

    puml_file = os.path.splitext(os.path.basename(java_file))[0] + '.puml'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_path = os.path.join(output_directory, puml_file)

    with open(output_path, 'w') as file:
        file.write(puml_code)


def convert_java_files(java_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for root, _, files in os.walk(java_directory):
        for file in files:
            if file.endswith('.java'):
                java_file = os.path.join(root, file)
                
                # Split the path using the directory separator ("/" on Unix-like systems)
                parts = java_file.split(os.path.sep)
            
                # Find the index of the element containing "JavaProjects"
                java_projects_index = parts.index("JavaProjects")
            
                # Extract the project name
                project_name = parts[java_projects_index + 1]

                print("Project:", project_name, "Java File:", java_file)
                java_to_puml(java_file, output_directory + "/" + project_name)


# Example usage
java_directory = 'JavaProjects'
output_directory = 'pumlFiles'

convert_java_files(java_directory, output_directory)

#------------------------------------------------------

# Directory containing .puml files
directory = "pumlFiles"

# Output directory for .png files
output_directory = "pngOutput"
os.makedirs(output_directory, exist_ok=True)

# Iterate over files in the directory
for root, _, files in os.walk(directory):
    for filename in files:
        if filename.endswith('.puml'):
            # Generate .png file
            puml_file = os.path.join(root, filename)
            png_file = os.path.splitext(filename)[0] + ".png"
            png_path = os.path.join(output_directory, png_file)
            # Modified command to include output directory
            command = f"plantuml -o {output_directory} {puml_file}"
            os.system(command)
            
            print(f"Generated {png_path}")


#-----------------------------------------------------------


# Directory containing project folders
main_directory = "pumlFiles"

# List to store project results
project_results = []

# Iterate over project folders
for project in os.listdir(main_directory):
    project_path = os.path.join(main_directory, project)
    
    if os.path.isdir(project_path):
        # Look for 'pngOutput' folder inside the project folder
        png_output_path = os.path.join(project_path, "pngOutput")
        if os.path.isdir(png_output_path):
            # Initialize counters for each project
            project_associations = 0
            
            # Iterate over PNG files in the 'pngOutput' folder
            for root, _, files in os.walk(png_output_path):
                for filename in files:
                    if filename.endswith('.png'):
                        image_path = os.path.join(root, filename)
                        image = cv2.imread(image_path)
                        
                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        edges = cv2.Canny(gray, 50, 150)
                        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)
                        
                        num_associations = 0
                        if lines is not None:
                            for line in lines:
                                x1, y1, x2, y2 = line[0]
                                if abs(x2 - x1) > 20 or abs(y2 - y1) > 20:
                                    num_associations += 1
                            project_associations += num_associations
            
            # Store the project result
            project_result = (project, project_associations)
            project_results.append(project_result)

# Save project results to a CSV file
csv_file = "associations.csv"
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Project", "Total Number of Associations"])
    writer.writerows(project_results)

print(f"Project results saved to {csv_file}")


# ------------------------------------------------------------- Up to PlantUML


def count_functions(java_project_dir):
    def find_main_file(project_dir):
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    if contains_main_method(file_path):
                        return file_path

        raise FileNotFoundError("Main Java file not found in the project directory.")

    def contains_main_method(java_file_path):
        with open(java_file_path, 'r') as file:
            java_code = file.read()

        pattern = r"public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s+\w*\s*\)\s*\{"
        return re.search(pattern, java_code) is not None

    # Add code to find the main Java file in the project directory
    main_file_path = find_main_file(java_project_dir)

    with open(main_file_path, 'r') as file:
        java_code = file.read()

    pattern = r"(public|private|protected|static|\s) [\w<>,\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{"
    matches = re.findall(pattern, java_code)
    return len(matches)


java_project_dirs = glob.glob('JavaProjects/*')  # Assumes 'JavaProjects' folder contains the Java projects

csv_file = 'function_counts.csv'  # Name of the CSV file to save the results
header = ['Project', 'Number of Functions']
rows = []

for project_dir in java_project_dirs:
    try:
        num_functions = count_functions(project_dir)
        project_name = os.path.basename(project_dir)
        rows.append([project_name, num_functions])
        print(f"Project: {project_name}, Number of functions: {num_functions}")
    except FileNotFoundError as e:
        print(f"Project: {project_dir}, Error: {str(e)}")

# Save the results to a CSV file
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(rows)

print(f"Function counts saved to {csv_file}")
