import os
import subprocess
import webbrowser
from jinja2 import Environment, FileSystemLoader

def format_idr(value):
    """Formats a numeric value to Indonesian currency format (e.g. 1.234.567,89)."""
    try:
        val = float(value)
        # Format to standard decimal
        s = f"{val:,.2f}"
        # Swap comma and dot: e.g. "1,234,567.89" -> "1.234.567,89"
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    except (ValueError, TypeError):
        return "0,00"

def get_browser_path():
    """Searches for Microsoft Edge or Google Chrome executable paths on Windows desktop platforms."""
    # Only try to locate on Windows desktop
    if os.name != 'nt':
        return None
        
    paths = [
        # Microsoft Edge standard paths
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Google Chrome standard paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    # Check if executable exists in standard paths
    for p in paths:
        if os.path.exists(p):
            return p
            
    # Fallback to checking if executable is in system PATH
    for cmd in ["msedge.exe", "chrome.exe", "msedge", "chrome"]:
        try:
            subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
            return cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
            
    return None

def compile_invoice_html(invoice_data):
    """
    Computes totals, formats numbers, and compiles the invoice data 
    into HTML using the Jinja2 template.
    """
    items = invoice_data.get("items", [])
    tax_rate = float(invoice_data.get("tax_rate", 0.5))
    tax_treatment = invoice_data.get("tax_treatment", "reverse") # "reverse" or "charge"
    
    # 1. Calculations
    subtotal = 0.0
    processed_items = []
    
    for item in items:
        qty = float(item.get("qty", 0))
        price = float(item.get("price", 20000))
        amt = qty * price
        subtotal += amt
        
        # Append date if included
        desc = item.get("desc", "").strip()
        if item.get("include_date", False) and item.get("date"):
            desc = f"{desc} — {item.get('date')}"
            
        processed_items.append({
            "desc": desc,
            "qty": int(qty) if qty.is_integer() else qty,
            "price": format_idr(price),
            "amount": format_idr(amt)
        })
        
    tax_amount = subtotal * (tax_rate / 100.0)
    
    if tax_treatment == "reverse":
        total_due = subtotal - tax_amount
    else:
        total_due = subtotal + tax_amount
        
    # 2. Rendering Context
    context = {
        "invoice_title": invoice_data.get("invoice_title", "Invoice"),
        "invoice_no": invoice_data.get("invoice_no", ""),
        "invoice_date": invoice_data.get("invoice_date", ""),
        
        "company_name": invoice_data.get("company_name", "Catering Fajar"),
        "company_address": invoice_data.get("company_address", ""),
        "company_email": invoice_data.get("company_email", ""),
        "company_phone": invoice_data.get("company_phone", ""),
        "company_website": invoice_data.get("company_website", ""),
        
        "recipient_name": invoice_data.get("recipient_name", ""),
        "recipient_address": invoice_data.get("recipient_address", ""),
        "billing_period": invoice_data.get("billing_period", ""),
        
        "items": processed_items,
        
        "subtotal": format_idr(subtotal),
        "tax_rate_percentage": f"{tax_rate:.1f}" if tax_rate.is_integer() else f"{tax_rate}",
        "tax_amount": format_idr(tax_amount),
        "tax_reverse_charge": (tax_treatment == "reverse"),
        "total_due": format_idr(total_due),
        
        "notes": invoice_data.get("notes", ""),
        "footer_note": invoice_data.get("footer_note", "Thank you for your continued business.")
    }
    
    # 3. Compile template
    # Find templates directory. We look in E:\self-project\catfaj-invoice\templates
    # which is our master template folder to avoid duplicate template files!
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, "templates")
    
    # If not found, look inside the local folder (fallback for mobile packaging)
    if not os.path.exists(templates_dir):
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("invoice_template.html")
    
    return template.render(context)

def generate_pdf(invoice_data, pdf_path):
    """
    Renders the invoice HTML and converts it to PDF using headless Edge/Chrome on Windows desktop,
    or falls back to saving and opening HTML in system browser on mobile.
    Returns (success_boolean, message_string)
    """
    html_content = compile_invoice_html(invoice_data)
    
    base_dir = os.path.dirname(pdf_path)
    if not base_dir:
        base_dir = "."
    temp_html_path = os.path.join(base_dir, "temp_invoice.html")
    
    try:
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        browser = get_browser_path()
        if not browser:
            # Fallback for mobile and other OS:
            # Tell the caller to open it in a browser webview for printing
            return False, temp_html_path
            
        # Desktop Windows printing using isolated browser session
        import tempfile
        import shutil
        
        temp_user_dir = tempfile.mkdtemp(prefix="edge_pdf_")
        norm_pdf_path = os.path.normpath(pdf_path)
        norm_html_path = os.path.normpath(os.path.abspath(temp_html_path))
        
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={temp_user_dir}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={norm_pdf_path}",
            norm_html_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        
        try:
            shutil.rmtree(temp_user_dir, ignore_errors=True)
        except Exception:
            pass
            
        if os.path.exists(pdf_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass
            return True, "Invoice PDF generated successfully!"
        else:
            raise Exception("PDF file was not created by the browser print process.")
            
    except Exception as e:
        return False, temp_html_path

def preview_in_browser(invoice_data):
    """Compiles the HTML invoice and returns the path to open for web preview."""
    html_content = compile_invoice_html(invoice_data)
    temp_html_path = "preview_invoice.html"
    try:
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True, temp_html_path
    except Exception as e:
        return False, f"Failed to save preview: {str(e)}"
