import datetime
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

# Import local modules
import data_manager
import invoice_generator

# Set up appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

INDONESIAN_MONTHS = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def parse_date(date_str):
    """Parses a date string in DD-MM-YYYY or common formats and returns a datetime object, or None."""
    date_str = date_str.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def format_date(dt):
    """Formats a datetime object to DD-MM-YYYY."""
    return dt.strftime("%d-%m-%Y")


def get_client_initials(name):
    """Generates initials from a company/person name, stripping common business prefixes."""
    if not name:
        return "XXX"

    cleaned = name.upper()
    prefixes = ["PT.", "PT", "CV.", "CV", "UD.", "UD", "CO.", "CO", "LTD.", "LTD"]

    words = cleaned.split()
    if words and words[0] in prefixes:
        words = words[1:]

    filtered_words = []
    for w in words:
        w_clean = "".join(c for c in w if c.isalnum())
        if w_clean and w_clean not in prefixes:
            filtered_words.append(w_clean)

    if not filtered_words:
        filtered_words = [c for c in cleaned if c.isalnum()]
        if not filtered_words:
            return "XXX"
        return "".join(filtered_words[:3])

    initials = "".join(w[0] for w in filtered_words if w)
    return initials[:3]


class InvoiceDesignerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Invoice Designer")
        self.geometry("1150x780")
        self.minsize(1050, 700)

        # Application state
        self.items = []  # List of dicts: {"desc": "...", "qty": 0.0, "price": 20000.0, "include_date": True/False, "date": "..."}
        self.is_updating_ui = False

        # Default company data
        self.defaults = data_manager.load_default_company_info()

        # Set up variables
        self.setup_variables()

        # Create UI elements
        self.create_widgets()

        # Load defaults into UI
        self.load_defaults_into_ui()

        # Initialize calculations
        self.update_calculations()

        # Add variable traces for auto-generation reactive behavior
        self.add_reactive_triggers()

    def setup_variables(self):
        # Company variables
        self.company_name_var = ctk.StringVar()
        self.company_address_var = ctk.StringVar()
        self.company_email_var = ctk.StringVar()
        self.company_phone_var = ctk.StringVar()
        self.company_website_var = ctk.StringVar()
        self.footer_note_var = ctk.StringVar()

        # Recipient variables
        self.recipient_name_var = ctk.StringVar()
        self.recipient_address_var = ctk.StringVar()

        # Invoice metadata variables
        self.invoice_title_var = ctk.StringVar(value="Invoice")
        self.bill_date_var = ctk.StringVar(value=format_date(datetime.datetime.now()))
        self.billing_period_var = ctk.StringVar()
        self.invoice_no_auto_var = ctk.BooleanVar(value=True)
        self.invoice_no_var = ctk.StringVar()
        self.invoice_counter_var = ctk.StringVar(value="1")

        # Item Form variables
        self.item_desc_var = ctk.StringVar()
        self.item_qty_var = ctk.StringVar(value="0")
        self.item_price_var = ctk.StringVar(value="20000")
        self.item_use_date_var = ctk.BooleanVar(value=False)
        self.item_date_var = ctk.StringVar(value=format_date(datetime.datetime.now()))

        # Tax and Calculations
        self.tax_rate_var = ctk.StringVar(value="0.5")
        self.tax_treatment_var = ctk.StringVar(
            value="Reverse Charge"
        )  # "Reverse Charge" or "Standard Charge"

    def add_reactive_triggers(self):
        # Trigger invoice number auto-update on relevant field changes
        self.recipient_name_var.trace_add(
            "write", lambda *a: self.trigger_invoice_auto_gen()
        )
        self.bill_date_var.trace_add(
            "write", lambda *a: self.trigger_invoice_auto_gen()
        )
        self.invoice_counter_var.trace_add(
            "write", lambda *a: self.trigger_invoice_auto_gen()
        )
        self.invoice_no_auto_var.trace_add(
            "write", lambda *a: self.trigger_invoice_auto_gen()
        )

        # Trigger billing period auto-update on invoice date change
        self.bill_date_var.trace_add(
            "write", lambda *a: self.trigger_billing_period_auto_calc()
        )

        # Initialize the reactive values
        self.trigger_billing_period_auto_calc()
        self.trigger_invoice_auto_gen()

    def create_widgets(self):
        # Main Grid Layout
        self.grid_columnconfigure(0, weight=4, minsize=480)  # Left panel
        self.grid_columnconfigure(1, weight=5, minsize=520)  # Right panel
        self.grid_rowconfigure(0, weight=0)  # Title Banner
        self.grid_rowconfigure(1, weight=1)  # Main Panels

        # ──────── TOP BANNER ────────
        self.banner = ctk.CTkFrame(self, height=70, corner_radius=0)
        self.banner.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
        self.banner.grid_columnconfigure(0, weight=1)
        self.banner.grid_columnconfigure(1, weight=0)

        title_lbl = ctk.CTkLabel(
            self.banner,
            text="CATERING FAJAR - INVOICE DESIGNER",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=25, pady=20)

        # Dark/Light Mode switch
        self.theme_switch = ctk.CTkSwitch(
            self.banner, text="Light Mode", command=self.toggle_theme
        )
        self.theme_switch.grid(row=0, column=1, padx=25, pady=20, sticky="e")

        # ──────── MAIN CONTAINER PANELS ────────

        # LEFT COLUMN (Scrollable settings)
        self.left_panel = ctk.CTkScrollableFrame(
            self,
            label_text="INVOICE PROPERTIES",
            label_font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
        )
        self.left_panel.grid(
            row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20)
        )

        # RIGHT COLUMN (Items list, totals and actions)
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.grid(
            row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20)
        )
        self.right_panel.grid_rowconfigure(0, weight=1)  # Item Table Frame
        self.right_panel.grid_rowconfigure(1, weight=0)  # Add Item Form Frame
        self.right_panel.grid_rowconfigure(2, weight=0)  # Calculations & Actions
        self.right_panel.grid_columnconfigure(0, weight=1)

        # ─── LEFT PANEL WIDGETS (PROPERTIES) ───

        # 1. Company Settings Section
        company_frame = ctk.CTkFrame(self.left_panel)
        company_frame.pack(fill="x", padx=10, pady=10)

        sec_title_1 = ctk.CTkLabel(
            company_frame,
            text="YOUR COMPANY PROFILE (CATERING)",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        sec_title_1.pack(anchor="w", padx=15, pady=(12, 8))

        self.create_label_entry(company_frame, "Company Name:", self.company_name_var)
        self.create_label_entry(company_frame, "Address:", self.company_address_var)
        self.create_label_entry(company_frame, "Email Address:", self.company_email_var)
        self.create_label_entry(company_frame, "Phone Number:", self.company_phone_var)
        self.create_label_entry(company_frame, "Website:", self.company_website_var)
        self.create_label_entry(company_frame, "Footer Note:", self.footer_note_var)

        save_default_btn = ctk.CTkButton(
            company_frame,
            text="Save as Default Profile",
            fg_color="transparent",
            border_width=1,
            hover_color="#2b2b2b",
            command=self.save_company_defaults,
        )
        save_default_btn.pack(fill="x", padx=15, pady=(5, 12))

        # 2. Recipient / Client Settings Section
        client_frame = ctk.CTkFrame(self.left_panel)
        client_frame.pack(fill="x", padx=10, pady=10)

        sec_title_2 = ctk.CTkLabel(
            client_frame,
            text="BILL TO (RECIPIENT)",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        sec_title_2.pack(anchor="w", padx=15, pady=(12, 8))

        self.create_label_entry(
            client_frame, "Client Name / Company *:", self.recipient_name_var
        )
        self.create_label_entry(
            client_frame, "Client Address (Optional):", self.recipient_address_var
        )

        # 3. Invoice Metadata Section
        meta_frame = ctk.CTkFrame(self.left_panel)
        meta_frame.pack(fill="x", padx=10, pady=(10, 20))

        sec_title_3 = ctk.CTkLabel(
            meta_frame,
            text="INVOICE METADATA",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        sec_title_3.pack(anchor="w", padx=15, pady=(12, 8))

        self.create_label_entry(meta_frame, "Invoice Title:", self.invoice_title_var)
        self.create_label_entry(
            meta_frame, "Invoice Date (DD-MM-YYYY):", self.bill_date_var
        )
        self.create_label_entry(
            meta_frame, "Billing Period (e.g. Mei 2026):", self.billing_period_var
        )

        # Auto-generation block
        chk_frame = ctk.CTkFrame(meta_frame, fg_color="transparent")
        chk_frame.pack(fill="x", padx=15, pady=4)

        auto_chk = ctk.CTkCheckBox(
            chk_frame,
            text="Auto-Generate Invoice Number",
            variable=self.invoice_no_auto_var,
            command=self.toggle_invoice_no_field,
        )
        auto_chk.pack(side="left")

        # Counter block for Auto-Gen
        self.counter_label = ctk.CTkLabel(chk_frame, text="Counter:")
        self.counter_label.pack(side="left", padx=(20, 5))
        self.counter_entry = ctk.CTkEntry(
            chk_frame, textvariable=self.invoice_counter_var, width=50
        )
        self.counter_entry.pack(side="left")

        # Invoice number entry
        self.invoice_no_entry_frame = ctk.CTkFrame(meta_frame, fg_color="transparent")
        self.invoice_no_entry_frame.pack(fill="x", padx=15, pady=(5, 12))
        lbl = ctk.CTkLabel(
            self.invoice_no_entry_frame, text="Invoice Number:", width=130, anchor="w"
        )
        lbl.pack(side="left")
        self.invoice_no_entry = ctk.CTkEntry(
            self.invoice_no_entry_frame, textvariable=self.invoice_no_var
        )
        self.invoice_no_entry.pack(side="left", fill="x", expand=True)

        # ─── RIGHT PANEL WIDGETS (ITEMS & ACTIONS) ───

        # 1. Items List Panel
        self.items_table_frame = ctk.CTkLabel(
            self.right_panel,
            text="CURRENT LINE ITEMS",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            fg_color="#1d1d1d",
            text_color="#ffffff",
            corner_radius=6,
            height=35,
        )
        self.items_table_frame.grid(
            row=0, column=0, sticky="new", padx=10, pady=(10, 0)
        )

        # Grid Headers (under title label)
        headers_frame = ctk.CTkFrame(
            self.right_panel, height=28, fg_color="transparent"
        )
        headers_frame.grid(row=0, column=0, sticky="new", padx=10, pady=(45, 0))
        headers_frame.grid_columnconfigure(0, weight=5)  # Desc
        headers_frame.grid_columnconfigure(1, weight=1)  # Qty
        headers_frame.grid_columnconfigure(2, weight=2)  # Unit Price
        headers_frame.grid_columnconfigure(3, weight=2)  # Total
        headers_frame.grid_columnconfigure(4, weight=0, minsize=40)  # Action

        h1 = ctk.CTkLabel(
            headers_frame,
            text="Description",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        )
        h1.grid(row=0, column=0, sticky="w", padx=5)
        h2 = ctk.CTkLabel(
            headers_frame,
            text="Qty",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="center",
        )
        h2.grid(row=0, column=1, sticky="we", padx=5)
        h3 = ctk.CTkLabel(
            headers_frame,
            text="Price (IDR)",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="e",
        )
        h3.grid(row=0, column=2, sticky="e", padx=5)
        h4 = ctk.CTkLabel(
            headers_frame,
            text="Total (IDR)",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="e",
        )
        h4.grid(row=0, column=3, sticky="e", padx=5)
        h5 = ctk.CTkLabel(headers_frame, text="", width=30)
        h5.grid(row=0, column=4, padx=5)

        # Scrollable items holder
        self.items_scroll_frame = ctk.CTkScrollableFrame(
            self.right_panel, fg_color="transparent"
        )
        self.items_scroll_frame.grid(
            row=0, column=0, sticky="nsew", padx=10, pady=(75, 10)
        )

        # 2. Add Item Form Panel
        add_form_frame = ctk.CTkFrame(self.right_panel)
        add_form_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        form_title = ctk.CTkLabel(
            add_form_frame,
            text="ADD NEW INVOICE ITEM",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        form_title.grid(
            row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5)
        )

        # Grid layout for fields inside add form
        add_form_frame.grid_columnconfigure(0, weight=4)  # Desc
        add_form_frame.grid_columnconfigure(1, weight=1)  # Qty
        add_form_frame.grid_columnconfigure(2, weight=2)  # Price

        l_desc = ctk.CTkLabel(
            add_form_frame, text="Item Description:", font=ctk.CTkFont(size=10)
        )
        l_desc.grid(row=1, column=0, sticky="w", padx=15)
        l_qty = ctk.CTkLabel(
            add_form_frame, text="Quantity:", font=ctk.CTkFont(size=10)
        )
        l_qty.grid(row=1, column=1, sticky="w", padx=5)
        l_price = ctk.CTkLabel(
            add_form_frame, text="Price (IDR):", font=ctk.CTkFont(size=10)
        )
        l_price.grid(row=1, column=2, sticky="w", padx=5)

        self.e_desc = ctk.CTkEntry(
            add_form_frame,
            textvariable=self.item_desc_var,
            placeholder_text="e.g. Catering Makan Siang",
        )
        self.e_desc.grid(row=2, column=0, sticky="ew", padx=(15, 5), pady=(0, 10))

        self.e_qty = ctk.CTkEntry(
            add_form_frame, textvariable=self.item_qty_var, placeholder_text="0"
        )
        self.e_qty.grid(row=2, column=1, sticky="ew", padx=5, pady=(0, 10))

        self.e_price = ctk.CTkEntry(
            add_form_frame, textvariable=self.item_price_var, placeholder_text="20000"
        )
        self.e_price.grid(row=2, column=2, sticky="ew", padx=5, pady=(0, 10))

        # Add Date Toggle options
        date_opt_frame = ctk.CTkFrame(add_form_frame, fg_color="transparent")
        date_opt_frame.grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=15, pady=(0, 12)
        )

        date_chk = ctk.CTkCheckBox(
            date_opt_frame,
            text="Include Date in Description",
            variable=self.item_use_date_var,
            command=self.toggle_item_date_field,
        )
        date_chk.pack(side="left")

        self.item_date_entry = ctk.CTkEntry(
            date_opt_frame, textvariable=self.item_date_var, width=120
        )
        self.item_date_entry.pack(side="left", padx=15)
        self.toggle_item_date_field()  # Set initial disabled state

        btn_add = ctk.CTkButton(
            date_opt_frame,
            text="+ Add Item",
            width=120,
            fg_color="#3a7ebf",
            hover_color="#295d8f",
            command=self.add_item,
        )
        btn_add.pack(side="right")

        # 3. Calculations Summary & Global Actions Frame
        self.calc_actions_frame = ctk.CTkFrame(self.right_panel)
        self.calc_actions_frame.grid(
            row=2, column=0, sticky="ew", padx=10, pady=(5, 10)
        )
        self.calc_actions_frame.grid_columnconfigure(0, weight=1)  # Tax Config
        self.calc_actions_frame.grid_columnconfigure(
            1, weight=1
        )  # Calculations Display
        self.calc_actions_frame.grid_columnconfigure(2, weight=1)  # Operations/Buttons

        # Column A: Tax Configuration
        tax_frame = ctk.CTkFrame(self.calc_actions_frame, fg_color="transparent")
        tax_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        tax_lbl = ctk.CTkLabel(
            tax_frame,
            text="TAX PREFERENCES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        tax_lbl.pack(anchor="w", pady=(0, 5))

        rate_row = ctk.CTkFrame(tax_frame, fg_color="transparent")
        rate_row.pack(fill="x", pady=2)
        r_lbl = ctk.CTkLabel(rate_row, text="Tax Rate (%):", width=80, anchor="w")
        r_lbl.pack(side="left")
        self.tax_rate_entry = ctk.CTkEntry(
            rate_row, textvariable=self.tax_rate_var, width=60
        )
        self.tax_rate_entry.pack(side="left")
        self.tax_rate_var.trace_add("write", lambda *a: self.update_calculations())

        treat_lbl = ctk.CTkLabel(tax_frame, text="Tax Treatment:", anchor="w")
        treat_lbl.pack(anchor="w", pady=(5, 2))

        self.tax_treat_menu = ctk.CTkOptionMenu(
            tax_frame,
            values=["Reverse Charge", "Standard Charge"],
            variable=self.tax_treatment_var,
            command=lambda e: self.update_calculations(),
        )
        self.tax_treat_menu.pack(fill="x")

        # Column B: Calculations Display
        calcs_display_frame = ctk.CTkFrame(
            self.calc_actions_frame, fg_color="transparent"
        )
        calcs_display_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        calcs_lbl = ctk.CTkLabel(
            calcs_display_frame,
            text="CALCULATION SUMMARY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        calcs_lbl.pack(anchor="w", pady=(0, 5))

        # Subtotal Row
        sub_row = ctk.CTkFrame(calcs_display_frame, fg_color="transparent")
        sub_row.pack(fill="x", pady=1)
        ctk.CTkLabel(sub_row, text="Subtotal:", font=ctk.CTkFont(size=11)).pack(
            side="left"
        )
        self.lbl_subtotal = ctk.CTkLabel(
            sub_row, text="IDR 0,00", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_subtotal.pack(side="right")

        # Tax Amount Row
        tamt_row = ctk.CTkFrame(calcs_display_frame, fg_color="transparent")
        tamt_row.pack(fill="x", pady=1)
        self.lbl_tax_title = ctk.CTkLabel(
            tamt_row, text="Tax (0.5%):", font=ctk.CTkFont(size=11)
        )
        self.lbl_tax_title.pack(side="left")
        self.lbl_tax_amount = ctk.CTkLabel(
            tamt_row, text="IDR (0,00)", font=ctk.CTkFont(size=11)
        )
        self.lbl_tax_amount.pack(side="right")

        # Total Row
        tot_row = ctk.CTkFrame(calcs_display_frame, fg_color="transparent")
        tot_row.pack(fill="x", pady=(8, 1))
        ctk.CTkLabel(
            tot_row, text="TOTAL DUE:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        self.lbl_total_due = ctk.CTkLabel(
            tot_row,
            text="IDR 0,00",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4CAF50",
        )
        self.lbl_total_due.pack(side="right")

        # Column C: Global Actions (Buttons)
        actions_grid = ctk.CTkFrame(self.calc_actions_frame, fg_color="transparent")
        actions_grid.grid(row=0, column=2, sticky="nsew", padx=15, pady=15)

        act_lbl = ctk.CTkLabel(
            actions_grid,
            text="GLOBAL OPERATIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#3a7ebf",
        )
        act_lbl.pack(anchor="w", pady=(0, 5))

        # Row 1 of actions
        act_row1 = ctk.CTkFrame(actions_grid, fg_color="transparent")
        act_row1.pack(fill="x", pady=3)
        btn_open = ctk.CTkButton(
            act_row1,
            text="Open JSON",
            width=70,
            fg_color="#4a4a4a",
            hover_color="#363636",
            command=self.load_invoice_file,
        )
        btn_open.pack(side="left", fill="x", expand=True, padx=(0, 3))
        btn_save = ctk.CTkButton(
            act_row1,
            text="Save JSON",
            width=70,
            fg_color="#4a4a4a",
            hover_color="#363636",
            command=self.save_invoice_file,
        )
        btn_save.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # Row 2 of actions
        btn_prev = ctk.CTkButton(
            actions_grid,
            text="Browser Preview",
            fg_color="#e08214",
            hover_color="#c26d0d",
            command=self.preview_invoice,
        )
        btn_prev.pack(fill="x", pady=3)

        btn_pdf = ctk.CTkButton(
            actions_grid,
            text="Export A4 PDF",
            fg_color="#2fa572",
            hover_color="#218057",
            font=ctk.CTkFont(weight="bold"),
            command=self.export_pdf,
        )
        btn_pdf.pack(fill="x", pady=3)

    def create_label_entry(self, parent, text, var):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=4)

        lbl = ctk.CTkLabel(frame, text=text, width=150, anchor="w")
        lbl.pack(side="left")

        entry = ctk.CTkEntry(frame, textvariable=var)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Light Mode")

    def toggle_invoice_no_field(self):
        if self.invoice_no_auto_var.get():
            self.invoice_no_entry.configure(state="disabled")
            self.counter_label.pack(side="left", padx=(20, 5))
            self.counter_entry.pack(side="left")
            self.trigger_invoice_auto_gen()
        else:
            self.invoice_no_entry.configure(state="normal")
            self.counter_label.pack_forget()
            self.counter_entry.pack_forget()

    def toggle_item_date_field(self):
        if self.item_use_date_var.get():
            self.item_date_entry.configure(state="normal")
        else:
            self.item_date_entry.configure(state="disabled")

    def load_defaults_into_ui(self):
        self.company_name_var.set(self.defaults.get("company_name", ""))
        self.company_address_var.set(self.defaults.get("company_address", ""))
        self.company_email_var.set(self.defaults.get("company_email", ""))
        self.company_phone_var.set(self.defaults.get("company_phone", ""))
        self.company_website_var.set(self.defaults.get("company_website", ""))
        self.footer_note_var.set(self.defaults.get("footer_note", ""))

    def save_company_defaults(self):
        info = {
            "company_name": self.company_name_var.get(),
            "company_address": self.company_address_var.get(),
            "company_email": self.company_email_var.get(),
            "company_phone": self.company_phone_var.get(),
            "company_website": self.company_website_var.get(),
            "footer_note": self.footer_note_var.get(),
        }
        if data_manager.save_default_company_info(info):
            self.defaults = info
            messagebox.showinfo(
                "Success", "Catering profile saved as default successfully!"
            )
        else:
            messagebox.showerror("Error", "Failed to save catering profile defaults.")

    def trigger_billing_period_auto_calc(self):
        if self.is_updating_ui:
            return

        date_str = self.bill_date_var.get()
        dt = parse_date(date_str)
        if dt:
            month_idx = dt.month
            year = dt.year
            month_name = INDONESIAN_MONTHS.get(month_idx, dt.strftime("%B"))

            # Format to 'Month Year' e.g. 'Mei 2026'
            self.is_updating_ui = True
            self.billing_period_var.set(f"{month_name} {year}")
            self.is_updating_ui = False

    def trigger_invoice_auto_gen(self):
        if self.is_updating_ui:
            return

        if not self.invoice_no_auto_var.get():
            return

        date_str = self.bill_date_var.get()
        dt = parse_date(date_str)

        # Get date token YYYYMM
        if dt:
            date_token = dt.strftime("%Y%m")
        else:
            date_token = datetime.datetime.now().strftime("%Y%m")

        # Get initials
        client_name = self.recipient_name_var.get()
        initials = get_client_initials(client_name)

        # Get counter
        counter_str = self.invoice_counter_var.get().strip()
        try:
            counter = int(counter_str) if counter_str else 1
        except ValueError:
            counter = 1

        generated_no = f"INV-{date_token}-{initials}-{counter:03d}"

        self.is_updating_ui = True
        self.invoice_no_var.set(generated_no)
        self.is_updating_ui = False

    def add_item(self):
        desc = self.item_desc_var.get().strip()
        qty_str = self.item_qty_var.get().strip()
        price_str = self.item_price_var.get().strip()
        use_date = self.item_use_date_var.get()
        item_date = self.item_date_var.get().strip()

        if not desc:
            messagebox.showwarning("Validation Error", "Item description is required.")
            return

        try:
            qty = float(qty_str) if qty_str else 0.0
            if qty < 0:
                raise ValueError("Quantity cannot be negative")
        except ValueError:
            messagebox.showwarning(
                "Validation Error", "Quantity must be a valid number."
            )
            return

        try:
            price = float(price_str) if price_str else 20000.0
            if price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            messagebox.showwarning("Validation Error", "Price must be a valid number.")
            return

        if use_date:
            dt = parse_date(item_date)
            if not dt:
                messagebox.showwarning(
                    "Validation Error", "Item date must be in DD-MM-YYYY format."
                )
                return
            normalized_date = format_date(dt)
        else:
            normalized_date = ""

        # Create item record
        new_item = {
            "desc": desc,
            "qty": qty,
            "price": price,
            "include_date": use_date,
            "date": normalized_date,
        }

        # Add to state list
        self.items.append(new_item)

        # Update Items list GUI
        self.refresh_items_list()

        # Perform calculations
        self.update_calculations()

        # Prepare for the NEXT item:
        # (We keep description and quantity values for easy consecutive item entry!)

        # 2. AUTO INCREMENT DATE IF CHECKED
        if use_date and normalized_date:
            dt = parse_date(normalized_date)
            if dt:
                next_day = dt + datetime.timedelta(days=1)
                self.item_date_var.set(format_date(next_day))

        # Return focus to item description entry for speedy keyboard input
        self.e_desc.focus()

    def delete_item(self, idx):
        if 0 <= idx < len(self.items):
            del self.items[idx]
            self.refresh_items_list()
            self.update_calculations()

    def refresh_items_list(self):
        # Clear all existing widgets inside the scroll frame
        for child in self.items_scroll_frame.winfo_children():
            child.destroy()

        # Repopulate
        for idx, item in enumerate(self.items):
            row_frame = ctk.CTkFrame(self.items_scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            row_frame.grid_columnconfigure(0, weight=5)  # Desc
            row_frame.grid_columnconfigure(1, weight=1)  # Qty
            row_frame.grid_columnconfigure(2, weight=2)  # Unit Price
            row_frame.grid_columnconfigure(3, weight=2)  # Amount
            row_frame.grid_columnconfigure(4, weight=0, minsize=40)  # Action

            # Label Description (Description + Date if toggled)
            desc_text = item["desc"]
            if item["include_date"] and item["date"]:
                desc_text = f"{desc_text} — {item['date']}"

            l_desc = ctk.CTkLabel(
                row_frame, text=desc_text, anchor="w", font=ctk.CTkFont(size=11)
            )
            l_desc.grid(row=0, column=0, sticky="w", padx=5)

            # Label Qty
            qty = item["qty"]
            qty_text = str(int(qty)) if qty.is_integer() else f"{qty:.2f}"
            l_qty = ctk.CTkLabel(
                row_frame, text=qty_text, anchor="center", font=ctk.CTkFont(size=11)
            )
            l_qty.grid(row=0, column=1, sticky="we", padx=5)

            # Label Price
            l_price = ctk.CTkLabel(
                row_frame,
                text=invoice_generator.format_idr(item["price"]),
                anchor="e",
                font=ctk.CTkFont(size=11),
            )
            l_price.grid(row=0, column=2, sticky="e", padx=5)

            # Label Total Amount
            total_amt = qty * item["price"]
            l_tot = ctk.CTkLabel(
                row_frame,
                text=invoice_generator.format_idr(total_amt),
                anchor="e",
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            l_tot.grid(row=0, column=3, sticky="e", padx=5)

            # Delete Button
            # Use character 🗑 or ✕ for deletion
            btn_del = ctk.CTkButton(
                row_frame,
                text="✕",
                width=24,
                height=24,
                fg_color="#c0392b",
                hover_color="#962d22",
                command=lambda index=idx: self.delete_item(index),
            )
            btn_del.grid(row=0, column=4, padx=(10, 5))

    def update_calculations(self):
        subtotal = 0.0
        for item in self.items:
            subtotal += float(item["qty"]) * float(item["price"])

        tax_rate_str = self.tax_rate_var.get().strip()
        try:
            tax_rate = float(tax_rate_str) if tax_rate_str else 0.0
        except ValueError:
            tax_rate = 0.0

        tax_amount = subtotal * (tax_rate / 100.0)

        tax_treatment = self.tax_treatment_var.get()
        if tax_treatment == "Reverse Charge":
            total_due = subtotal - tax_amount
            tax_disp = f"({invoice_generator.format_idr(tax_amount)})"
        else:
            total_due = subtotal + tax_amount
            tax_disp = invoice_generator.format_idr(tax_amount)

        # Update Labels
        self.lbl_subtotal.configure(
            text=f"IDR {invoice_generator.format_idr(subtotal)}"
        )
        self.lbl_tax_title.configure(text=f"Tax ({tax_rate_str}%):")
        self.lbl_tax_amount.configure(text=f"IDR {tax_disp}")
        self.lbl_total_due.configure(
            text=f"IDR {invoice_generator.format_idr(total_due)}"
        )

    def gather_invoice_data(self):
        """Assembles all fields from the GUI into a single unified dictionary."""
        tax_rate_str = self.tax_rate_var.get().strip()
        try:
            tax_rate = float(tax_rate_str) if tax_rate_str else 0.0
        except ValueError:
            tax_rate = 0.0

        tax_treatment_code = (
            "reverse" if self.tax_treatment_var.get() == "Reverse Charge" else "charge"
        )

        return {
            "invoice_title": self.invoice_title_var.get(),
            "invoice_no": self.invoice_no_var.get(),
            "invoice_date": self.bill_date_var.get(),
            "company_name": self.company_name_var.get(),
            "company_address": self.company_address_var.get(),
            "company_email": self.company_email_var.get(),
            "company_phone": self.company_phone_var.get(),
            "company_website": self.company_website_var.get(),
            "footer_note": self.footer_note_var.get(),
            "recipient_name": self.recipient_name_var.get(),
            "recipient_address": self.recipient_address_var.get(),
            "billing_period": self.billing_period_var.get(),
            "items": self.items,
            "tax_rate": tax_rate,
            "tax_treatment": tax_treatment_code,
            "invoice_no_auto": self.invoice_no_auto_var.get(),
            "invoice_counter": self.invoice_counter_var.get(),
            "notes": "",  # Can extend later if required
        }

    def load_invoice_file(self):
        path = filedialog.askopenfilename(filetypes=[("Invoice Data Files", "*.json")])
        if not path:
            return

        data = data_manager.load_invoice(path)
        if not data:
            messagebox.showerror("Error", "Could not load invoice data from JSON.")
            return

        # Populate GUI from JSON
        self.is_updating_ui = True

        self.invoice_title_var.set(data.get("invoice_title", "Invoice"))
        self.invoice_no_var.set(data.get("invoice_no", ""))
        self.bill_date_var.set(data.get("invoice_date", ""))
        self.billing_period_var.set(data.get("billing_period", ""))

        self.company_name_var.set(data.get("company_name", ""))
        self.company_address_var.set(data.get("company_address", ""))
        self.company_email_var.set(data.get("company_email", ""))
        self.company_phone_var.set(data.get("company_phone", ""))
        self.company_website_var.set(data.get("company_website", ""))
        self.footer_note_var.set(data.get("footer_note", ""))

        self.recipient_name_var.set(data.get("recipient_name", ""))
        self.recipient_address_var.set(data.get("recipient_address", ""))

        self.tax_rate_var.set(str(data.get("tax_rate", 0.5)))

        tax_code = data.get("tax_treatment", "reverse")
        self.tax_treatment_var.set(
            "Reverse Charge" if tax_code == "reverse" else "Standard Charge"
        )

        self.invoice_no_auto_var.set(data.get("invoice_no_auto", True))
        self.invoice_counter_var.set(str(data.get("invoice_counter", 1)))

        # Load items list
        self.items = data.get("items", [])

        self.is_updating_ui = False

        # Sync reactive updates
        self.toggle_invoice_no_field()
        self.refresh_items_list()
        self.update_calculations()

        messagebox.showinfo("Success", "Invoice data loaded successfully!")

    def save_invoice_file(self):
        # Validation: recipient name is required
        client = self.recipient_name_var.get().strip()
        if not client:
            messagebox.showwarning(
                "Validation Error", "Recipient Client Name is required to save."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Invoice Data Files", "*.json")]
        )
        if not path:
            return

        data = self.gather_invoice_data()

        if data_manager.save_invoice(path, data):
            messagebox.showinfo(
                "Success", f"Invoice saved to {os.path.basename(path)} successfully!"
            )
        else:
            messagebox.showerror("Error", "Failed to save invoice JSON file.")

    def preview_invoice(self):
        # Validation
        client = self.recipient_name_var.get().strip()
        if not client:
            messagebox.showwarning(
                "Validation Error", "Recipient Client Name is required."
            )
            return

        data = self.gather_invoice_data()
        success, msg = invoice_generator.preview_in_browser(data)
        if not success:
            messagebox.showerror("Preview Failed", msg)

    def export_pdf(self):
        # Validation
        client = self.recipient_name_var.get().strip()
        if not client:
            messagebox.showwarning(
                "Validation Error", "Recipient Client Name is required."
            )
            return

        # Choose export save path
        suggested_name = f"invoice_{self.invoice_no_var.get()}.pdf".replace("-", "_")
        path = filedialog.asksaveasfilename(
            initialfile=suggested_name,
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
        )
        if not path:
            return

        data = self.gather_invoice_data()

        # Force a GUI refresh to prevent thread lockup during PDF print subprocess
        self.update()

        # Start conversion
        success, msg = invoice_generator.generate_pdf(data, path)
        if success:
            messagebox.showinfo("Success", msg)

            # Post-success increment: auto-increment counter to ready for next invoice
            if self.invoice_no_auto_var.get():
                try:
                    current_c = int(self.invoice_counter_var.get())
                    self.invoice_counter_var.set(str(current_c + 1))
                except Exception:
                    pass
        else:
            messagebox.showwarning("PDF Export Notice", msg)


if __name__ == "__main__":
    app = InvoiceDesignerApp()
    app.mainloop()
