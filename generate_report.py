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
    
    # -------------------------------------------------------------
    # SECTION B CONTENT
    # -------------------------------------------------------------
    data["section_b"] = {
        "title": "B. Stored XSS & Parser Discrepancies",
        "intro": (
            "This section details the theoretical analysis and architectural design of a Stored Cross-Site "
            "Scripting (XSS) attack on the <b>XSSApp</b> website. The analysis explores how a vulnerability "
            "emerges from a parser discrepancy between server-side HTML validators and browser rendering engines, "
            "allowing a low-privileged user to impersonate the administrator and execute privileged actions (such as data deletion)."
        ),
        "parser_discrepancy_title": "The Flaw: BeautifulSoup vs. Browser DOM Reconstruction",
        "parser_discrepancy_desc": (
            "The root vulnerability lies in <code>validation_utilities.validate_message()</code>. The function attempts "
            "to validate user input by parsing it with BeautifulSoup (using Python's built-in <code>html.parser</code>) "
            "and checking for the presence of <code>&lt;script&gt;</code> tags or any attributes starting with <code>on</code> "
            "(event handlers like <code>onerror</code>).<br/><br/>"
            "This validation approach introduces a severe **parser discrepancy**:<br/>"
            "1. **BeautifulSoup's Strict Parsing**: When given highly broken or malformed HTML tags (such as unclosed brackets, "
            "unusual slashes, or nested tags like <code>&lt;&lt;script&gt;alert(1)&lt;/script&gt;</code>), Python's strict "
            "<code>html.parser</code> frequently fails to resolve the malformed segments as standard elements. Consequently, "
            "BeautifulSoup does not register them as active tags or find any attributes matching the blacklist, allowing the "
            "string to pass validation.<br/>"
            "2. **Browser's Lenient Normalization**: When the browser (e.g., Chrome's Blink engine) receives the raw "
            "malformed string, it uses highly permissive error-recovery algorithms to reconstruct a valid Document Object Model (DOM). "
            "Chrome successfully normalizes the malformed markup, closes the unclosed brackets, and renders/executes the "
            "resulting JavaScript payload."
        ),
        "attack_flow_title": "Conceptual Attack Architecture",
        "steps": [
            {
                "name": "1. Storing the Payload (Stored/Persistent Vector)",
                "desc": (
                    "A low-privileged ('weak') user posts a contact request containing the malformed HTML payload. "
                    "Because the payload bypasses the BeautifulSoup blacklist, the server accepts the input and "
                    "stores it raw in the global <code>messages</code> database."
                )
            },
            {
                "name": "2. Insecure Rendering Context",
                "desc": (
                    "When the administrator logs in and views the homepage (<code>/</code>), the Flask application "
                    "fetches the stored messages. Because the message is wrapped in <code>Markup</code> (which disables "
                    "Jinja2 auto-escaping), the server transmits the raw malformed string directly to the admin's browser."
                )
            },
            {
                "name": "3. Execution & Impersonation (Session Riding / Hijacking)",
                "desc": (
                    "The administrator's browser parses the malformed string, normalizes it, and executes the injected script "
                    "within the active administrative session. The script executes same-origin requests (e.g., using "
                    "<code>fetch('/drop_all_messages')</code>) in the background. Since the browser automatically includes "
                    "the administrator's session cookie, the server authenticates the request and executes the administrative "
                    "command, successfully deleting all messages on behalf of the low-privileged user."
                )
            },
            {
                "name": "4. Listening Server Backend (High-Level Design)",
                "desc": (
                    "If the session cookie lacks <code>HttpOnly</code>, the injected script can exfiltrate the token value "
                    "to a local listening server. The listener can be structured conceptually as a basic HTTP server "
                    "(using Python's <code>http.server</code> or the <code>requests</code> library) that logs incoming "
                    "GET parameters. For example:<br/>"
                    "<code>python -m http.server 8080</code><br/>"
                    "The XSS payload sends the session identifier to the listener: <code>http://127.0.0.1:8080/?cookie=value</code>. "
                    "The attacker logs the token, imports it into their browser, and gains full administrative persistence."
                )
            }
        ]
    }

    # -------------------------------------------------------------
    # SECTION C CONTENT
    # -------------------------------------------------------------
    data["section_c"] = {
        "title": "C. Analysis of &lt;object&gt; Tag Restrictions",
        "intro": (
            "This section analyzes the security restrictions applied to the HTML <code>&lt;object&gt;</code> tag "
            "when loaded with active MIME types such as <code>text/x-scriptlet</code>. We examine the theoretical "
            "mechanics of why modern web browsers systematically block cookie exfiltration attempts via this attack vector."
        ),
        "how_it_works_title": "Historical Context: HTML Scriptlets and ActiveX Control",
        "how_it_works_desc": (
            "Historically, in legacy Microsoft Internet Explorer (IE4 through IE11), <b>HTML Scriptlets</b> "
            "(defined using <code>&lt;object type=\"text/x-scriptlet\" data=\"URL\"&gt;</code>) were proprietary components "
            "allowing developers to encapsulate dynamic, scripting-capable HTML pages into reusable objects. "
            "Crucially, these objects could execute scripts directly inside the parent page's security context, allowing "
            "the embedded scriptlet document to access host elements and read <code>document.cookie</code>, bypass sandboxes, "
            "and exfiltrate session data."
        ),
        "why_it_fails_title": "Why the Attack Fails in Modern Browsers (Blink, WebKit, Gecko)",
        "reasons": [
            {
                "name": "1. Deprecation and Deletion of Legacy Technologies",
                "desc": (
                    "HTML Scriptlets and active content handlers (including Silverlight, Java Applets, and ActiveX) have been "
                    "completely deprecated and permanently removed from modern browser engines. Modern browsers (Chrome, Edge, Firefox, "
                    "and Safari) do not register or recognize the <code>text/x-scriptlet</code> MIME type. When Chrome processes "
                    "<code>&lt;object type=\"text/x-scriptlet\" data=\"...\"&gt;</code>, it ignores the proprietary scriptlet handler "
                    "entirely and treats the element as an unresolvable type, blocking all script execution."
                )
            },
            {
                "name": "2. Strict Same-Origin Policy (SOP) Boundaries",
                "desc": (
                    "Modern browsers treat standard <code>&lt;object&gt;</code>, <code>&lt;iframe&gt;</code>, and "
                    "<code>&lt;embed&gt;</code> elements as separate, nested browsing contexts (documents). Even if the embedded "
                    "object could load and execute a script internally (e.g., as a standard HTML document), the <b>Same-Origin Policy (SOP)</b> "
                    "strictly blocks any cross-document interaction unless the nested document is loaded from the exact same protocol, "
                    "domain, and port as the parent document. If loaded from an external origin, any attempt by the object's internal "
                    "script to read <code>window.parent.document.cookie</code> throws a fatal <code>DOMException</code> (Cross-Origin Blocked)."
                )
            },
            {
                "name": "3. Sandboxing and Security Policy Directives (CSP)",
                "desc": (
                    "Modern browser environments support secure sandboxing controls (e.g., CSP headers like <code>object-src 'none'</code>) "
                    "which completely restrict the instantiation of plugins or executable documents inside <code>&lt;object&gt;</code> "
                    "tags, providing a hard, client-side cryptographic barrier against plugin-based exploitation."
                )
            }
        ]
    }
    
    # -------------------------------------------------------------
    # SECTION D CONTENT
    # -------------------------------------------------------------
    data["section_d"] = {
        "title": "D. Codebase Vulnerability Remediation",
        "intro": (
            "This section presents four critical security remediation patches implemented within the "
            "<b>XSSApp</b> codebase (specifically inside <code>app.py</code>). These patches address "
            "vulnerabilities in session security, cryptographic password verification, unsafe HTML output "
            "rendering, and process-start session invalidation."
        ),
        "vulnerabilities": [
            {
                "name": "1. Hardening Session Cookies (Mitigating Session Hijacking)",
                "type": "Session Hijacking / Insecure Cookie Configuration",
                "flaw_desc": (
                    "Originally, the Flask server explicitly disabled script protection on its session cookies "
                    "by setting <code>app.config[\"SESSION_COOKIE_HTTPONLY\"] = False</code>. This critical "
                    "misconfiguration exposed the active session identifier directly to client-side scripts "
                    "via <code>document.cookie</code>, enabling immediate and complete session theft in the event "
                    "of any XSS compromise."
                ),
                "patch_desc": (
                    "To mitigate this risk, we enabled the <code>HttpOnly</code> directive. In addition, "
                    "we configured the <code>Secure</code> flag to restrict cookie transmission strictly to HTTPS "
                    "connections, and added the <code>SameSite='Lax'</code> directive to block cross-site request "
                    "forgery (CSRF) session riding attacks:"
                ),
                "code": (
                    "# Secure session cookies configuration\n"
                    "app.config[\"SESSION_COOKIE_HTTPONLY\"] = True\n"
                    "app.config[\"SESSION_COOKIE_SECURE\"] = True\n"
                    "app.config[\"SESSION_COOKIE_SAMESITE\"] = 'Lax'"
                )
            },
            {
                "name": "2. Salted Password Hashing via Scrypt KDF (Credential Protection)",
                "type": "Insecure Password Hashing & Static Comparisons",
                "flaw_desc": (
                    "The administrator password check originally used a simple unsalted SHA-256 hash comparison. "
                    "Unsalted hashes are highly vulnerable to rapid precomputation attacks using offline dictionary lists "
                    "or pre-compiled rainbow tables. In addition, the static password hash was hardcoded directly in "
                    "the source code."
                ),
                "patch_desc": (
                    "We replaced the unsalted SHA-256 check with Werkzeug's secure key derivation functions. "
                    "We generated a salted scrypt hash of the administrator password (utilizing 32,768 work iterations, "
                    "a block size of 8, and a parallelization factor of 1) and integrated <code>check_password_hash</code> "
                    "to perform cryptographically secure comparisons that are highly resistant to offline brute-force attacks:"
                ),
                "code": (
                    "from werkzeug.security import check_password_hash\n\n"
                    "def test_administrator_password(password: str):\n"
                    "    # Salted hash generated using scrypt (standard Werkzeug format)\n"
                    "    hashed_password = (\n"
                    "        \"scrypt:32768:8:1$KAaN1iT6BRmDlHL3$d68bdf6457a5218183113be9dc53d875\"\n"
                    "        \"9d0f8d05e6d15be1f6e024dbaaab817a17a0b6900d7d286cdac7baa4442faed7aba\"\n"
                    "        \"8ef61b5a0c2007ca867e145331571\"\n"
                    "    )\n"
                    "    return check_password_hash(hashed_password, password)"
                )
            },
            {
                "name": "3. Enforcing Template Auto-Escaping (Eliminating Stored XSS)",
                "type": "Unsafe HTML Rendering / Markup Bypass",
                "flaw_desc": (
                    "To support formatted text, the server originally wrapped the user-submitted <code>message</code> "
                    "field inside a <code>jinja2.Markup()</code> block before appending it to the global messages list. "
                    "This tells the template engine that the string contains safe HTML, completely disabling Jinja2's "
                    "built-in context-aware auto-escaping. As a result, any HTML or JavaScript injected into the message field "
                    "was rendered raw and executed directly in the browser of any user viewing the homepage."
                ),
                "patch_desc": (
                    "Rather than attempting to filter out tags using custom validation, the secure and correct remedy "
                    "is to let the template engine escape the user input. We removed the unsafe <code>Markup</code> "
                    "wrapping entirely. Now, all user-submitted inputs are stored as raw text, and Jinja2 automatically "
                    "encodes special characters (such as <code>&lt;</code> and <code>&gt;</code>) into safe text entities, "
                    "making Stored XSS completely impossible:"
                ),
                "code": (
                    "def add_message(args: dict):\n"
                    "    required_args = [\"name\", \"phone_number\", \"email\", \"subject\", \"message\"]\n"
                    "    result = {name: args.get(name) for name in required_args}\n"
                    "    for validator_name, validator in VALIDATORS.items():\n"
                    "        if validator_name in result:\n"
                    "            validator(result[validator_name])\n"
                    "    # Removed Markup wrapper to let Jinja2 automatically auto-escape output safely!\n"
                    "    if is_administrator_logged_in():\n"
                    "        result[\"name\"] = result[\"name\"] + \" (Administrator)\"\n\n"
                    "    messages.append(result)"
                )
            },
            {
                "name": "4. Persistent Application Secret Key (Session Lifecycle)",
                "type": "Ephemeral Cryptographic Secret Key Configuration",
                "flaw_desc": (
                    "The application's cryptographic <code>secret_key</code> was originally generated as 16 random bytes "
                    "on every application start. This meant that whenever the server was restarted or reloaded, all existing "
                    "user sessions, CSRF tokens, and signed cookies were instantly invalidated, resulting in immediate user logout "
                    "and broken active requests."
                ),
                "patch_desc": (
                    "We standardized secret key loading to read from the <code>FLASK_SECRET_KEY</code> environment variable "
                    "first. If not configured, it loads from a persistent local file (<code>.secret_key</code>) that is generated "
                    "safely on first boot. This ensures consistent session states across server restarts while maintaining high cryptographic entropy:"
                ),
                "code": (
                    "def start_app():\n"
                    "    # Load secret key persistently to avoid session invalidation on restart\n"
                    "    secret_key = os.environ.get(\"FLASK_SECRET_KEY\")\n"
                    "    if not secret_key:\n"
                    "        secret_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), \".secret_key\")\n"
                    "        if os.path.exists(secret_key_file):\n"
                    "            with open(secret_key_file, \"rb\") as f:\n"
                    "                secret_key = f.read()\n"
                    "        else:\n"
                    "            secret_key = generate_random_key()\n"
                    "            with open(secret_key_file, \"wb\") as f:\n"
                    "                f.write(secret_key)"
                )
            }
        ]
    }

    # -------------------------------------------------------------
    # SECTION E CONTENT
    # -------------------------------------------------------------
    data["section_e"] = {
        "title": "E. Session Riding & Bypassing HttpOnly Cookie Protections",
        "intro": (
            "This section explains the theoretical mechanics of how an attacker can successfully execute the "
            "actions in Section B (specifically, deleting all messages on the server) even if the administrator "
            "session cookie was configured with the <code>HttpOnly</code> directive. We analyze how XSS-based "
            "<b>Session Riding</b> and DOM access completely bypass this security boundary."
        ),
        "mechanism_title": "The Mechanism of Session Riding / Client-Side Request Forgery",
        "mechanism_desc": (
            "The <code>HttpOnly</code> flag is a vital defense-in-depth control that strictly prevents client-side scripts "
            "(such as JavaScript injected via XSS) from reading the <code>document.cookie</code> property. "
            "This completely stops the script from exfiltrating the raw session identifier back to the attacker. "
            "However, <code>HttpOnly</code> **does not** prevent the browser from automatically attaching the session cookie "
            "to any outgoing HTTP requests sent back to the application's origin."
        ),
        "steps": [
            {
                "name": "1. Direct HTTP Requests (Same-Origin Fetch)",
                "desc": (
                    "Because the injected script executes inside the victim's active browser context (under the same origin), "
                    "any HTTP request the script makes to the server automatically includes all relevant cookies (including "
                    "<code>HttpOnly</code> ones). To trigger the deletion of all messages, the attacker does not need to know the "
                    "actual session token value. The script can simply issue a same-origin background fetch request to the administrative "
                    "endpoint:<br/>"
                    "<code>fetch('/drop_all_messages')</code><br/>"
                    "The browser seamlessly attaches the administrator's cookie, and the server executes the action."
                )
            },
            {
                "name": "2. Bypassing CSRF Token Protection",
                "desc": (
                    "If the application enforces anti-CSRF token verification (as in the <code>/request</code> route using <code>csrf_token</code>), "
                    "a simple cross-site request would fail. However, because the script runs inside the same origin due to XSS, the script "
                    "has **full read and write access to the page's DOM**. The script can execute a multi-step payload:<br/>"
                    "a) Perform a background GET request to the homepage (<code>/</code>).<br/>"
                    "b) Parse the response HTML to locate the hidden input field containing the anti-CSRF token value: "
                    "<code>&lt;input type=\"hidden\" name=\"csrf_token\" value=\"TOKEN\"&gt;</code>.<br/>"
                    "c) Extract the token value from the DOM and include it in the POST request body sent to the protected endpoint.<br/>"
                    "This demonstrates why **XSS completely neutralizes CSRF protection**; once an attacker can execute script on the origin, "
                    "they can read any client-side tokens and bypass all anti-forgery validations."
                )
            }
        ]
    }

    # Placeholder for subsequent sections
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
        [Paragraph("Submitters:", style_body), Paragraph("Omri Asudon (208853598)<br/>Dvir Weinman (206397226)", style_meta)],
        [Paragraph("Submission Date:", style_body), Paragraph("June 02, 2026", style_meta)],
        [Paragraph("Course:", style_body), Paragraph("Secure Programming - Assignment 3", style_meta)],
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
    # SECTION A: HTTPS SETUP
    # =============================================================
    data = get_report_data()
    sec_a = data["section_a"]
    
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

    # =============================================================
    # SECTION B: STORED XSS & PARSER DISCREPANCIES
    # =============================================================
    if "section_b" in data:
        sec_b = data["section_b"]
        story.append(PageBreak())
        story.append(Paragraph(sec_b["title"], style_h1))
        story.append(Paragraph(sec_b["intro"], style_body))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(sec_b["parser_discrepancy_title"], style_h2))
        story.append(Paragraph(sec_b["parser_discrepancy_desc"], style_body))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph(sec_b["attack_flow_title"], style_h2))
        
        for step in sec_b["steps"]:
            elements = []
            elements.append(Paragraph(f"<b>{step['name']}</b>", style_h2))
            elements.append(Paragraph(step["desc"], style_body))
            elements.append(Spacer(1, 10))
            story.append(KeepTogether(elements))

    # =============================================================
    # SECTION C: OBJECT TAG ANALYSIS
    # =============================================================
    if "section_c" in data:
        sec_c = data["section_c"]
        story.append(PageBreak())
        story.append(Paragraph(sec_c["title"], style_h1))
        story.append(Paragraph(sec_c["intro"], style_body))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(sec_c["how_it_works_title"], style_h2))
        story.append(Paragraph(sec_c["how_it_works_desc"], style_body))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(sec_c["why_it_fails_title"], style_h2))
        
        for reason in sec_c["reasons"]:
            elements = []
            elements.append(Paragraph(f"<b>{reason['name']}</b>", style_h2))
            elements.append(Paragraph(reason["desc"], style_body))
            elements.append(Spacer(1, 10))
            story.append(KeepTogether(elements))

    # =============================================================
    # SECTION D: VULNERABILITY REMEDIATION
    # =============================================================
    if "section_d" in data:
        sec_d = data["section_d"]
        story.append(PageBreak())
        story.append(Paragraph(sec_d["title"], style_h1))
        story.append(Paragraph(sec_d["intro"], style_body))
        story.append(Spacer(1, 10))
        
        for vuln in sec_d["vulnerabilities"]:
            elements = []
            elements.append(Paragraph(f"<b>{vuln['name']}</b>", style_h2))
            elements.append(Paragraph(f"<b>Vulnerability Classification:</b> {vuln['type']}", style_body))
            elements.append(Paragraph(f"<b>Security Flaw Analysis:</b>", style_body))
            elements.append(Paragraph(vuln["flaw_desc"], style_body))
            elements.append(Paragraph(f"<b>Applied Mitigation Patch:</b>", style_body))
            elements.append(Paragraph(vuln["patch_desc"], style_body))
            
            if "code" in vuln:
                # Code box styling
                code_lines = vuln["code"].split('\n')
                code_paragraphs = [Paragraph(line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;'), style_code) for line in code_lines]
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

    # =============================================================
    # SECTION E: SESSION RIDING (HTTPONLY BYPASS)
    # =============================================================
    if "section_e" in data:
        sec_e = data["section_e"]
        story.append(PageBreak())
        story.append(Paragraph(sec_e["title"], style_h1))
        story.append(Paragraph(sec_e["intro"], style_body))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(sec_e["mechanism_title"], style_h2))
        story.append(Paragraph(sec_e["mechanism_desc"], style_body))
        story.append(Spacer(1, 10))
        
        for step in sec_e["steps"]:
            elements = []
            elements.append(Paragraph(f"<b>{step['name']}</b>", style_h2))
            elements.append(Paragraph(step["desc"], style_body))
            elements.append(Spacer(1, 15))
            story.append(KeepTogether(elements))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully: {filename}")


if __name__ == "__main__":
    build_pdf()
