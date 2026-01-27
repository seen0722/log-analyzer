import os
import subprocess
import markdown

def generate_pdf_report(markdown_content, session_id, report_dir):
    """
    Generates HTML and PDF reports from the markdown content.
    Returns the filenames of the generated reports.
    """
    base_name = f"RCA_Report_{session_id}"
    md_path = os.path.join(report_dir, f"{base_name}.md")
    html_path = os.path.join(report_dir, f"{base_name}.html")
    pdf_path = os.path.join(report_dir, f"{base_name}.pdf")
    
    # 1. Save Markdown
    with open(md_path, "w") as f:
        f.write(markdown_content)
        
    # 2. Convert to HTML with Custom Styling
    css_url = f"file://{os.path.abspath('static/report.css')}"
    
    # We will build a complete HTML file manually to ensure styles are applied
    html_body = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="{css_url}">
        <style>
           /* Fallback if file link fails (though Headless Chrome usually handles it) */
           body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; }}
        </style>
    </head>
    <body class="report-body">
        {html_body}
    </body>
    </html>
    """
    
    with open(html_path, "w") as f:
        f.write(html_template)
            
    # 3. Convert to PDF (using Headless Chrome)
            
    # 3. Convert to PDF (using Headless Chrome)
    # This assumes Chrome is installed at the standard macOS location
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    if os.path.exists(chrome_path):
        try:
             subprocess.run([
                chrome_path,
                "--headless",
                "--disable-gpu",
                f"--print-to-pdf={pdf_path}",
                f"file://{html_path}"
             ], check=True)
        except Exception as e:
            print(f"PDF Generation failed: {e}")
            pass # PDF might fail if chrome not found/working, but at least we have MD/HTML
            
    return {
        "md": f"{base_name}.md",
        "html": f"{base_name}.html",
        "pdf": f"{base_name}.pdf" if os.path.exists(pdf_path) else None
    }
