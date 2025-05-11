from fpdf import FPDF

# Create instance of FPDF class
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Title
pdf.cell(200, 10, txt="Environmental Monitoring Report", ln=True, align='C')

# Add summary
pdf.ln(10)
pdf.cell(200, 10, txt="Summary of NDVI Analysis", ln=True)
pdf.multi_cell(0, 10, "Your summary and findings go here...")

# Add statistics
pdf.ln(5)
pdf.cell(200, 10, txt="NDVI Statistics", ln=True)
pdf.cell(200, 10, txt="NDVI Mean: 0.45", ln=True)
pdf.cell(200, 10, txt="NDVI StdDev: 0.12", ln=True)

# Add more sections as needed...

# Save the PDF
pdf.output("NDVI_Report.pdf")
