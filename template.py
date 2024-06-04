import subprocess
import os

def check_pdflatex():
    try:
        result = subprocess.run(['pdflatex', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def populate_template(template_path, output_path, content_dict):
    with open(template_path, 'r') as file:
        template_content = file.read()

    for placeholder, value in content_dict.items():
        template_content = template_content.replace(placeholder, value)

    with open(output_path, 'w') as file:
        file.write(template_content)

def generate_pdf(latex_file_path, output_dir):
    try:
        result = subprocess.run(['pdflatex', latex_file_path], cwd=output_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("PDF generated successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to generate PDF:", e)

def main():
    try:
        if not check_pdflatex():
            print("pdflatex not found. Please install LaTeX distribution (e.g., MacTeX for macOS, MiKTeX for Windows, TeX Live for Linux).")
            return

        name = "Jake Li"
        major_list = "Sports Medicine, Rehabilitation Science, Biological Sciences"
        word_cloud_file_path = "/Users/nurizaurulbaeva/Desktop/Jake_Li_word_cloud.png"
        output_dir = "/Users/nurizaurulbaeva/Desktop"
        latex_template_path = os.path.join(output_dir, 'pro[1].tex')
        latex_output_path = os.path.join(output_dir, 'filled_template.tex')

        generated_content = {
            "%name%": name,
            "%image%": word_cloud_file_path,
            "%generated_summary%": "Generated summary...",
            "%generated_major_prompt_two%": "Generated major prompt two...",
            "%generated_major_prompt_three%": "Generated major prompt three...",
            "%major_list%": major_list,
            "%generated_potential_major%": "Generated potential major...",
            "%generated_Correspondence_college_recommendations%": "Generated Correspondence college recommendations...",
            "%generated_Correspondence_Courses%": "Generated Correspondence Courses...",
            "%generated_Major_development_history%": "Generated Major development history...",
            "%generated_Cutting_edge_field%": "Generated Cutting edge field...",
            "%generated_visualization_p3%": "Generated visualization p3...",
            "%generated_Highschool_activities%": "Generated Highschool activities..."
        }

        # Populate the LaTeX template
        populate_template(latex_template_path, latex_output_path, generated_content)

        # Generate the PDF
        generate_pdf(latex_output_path, output_dir)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
