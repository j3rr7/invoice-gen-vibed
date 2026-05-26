import json
import os

DEFAULT_SETTINGS_FILE = ".company_defaults.json"

DEFAULT_COMPANY_INFO = {
    "company_name": "My Company",
    "company_address": "Address",
    "company_email": "contact-me@email.com",
    "company_phone": "",
    "company_website": "",
    "footer_note": "Thank you for your continued business.",
}


def load_default_company_info():
    """Loads the company default details. Falls back to pre-defined values."""
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        try:
            with open(DEFAULT_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all default keys exist
                for k, v in DEFAULT_COMPANY_INFO.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_COMPANY_INFO.copy()
    return DEFAULT_COMPANY_INFO.copy()


def save_default_company_info(info):
    """Saves the current company details as defaults."""
    try:
        with open(DEFAULT_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving company defaults: {e}")
        return False


def save_invoice(file_path, data):
    """Saves the entire state of an invoice to a JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving invoice: {e}")
        return False


def load_invoice(file_path):
    """Loads invoice data from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading invoice: {e}")
        return None
