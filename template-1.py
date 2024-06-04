import pandas as pd
from fpdf import FPDF

# Load data from Excel
data = pd.read_excel('form_eng.xlsx')

# Create instance of FPDF class and add a page
pdf = FPDF()
pdf.add_page()

# Add Unicode font
pdf.add_font('DejaVuSerif', '', '/Users/nurizaurulbaeva/Desktop/dejavu-fonts-ttf2/ttf/DejaVuSerif.ttf', uni=True)
pdf.set_font('DejaVuSerif', '', 14)

# Set initial y position
y = 50

# Iterate over DataFrame rows
for index, row in data.iterrows():
    # Assuming the Excel file has columns 'Name', 'Age', and 'Comments'
    pdf.set_xy(10, y)
    text = f"Name: {row['Student English name（ex：Eric Zhang or Runxin Zhang）Student Name (First Name + Last Name)']}, Age: {row['Grade Level']}"
    pdf.cell(200, 10, txt=text, ln=True)
    y += 10  # Move to the next line

# Save the PDF to a file on the Desktop
desktop_path = '/Users/nurizaurulbaeva/Desktop/'  # Replace 'YourUsername' with your actual username
pdf.output(desktop_path)

print("PDF generated successfully on your Desktop!")
