import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw headers/footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Draw Title Page background/border
        if self._pageNumber == 1:
            self.setStrokeColor(colors.HexColor("#2C3E50"))
            self.setLineWidth(2)
            self.rect(36, 36, 540, 720) # 0.5 in margins
            return

        # Draw Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#2C3E50"))
        self.drawString(54, 750, "SECURE PROGRAMMING - EXERCISE 3 SOLUTION REPORT")
        self.setStrokeColor(colors.HexColor("#BDC3C7"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Draw Footer
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        self.drawRightString(558, 36, f"Page {self._pageNumber} of {page_count}")
        self.drawString(54, 36, "Academic Submission - Confidential")
        self.setStrokeColor(colors.HexColor("#BDC3C7"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)


def get_report_data():
    """
    Helper function returns the structured content for the report.
    We will append other sections to this function as we progress!
    """
    data = {}
    
    # -------------------------------------------------------------
    # SECTION A CONTENT
    # -------------------------------------------------------------
    data["section_a"] = {
        "title": "A. Adding a Digital Certificate (HTTPS Setup)",
        "intro": (
            "This section details the design, configuration, and implementation of a locally trusted "
            "HTTPS (SSL/TLS) environment for the <b>XSSApp</b> website. The implementation ensures that "
            "the server uses a logical domain name (<b>xssapp.local</b>) and that modern browsers (specifically "
            "Chrome 85 and above) recognize the SSL certificate as fully secure without displaying any warnings."
        ),
        "why_san_matters_title": "Why Standard Self-Signed Certificates Fail in Modern Chrome",
        "why_san_matters_desc": (
            "Historically, browsers validated certificates using the <b>Common Name (CN)</b> field (e.g., CN=localhost). "
            "However, starting with Chrome 58 and strictly enforced in version 85+, Google deprecated and removed support "
            "for Common Name matching. Chrome now exclusively validates the server identity using the "
            "<b>Subject Alternative Name (SAN)</b> extension. If the SAN extension is missing or does not match the active "
            "hostname, Chrome raises a <code>NET::ERR_CERT_COMMON_NAME_INVALID</code> error, even if the certificate is signed "
            "by a trusted root authority."
        ),
        "steps": [
            {
                "name": "1. Named Host Configuration",
                "desc": (
                    "To satisfy the requirement of a 'logical/valid name', we mapped a custom domain to our local loopback interface. "
                    "This was done by editing the Windows hosts file (<code>C:\\Windows\\System32\\drivers\\etc\\hosts</code>) and adding the "
                    "following entry mapping the local loopback to our logical hostname:<br/>"
                    "<code>127.0.0.1    xssapp.local</code>"
                )
            },
            {
                "name": "2. Creating the OpenSSL Configuration (openssl.cnf)",
                "desc": (
                    "To generate a certificate with the required SAN extension, we created an OpenSSL configuration file named "
                    "<code>openssl.cnf</code>. This file explicitly requests the <b>subjectAltName</b> extension to contain both our "
                    "logical domain name and the local loopback IP address (ensuring fallback compatibility):"
                ),
                "code": (
                    "[req]\n"
                    "distinguished_name = req_distinguished_name\n"
                    "x509_extensions = v3_req\n"
                    "prompt = no\n\n"
                    "[req_distinguished_name]\n"
                    "C = US\n"
                    "ST = State\n"
                    "L = City\n"
                    "O = Organization\n"
                    "CN = xssapp.local\n\n"
                    "[v3_req]\n"
                    "keyUsage = keyCertSign, cRLSign, digitalSignature, keyEncipherment\n"
                    "extendedKeyUsage = serverAuth\n"
                    "subjectAltName = @alt_names\n\n"
                    "[alt_names]\n"
                    "DNS.1 = xssapp.local\n"
                    "IP.1 = 127.0.0.1"
                )
            },
            {
                "name": "3. Generating Key and Certificate Pair",
                "desc": (
                    "Using the OpenSSL executable found inside the local Git installation, we ran the following command to "
                    "generate a new 2048-bit RSA private key (<code>key.pem</code>) and a self-signed X.509 certificate (<code>cert.pem</code>) "
                    "valid for 365 days using our configuration file:"
                ),
                "code": (
                    'openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -config openssl.cnf'
                )
            },
            {
                "name": "4. Installing and Trusting the Certificate in Windows Store",
                "desc": (
                    "Even with a valid SAN, Chrome will reject the certificate because it is self-signed and does not chain up to a "
                    "trusted certificate authority. To establish trust, we imported the certificate (<code>cert.pem</code>) into the Windows "
                    "<b>Trusted Root Certification Authorities</b> store for the active user using PowerShell:"
                ),
                "code": (
                    "Import-Certificate -FilePath .\\cert.pem -CertStoreLocation Cert:\\CurrentUser\\Root"
                )
            },
            {
                "name": "5. Modifying app.py to Serve HTTPS",
                "desc": (
                    "Finally, we updated the Flask server's startup routine in <code>app.py</code> to dynamically scan for "
                    "<code>cert.pem</code> and <code>key.pem</code>. If found, it automatically initializes the server in HTTPS mode using "
                    "an SSL context, binding securely to port 5000:"
                ),
                "code": (
                    "def start_app():\n"
                    "    ...\n"
                    '    cert_path = "cert.pem"\n'
                    '    key_path = "key.pem"\n'
                    "    if not (os.path.exists(cert_path) and os.path.exists(key_path)):\n"
                    "        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n"
                    '        cert_path = os.path.join(base_dir, "cert.pem")\n'
                    '        key_path = os.path.join(base_dir, "key.pem")\n\n'
                    "    if os.path.exists(cert_path) and os.path.exists(key_path):\n"
                    '        app.logger.info("Starting server with HTTPS...")\n'
                    "        app.run(host=\"0.0.0.0\", port=5000, ssl_context=(cert_path, key_path))\n"
                    "    else:\n"
                    '        app.logger.info("Starting server with HTTP...")\n'
                    "        app.run(host=\"0.0.0.0\", port=5000)"
                )
            }
        ]
    }
    
    # Placeholder for subsequent sections
    # data["section_c"] = ...
    # data["section_d"] = ...
    # data["section_e"] = ...
    # data["section_f_g"] = ...

    return data


def build_pdf(filename="Exercise_3_Solution_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54, # 0.75 in margin
        rightMargin=54,
        topMargin=72, # 1.0 in margin
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#2C3E50")  # Slate Blue
    c_secondary = colors.HexColor("#16A085") # Teal Accent
    c_dark = colors.HexColor("#34495E")      # Body text
    c_code_bg = colors.HexColor("#F8F9F9")   # Soft gray
    c_border = colors.HexColor("#E5E7E9")    # Light borders

    # Custom Typographical Styles
    style_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=15
    )

    style_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_dark,
        alignment=1, # Center
        spaceAfter=40
    )

    style_meta = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=c_primary,
        alignment=1, # Center
    )

    style_h1 = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_dark,
        spaceAfter=8
    )

    style_code = ParagraphStyle(
        "Code_Custom",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=4,
        spaceAfter=4
    )

    story = []

    # =============================================================
    # COVER PAGE
    # =============================================================
    story.append(Spacer(1, 150))
    story.append(Paragraph("SECURE PROGRAMMING", style_subtitle))
    story.append(Paragraph("EXERCISE 3 SOLUTION REPORT", style_title))
    
    # Decorative colored horizontal bar
    t_bar = Table([[""]], colWidths=[200], rowHeights=[4])
    t_bar.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_secondary),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_bar)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Configuring HTTPS, Secure Auditing, and Code Vulnerability Remediation", style_subtitle))
    story.append(Spacer(1, 150))
    
    # Meta Box
    meta_data = [
        [Paragraph("Submission Date:", style_body), Paragraph("June 02, 2026", style_meta)],
        [Paragraph("Course:", style_body), Paragraph("Secure Programming - Assignment 3", style_meta)],
        [Paragraph("Status:", style_body), Paragraph("Task A Complete - In Progress", style_meta)],
    ]
    t_meta = Table(meta_data, colWidths=[110, 150])
    t_meta.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7E9")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    
    # Center-align the table on cover page
    t_meta_outer = Table([[t_meta]], colWidths=[260])
    t_meta_outer.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_meta_outer)
    
    story.append(PageBreak())

    # =============================================================
    # TABLE OF CONTENTS / INTRO
    # =============================================================
    story.append(Paragraph("Report Outline", style_h1))
    story.append(Spacer(1, 5))
    
    outline_data = [
        [Paragraph("<b>Section</b>", style_meta), Paragraph("<b>Status</b>", style_meta), Paragraph("<b>Page</b>", style_meta)],
        [Paragraph("A. Adding a Digital Certificate (HTTPS Setup)", style_body), Paragraph("COMPLETED", style_meta), Paragraph("3", style_body)],
        [Paragraph("C. Analysis of &lt;object&gt; Tag Restrictions", style_body), Paragraph("PENDING", style_body), Paragraph("-", style_body)],
        [Paragraph("D. Codebase Vulnerability Remediation", style_body), Paragraph("PENDING", style_body), Paragraph("-", style_body)],
        [Paragraph("E, F, G. Advanced Cyber Security Concepts", style_body), Paragraph("PENDING", style_body), Paragraph("-", style_body)],
    ]
    t_outline = Table(outline_data, colWidths=[300, 120, 80])
    t_outline.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_code_bg),
        ('LINEBELOW', (0,0), (-1,0), 1.5, c_primary),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_outline)
    story.append(Spacer(1, 20))
    
    # =============================================================
    # SECTION A: HTTPS SETUP
    # =============================================================
    data = get_report_data()
    sec_a = data["section_a"]
    
    story.append(PageBreak())
    story.append(Paragraph(sec_a["title"], style_h1))
    story.append(Paragraph(sec_a["intro"], style_body))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(sec_a["why_san_matters_title"], style_h2))
    story.append(Paragraph(sec_a["why_san_matters_desc"], style_body))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Implementation Checklist & Walkthrough", style_h2))
    
    for step in sec_a["steps"]:
        elements = []
        elements.append(Paragraph(f"<b>{step['name']}</b>", style_h2))
        elements.append(Paragraph(step["desc"], style_body))
        
        if "code" in step:
            # Code box styling
            code_lines = step["code"].split('\n')
            code_paragraphs = [Paragraph(line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;'), style_code) for line in code_lines]
            
            # Wrap code inside a single cell table with a light background and border
            t_code = Table([[code_paragraphs]], colWidths=[500])
            t_code.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), c_code_bg),
                ('BOX', (0,0), (-1,-1), 0.5, c_border),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(Spacer(1, 5))
            elements.append(t_code)
            
        elements.append(Spacer(1, 15))
        story.append(KeepTogether(elements))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully: {filename}")


if __name__ == "__main__":
    build_pdf()
