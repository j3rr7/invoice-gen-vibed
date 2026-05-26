import datetime
import os

import flet as ft

# Import local mobile modules
import data_manager
import invoice_generator

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

# ── Design Tokens ──
ACCENT = "#1e88e5"
ACCENT_DARK = "#1565c0"
ACCENT_LIGHT = "#42a5f5"
SUCCESS = "#43a047"
WARNING = "#fb8c00"
DANGER = "#e53935"
SURFACE = "#1e1e2e"
SURFACE_ALT = "#2a2a3e"
CARD_BG = "#252538"
DIVIDER = "#35354a"
TEXT_PRIMARY = "#e8eaf6"
TEXT_SECONDARY = "#9e9eb8"


# ── Padding / Margin helpers ────────────────────────
def _p(left=0, top=0, right=0, bottom=0):
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def _psym(horizontal=0, vertical=0):
    return ft.Padding(left=horizontal, top=vertical, right=horizontal, bottom=vertical)


def _pall(v):
    return ft.Padding(left=v, top=v, right=v, bottom=v)


def _m(left=0, top=0, right=0, bottom=0):
    return ft.Margin(left=left, top=top, right=right, bottom=bottom)


def _msym(horizontal=0, vertical=0):
    return ft.Margin(left=horizontal, top=vertical, right=horizontal, bottom=vertical)


def _br(r):
    return ft.BorderRadius(top_left=r, top_right=r, bottom_left=r, bottom_right=r)


def _br_only(tl=0, tr=0, bl=0, br=0):
    return ft.BorderRadius(top_left=tl, top_right=tr, bottom_left=bl, bottom_right=br)


# ────────────────────────────────────────────────────


def parse_date(date_str):
    date_str = date_str.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def format_date(dt):
    return dt.strftime("%d-%m-%Y")


def get_client_initials(name):
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


# ── Reusable UI builders ─────────────────────────────


def section_header(title: str, icon: str, color: str = "#1e88e5") -> ft.Container:
    """Colored pill-style section label."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=14, color=color),
                ft.Text(title, size=10, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=5,
            tight=True,
        ),
        margin=_m(bottom=10, top=2),
    )


def styled_field(
    label: str,
    value: str = "",
    hint: str = "",
    icon: str = None,
    multiline=False,
    min_lines=1,
    max_lines=1,
    width=None,
    disabled=False,
    expand=False,
    on_change=None,
) -> ft.TextField:
    """Uniformly styled text input field."""
    kwargs = dict(
        label=label,
        value=value,
        hint_text=hint,
        disabled=disabled,
        expand=expand,
        border_color=DIVIDER,
        focused_border_color=ACCENT,
        focused_color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        cursor_color=ACCENT,
        border_radius=10,
        content_padding=_psym(horizontal=14, vertical=12),
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
        on_change=on_change,
    )
    if icon:
        kwargs["prefix_icon"] = icon
    if width:
        kwargs["width"] = width
    return ft.TextField(**kwargs)


def accent_card(content: ft.Control, accent_color: str = "#1e88e5") -> ft.Container:
    """Card with a left-side colored accent bar."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    width=4, bgcolor=accent_color, border_radius=_br_only(tl=12, bl=12)
                ),
                ft.Container(
                    content=content,
                    expand=True,
                    padding=_psym(horizontal=14, vertical=14),
                ),
            ],
            spacing=0,
        ),
        bgcolor=CARD_BG,
        border_radius=_br(12),
        margin=_m(bottom=12),
        shadow=ft.BoxShadow(blur_radius=10, color="#00000030", offset=ft.Offset(0, 3)),
    )


# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════
def main(page: ft.Page):
    # ── Page Config ──
    page.title = "Invoice Designer"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.bgcolor = SURFACE
    page.window.width = 440
    page.window.height = 830
    page.window.min_width = 380
    page.window.min_height = 600
    page.padding = 0

    defaults = data_manager.load_default_company_info()
    items_list = []

    # ── INPUT FIELDS ──
    comp_name_input = styled_field(
        "Company Name", defaults.get("company_name", ""), icon=ft.Icons.BUSINESS
    )
    comp_addr_input = styled_field(
        "Address", defaults.get("company_address", ""), icon=ft.Icons.LOCATION_ON
    )
    comp_email_input = styled_field(
        "Email", defaults.get("company_email", ""), icon=ft.Icons.EMAIL
    )
    comp_phone_input = styled_field(
        "Phone", defaults.get("company_phone", ""), icon=ft.Icons.PHONE
    )
    comp_web_input = styled_field(
        "Website", defaults.get("company_website", ""), icon=ft.Icons.LANGUAGE
    )
    comp_footer_input = styled_field(
        "Footer Note", defaults.get("footer_note", ""), icon=ft.Icons.STICKY_NOTE_2
    )

    recipient_name_input = styled_field(
        "Client Name / Company *", hint="Required", icon=ft.Icons.PERSON
    )
    recipient_addr_input = styled_field(
        "Client Address (Optional)",
        icon=ft.Icons.HOME,
        multiline=True,
        min_lines=2,
        max_lines=4,
    )

    invoice_title_input = styled_field(
        "Invoice Title", "Invoice", icon=ft.Icons.RECEIPT_LONG
    )
    invoice_date_input = styled_field(
        "Invoice Date (DD-MM-YYYY)",
        format_date(datetime.datetime.now()),
        icon=ft.Icons.CALENDAR_TODAY,
    )
    billing_period_input = styled_field("Billing Period", icon=ft.Icons.DATE_RANGE)

    auto_no_switch = ft.Switch(
        value=True,
        active_color=ACCENT,
        label="",
        inactive_track_color=DIVIDER,
        width=44,
    )
    counter_input = styled_field("Counter", "1", width=80)
    invoice_no_input = styled_field("Invoice Number", disabled=True, icon=ft.Icons.TAG)

    item_desc_input = styled_field("Item Description", hint="e.g. Item", expand=True)
    item_qty_input = styled_field("Qty", "0", width=72)
    item_price_input = styled_field("Price (IDR)", "20000", width=130)
    item_date_input = styled_field(
        "Item Date", format_date(datetime.datetime.now()), width=140, disabled=True
    )
    item_date_checkbox = ft.Checkbox(
        value=False,
        fill_color=ACCENT,
        check_color="white",
        label="Include Date",
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12),
    )

    tax_rate_input = styled_field("Tax Rate (%)", "0.5", width=100)
    tax_treatment_dropdown = ft.Dropdown(
        label="Tax Treatment",
        value="Reverse Charge",
        options=[
            ft.dropdown.Option("Reverse Charge"),
            ft.dropdown.Option("Standard Charge"),
        ],
        border_color=DIVIDER,
        focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        border_radius=10,
        content_padding=_psym(horizontal=14, vertical=10),
        expand=True,
    )
    tax_treatment_dropdown.on_change = lambda e: update_calculations()

    # ── TOTALS DISPLAY ──
    subtotal_lbl = ft.Text(
        "IDR 0,00", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY
    )
    tax_title_lbl = ft.Text("Tax (0.5%):", size=13, color=TEXT_SECONDARY)
    tax_val_lbl = ft.Text("IDR (0,00)", size=13, color=TEXT_SECONDARY)
    total_due_lbl = ft.Text(
        "IDR 0,00", size=22, weight=ft.FontWeight.BOLD, color=SUCCESS
    )

    # ── ITEMS LISTVIEW ──
    items_list_view = ft.ListView(
        expand=True, spacing=8, padding=_psym(horizontal=4, vertical=4)
    )
    item_count_badge = ft.Text("0 items", size=11, color=TEXT_SECONDARY)

    # ── REACTIVE LOGIC ──
    def trigger_billing_period_auto_calc():
        dt = parse_date(invoice_date_input.value)
        if dt:
            billing_period_input.value = (
                f"{INDONESIAN_MONTHS.get(dt.month, dt.strftime('%B'))} {dt.year}"
            )
            billing_period_input.update()

    def trigger_invoice_auto_gen():
        if not auto_no_switch.value:
            return
        dt = parse_date(invoice_date_input.value)
        date_token = (
            dt.strftime("%Y%m") if dt else datetime.datetime.now().strftime("%Y%m")
        )
        initials = get_client_initials(recipient_name_input.value)
        try:
            counter = (
                int(counter_input.value.strip()) if counter_input.value.strip() else 1
            )
        except ValueError:
            counter = 1
        invoice_no_input.value = f"INV-{date_token}-{initials}-{counter:03d}"
        invoice_no_input.update()

    def toggle_invoice_auto(e):
        invoice_no_input.disabled = auto_no_switch.value
        counter_input.visible = auto_no_switch.value
        invoice_no_input.update()
        counter_input.update()
        if auto_no_switch.value:
            trigger_invoice_auto_gen()

    def toggle_item_date(e):
        item_date_input.disabled = not item_date_checkbox.value
        item_date_input.update()

    recipient_name_input.on_change = lambda e: trigger_invoice_auto_gen()
    invoice_date_input.on_change = lambda e: (
        trigger_billing_period_auto_calc(),
        trigger_invoice_auto_gen(),
    )
    counter_input.on_change = lambda e: trigger_invoice_auto_gen()
    auto_no_switch.on_change = toggle_invoice_auto
    item_date_checkbox.on_change = toggle_item_date
    tax_rate_input.on_change = lambda e: update_calculations()

    # ── CALCULATIONS ──
    def update_calculations():
        subtotal = sum(float(i["qty"]) * float(i["price"]) for i in items_list)
        try:
            tax_rate = float(tax_rate_input.value.strip() or 0)
        except ValueError:
            tax_rate = 0.0
        tax_amt = subtotal * (tax_rate / 100)
        if tax_treatment_dropdown.value == "Reverse Charge":
            total = subtotal - tax_amt
            tax_disp = f"({invoice_generator.format_idr(tax_amt)})"
        else:
            total = subtotal + tax_amt
            tax_disp = invoice_generator.format_idr(tax_amt)
        subtotal_lbl.value = f"IDR {invoice_generator.format_idr(subtotal)}"
        tax_title_lbl.value = f"Tax ({tax_rate}%):"
        tax_val_lbl.value = f"IDR {tax_disp}"
        total_due_lbl.value = f"IDR {invoice_generator.format_idr(total)}"
        subtotal_lbl.update()
        tax_title_lbl.update()
        tax_val_lbl.update()
        total_due_lbl.update()

    # ── ITEM LIST ──
    def refresh_items_list():
        items_list_view.controls.clear()
        count = len(items_list)
        item_count_badge.value = f"{count} item{'s' if count != 1 else ''}"
        try:
            item_count_badge.update()
        except Exception:
            pass

        if not items_list:
            items_list_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.RECEIPT_LONG_OUTLINED, color=DIVIDER, size=40
                            ),
                            ft.Text(
                                "No items added yet", color=TEXT_SECONDARY, size=13
                            ),
                            ft.Text(
                                "Use the form above to add items.",
                                color=DIVIDER,
                                size=11,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    alignment=ft.Alignment(0, 0),
                    height=130,
                )
            )
        else:
            for idx, item in enumerate(items_list):
                desc = item["desc"]
                if item["include_date"] and item["date"]:
                    desc = f"{desc} — {item['date']}"
                qty = item["qty"]
                qty_s = str(int(qty)) if qty == int(qty) else f"{qty:.2f}"
                amt = qty * item["price"]

                card = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    str(idx + 1),
                                    size=11,
                                    color="white",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=ACCENT,
                                width=26,
                                height=26,
                                border_radius=13,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            desc,
                                            size=13,
                                            weight=ft.FontWeight.W_500,
                                            color=TEXT_PRIMARY,
                                            no_wrap=False,
                                        ),
                                        ft.Text(
                                            f"Qty {qty_s}  ×  IDR {invoice_generator.format_idr(item['price'])}",
                                            size=11,
                                            color=TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                                expand=True,
                            ),
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            invoice_generator.format_idr(amt),
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color="white",
                                        ),
                                        bgcolor=ACCENT_DARK,
                                        border_radius=8,
                                        padding=_psym(horizontal=8, vertical=4),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                        icon_size=18,
                                        icon_color=DANGER,
                                        tooltip="Delete item",
                                        on_click=lambda e, i=idx: delete_item(i),
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    bgcolor=CARD_BG,
                    border_radius=10,
                    padding=_psym(horizontal=12, vertical=10),
                    margin=_m(bottom=8),
                    shadow=ft.BoxShadow(
                        blur_radius=6, color="#00000020", offset=ft.Offset(0, 2)
                    ),
                )
                items_list_view.controls.append(card)

        items_list_view.update()

    def delete_item(idx):
        if 0 <= idx < len(items_list):
            del items_list[idx]
            refresh_items_list()
            update_calculations()

    # ── SNACKBAR ──
    def show_snack(msg: str, color: str = "#1e88e5"):
        icon_name = (
            ft.Icons.CHECK_CIRCLE if color == SUCCESS else ft.Icons.ERROR_OUTLINE
        )
        page.open(
            ft.SnackBar(
                content=ft.Row(
                    [
                        ft.Icon(icon_name, color="white", size=16),
                        ft.Text(msg, color="white", size=13),
                    ],
                    spacing=8,
                    tight=True,
                ),
                bgcolor=color,
                duration=2500,
            )
        )

    # ── ADD ITEM ──
    def add_item(e):
        desc = item_desc_input.value.strip()
        if not desc:
            show_snack("Item description is required!", DANGER)
            return
        try:
            qty = float(item_qty_input.value or 0)
            if qty < 0:
                raise ValueError
        except ValueError:
            show_snack("Quantity must be a positive number!", DANGER)
            return
        try:
            price = float(item_price_input.value or 20000)
            if price < 0:
                raise ValueError
        except ValueError:
            show_snack("Price must be a positive number!", DANGER)
            return

        normalized_date = ""
        if item_date_checkbox.value:
            dt = parse_date(item_date_input.value)
            if not dt:
                show_snack("Date must be DD-MM-YYYY format!", DANGER)
                return
            normalized_date = format_date(dt)
            item_date_input.value = format_date(dt + datetime.timedelta(days=1))
            item_date_input.update()

        items_list.append(
            {
                "desc": desc,
                "qty": qty,
                "price": price,
                "include_date": item_date_checkbox.value,
                "date": normalized_date,
            }
        )
        refresh_items_list()
        update_calculations()
        item_desc_input.focus()
        show_snack(f"Added: '{desc}'", SUCCESS)

    # ── GATHER DATA ──
    def gather_invoice_data():
        try:
            tax_rate = float(tax_rate_input.value.strip() or 0)
        except ValueError:
            tax_rate = 0.0
        return {
            "invoice_title": invoice_title_input.value,
            "invoice_no": invoice_no_input.value,
            "invoice_date": invoice_date_input.value,
            "company_name": comp_name_input.value,
            "company_address": comp_addr_input.value,
            "company_email": comp_email_input.value,
            "company_phone": comp_phone_input.value,
            "company_website": comp_web_input.value,
            "footer_note": comp_footer_input.value,
            "recipient_name": recipient_name_input.value,
            "recipient_address": recipient_addr_input.value,
            "billing_period": billing_period_input.value,
            "items": items_list,
            "tax_rate": tax_rate,
            "tax_treatment": "reverse"
            if tax_treatment_dropdown.value == "Reverse Charge"
            else "charge",
            "invoice_no_auto": auto_no_switch.value,
            "invoice_counter": counter_input.value,
            "notes": "",
        }

    # ── FILE OPS ──
    def save_defaults(e):
        info = {
            "company_name": comp_name_input.value,
            "company_address": comp_addr_input.value,
            "company_email": comp_email_input.value,
            "company_phone": comp_phone_input.value,
            "company_website": comp_web_input.value,
            "footer_note": comp_footer_input.value,
        }
        if data_manager.save_default_company_info(info):
            show_snack("Profile saved as default!", SUCCESS)
        else:
            show_snack("Failed to save defaults.", DANGER)

    def trigger_load_dialog(e):
        from tkinter import filedialog

        path = filedialog.askopenfilename(filetypes=[("Invoice Data Files", "*.json")])
        if not path:
            return
        data = data_manager.load_invoice(path)
        if not data:
            show_snack("Could not load invoice data.", DANGER)
            return
        invoice_title_input.value = data.get("invoice_title", "Invoice")
        invoice_no_input.value = data.get("invoice_no", "")
        invoice_date_input.value = data.get("invoice_date", "")
        billing_period_input.value = data.get("billing_period", "")
        comp_name_input.value = data.get("company_name", "")
        comp_addr_input.value = data.get("company_address", "")
        comp_email_input.value = data.get("company_email", "")
        comp_phone_input.value = data.get("company_phone", "")
        comp_web_input.value = data.get("company_website", "")
        comp_footer_input.value = data.get("footer_note", "")
        recipient_name_input.value = data.get("recipient_name", "")
        recipient_addr_input.value = data.get("recipient_address", "")
        tax_rate_input.value = str(data.get("tax_rate", 0.5))
        tax_code = data.get("tax_treatment", "reverse")
        tax_treatment_dropdown.value = (
            "Reverse Charge" if tax_code == "reverse" else "Standard Charge"
        )
        auto_no_switch.value = data.get("invoice_no_auto", True)
        counter_input.value = str(data.get("invoice_counter", 1))
        nonlocal items_list
        items_list = data.get("items", [])
        invoice_no_input.disabled = auto_no_switch.value
        counter_input.visible = auto_no_switch.value
        refresh_items_list()
        update_calculations()
        page.update()
        show_snack("Invoice loaded!", SUCCESS)

    def trigger_save_dialog(e):
        if not recipient_name_input.value.strip():
            show_snack("Client Name is required to save!", DANGER)
            return
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Invoice Data Files", "*.json")]
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        if data_manager.save_invoice(path, gather_invoice_data()):
            show_snack("Invoice saved!", SUCCESS)
        else:
            show_snack("Save failed.", DANGER)

    def trigger_preview(e):
        if not recipient_name_input.value.strip():
            show_snack("Client Name is required!", DANGER)
            return
        success, preview_path = invoice_generator.preview_in_browser(
            gather_invoice_data()
        )
        if success:
            page.launch_url(os.path.abspath(preview_path))
            show_snack("Preview opened in browser!", ACCENT)
        else:
            show_snack(f"Preview failed: {preview_path}", DANGER)

    def show_print_help():
        def close_dlg(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.PRINT, color=ACCENT),
                    ft.Text(
                        "Print/Save Invoice",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY,
                    ),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        "The HTML invoice has been opened in your browser.",
                        color=TEXT_SECONDARY,
                        size=13,
                    ),
                    ft.Divider(color=DIVIDER, height=16),
                    ft.Text(
                        "On Android:", color=ACCENT, size=12, weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "1. Tap the browser menu (three dots).\n2. Tap 'Share' → 'Print'.\n3. Select 'Save as PDF'.",
                        color=TEXT_SECONDARY,
                        size=12,
                    ),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=CARD_BG,
            actions=[
                ft.TextButton(
                    "Got it", style=ft.ButtonStyle(color=ACCENT), on_click=close_dlg
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def trigger_pdf_export(e):
        if not recipient_name_input.value.strip():
            show_snack("Client Name is required!", DANGER)
            return
        if os.name == "nt":
            from tkinter import filedialog

            suggested = f"invoice_{invoice_no_input.value}.pdf".replace("-", "_")
            path = filedialog.asksaveasfilename(
                initialfile=suggested,
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
            )
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            success, msg = invoice_generator.generate_pdf(gather_invoice_data(), path)
            if success:
                show_snack(msg, SUCCESS)
                if auto_no_switch.value:
                    try:
                        counter_input.value = str(int(counter_input.value) + 1)
                        counter_input.update()
                        trigger_invoice_auto_gen()
                    except Exception:
                        pass
            else:
                page.launch_url(os.path.abspath(msg))
                show_print_help()
        else:
            success, msg = invoice_generator.generate_pdf(
                gather_invoice_data(), "temp_render.pdf"
            )
            page.launch_url(os.path.abspath(msg))
            show_print_help()

    # ── THEME TOGGLE ──
    theme_icon_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        icon_color="white",
        icon_size=20,
        tooltip="Toggle theme",
    )

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#f4f6fb"
            theme_icon_btn.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = SURFACE
            theme_icon_btn.icon = ft.Icons.LIGHT_MODE
        page.update()

    theme_icon_btn.on_click = toggle_theme

    # ══════════════════════════════════════════════════
    #  VIEW 1 — PROFILE
    # ══════════════════════════════════════════════════
    view_profile = ft.ListView(
        controls=[
            ft.Container(height=12),
            # Company section
            accent_card(
                ft.Column(
                    [
                        section_header("YOUR COMPANY", ft.Icons.STORE, ACCENT),
                        comp_name_input,
                        ft.Container(height=6),
                        comp_addr_input,
                        ft.Container(height=6),
                        ft.Row([comp_email_input, comp_phone_input], spacing=8),
                        ft.Container(height=6),
                        comp_web_input,
                        ft.Container(height=6),
                        comp_footer_input,
                        ft.Container(height=10),
                        ft.Button(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.SAVE_ALT, size=15, color="white"),
                                    ft.Text(
                                        "Save as Default Profile",
                                        size=13,
                                        color="white",
                                    ),
                                ],
                                spacing=6,
                                tight=True,
                            ),
                            on_click=save_defaults,
                            bgcolor=ACCENT_DARK,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=_psym(horizontal=16, vertical=12),
                            ),
                            elevation=3,
                            expand=True,
                        ),
                    ],
                    spacing=0,
                )
            ),
            # Client section
            accent_card(
                ft.Column(
                    [
                        section_header(
                            "BILL TO (CLIENT)", ft.Icons.PERSON_PIN, WARNING
                        ),
                        recipient_name_input,
                        ft.Container(height=6),
                        recipient_addr_input,
                    ],
                    spacing=0,
                ),
                accent_color=WARNING,
            ),
            # Invoice meta
            accent_card(
                ft.Column(
                    [
                        section_header(
                            "INVOICE SETTINGS", ft.Icons.RECEIPT_LONG, ACCENT_LIGHT
                        ),
                        invoice_title_input,
                        ft.Container(height=6),
                        invoice_date_input,
                        ft.Container(height=6),
                        billing_period_input,
                        ft.Container(height=12),
                        # Auto-number toggle
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Auto-Generate Number",
                                                size=13,
                                                color=TEXT_PRIMARY,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                            ft.Text(
                                                "From client + date + counter",
                                                size=11,
                                                color=TEXT_SECONDARY,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    auto_no_switch,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=SURFACE_ALT,
                            border_radius=10,
                            padding=_psym(horizontal=12, vertical=10),
                        ),
                        ft.Container(height=8),
                        ft.Row([invoice_no_input, counter_input], spacing=8),
                    ],
                    spacing=0,
                ),
                accent_color=ACCENT_LIGHT,
            ),
            ft.Container(height=24),
        ],
        spacing=0,
        padding=_msym(horizontal=16),
        expand=True,
    )

    # ══════════════════════════════════════════════════
    #  VIEW 2 — ITEMS
    # ══════════════════════════════════════════════════
    view_items = ft.Column(
        [
            # Add item form card
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ADD_BOX, color=ACCENT, size=18),
                                ft.Text(
                                    "ADD NEW LINE ITEM",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ACCENT,
                                ),
                                ft.Container(expand=True),
                                item_count_badge,
                            ]
                        ),
                        ft.Container(height=10),
                        item_desc_input,
                        ft.Container(height=8),
                        ft.Row([item_qty_input, item_price_input], spacing=10),
                        ft.Container(height=8),
                        ft.Row(
                            [item_date_checkbox, item_date_input],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=10),
                        ft.Button(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.ADD_CIRCLE_OUTLINE,
                                        size=16,
                                        color="white",
                                    ),
                                    ft.Text(
                                        "Add Item to Invoice", size=13, color="white"
                                    ),
                                ],
                                tight=True,
                                spacing=6,
                            ),
                            on_click=add_item,
                            bgcolor=ACCENT,
                            expand=True,
                            elevation=4,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=_psym(horizontal=16, vertical=13),
                            ),
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=CARD_BG,
                border_radius=_br(12),
                padding=_pall(16),
                margin=_m(bottom=12),
                border=ft.border.Border(left=ft.border.BorderSide(4, ACCENT)),
                shadow=ft.BoxShadow(
                    blur_radius=10, color="#00000030", offset=ft.Offset(0, 3)
                ),
            ),
            # Items list
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.LIST_ALT, color=TEXT_SECONDARY, size=16
                                ),
                                ft.Text(
                                    "CURRENT LINE ITEMS",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_SECONDARY,
                                ),
                            ],
                            spacing=6,
                        ),
                        ft.Container(height=8),
                        items_list_view,
                    ],
                    spacing=0,
                    expand=True,
                ),
                expand=True,
                bgcolor=SURFACE_ALT,
                border_radius=_br(12),
                padding=_pall(12),
            ),
        ],
        spacing=0,
        expand=True,
    )

    view_items_container = ft.Container(
        content=view_items, padding=_psym(horizontal=16, vertical=12), expand=True
    )

    # ══════════════════════════════════════════════════
    #  VIEW 3 — SUMMARY & ACTIONS
    # ══════════════════════════════════════════════════
    view_totals = ft.ListView(
        controls=[
            ft.Container(height=12),
            # Tax configuration
            accent_card(
                ft.Column(
                    [
                        section_header("TAX CONFIGURATION", ft.Icons.PERCENT, WARNING),
                        ft.Row([tax_rate_input, tax_treatment_dropdown], spacing=10),
                    ],
                    spacing=0,
                ),
                accent_color=WARNING,
            ),
            # Calculation summary
            ft.Container(
                content=ft.Column(
                    [
                        section_header(
                            "CALCULATION SUMMARY", ft.Icons.CALCULATE, SUCCESS
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    "Subtotal",
                                    size=13,
                                    color=TEXT_SECONDARY,
                                    expand=True,
                                ),
                                subtotal_lbl,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=4),
                        ft.Row(
                            [tax_title_lbl, tax_val_lbl],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            height=1, bgcolor=DIVIDER, margin=_msym(vertical=12)
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    "TOTAL DUE",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_PRIMARY,
                                ),
                                total_due_lbl,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=CARD_BG,
                border_radius=_br(12),
                padding=_pall(16),
                margin=_m(bottom=12),
                border=ft.border.Border(left=ft.border.BorderSide(4, SUCCESS)),
                shadow=ft.BoxShadow(
                    blur_radius=10, color="#00000030", offset=ft.Offset(0, 3)
                ),
            ),
            # File management
            accent_card(
                ft.Column(
                    [
                        section_header("FILE MANAGEMENT", ft.Icons.FOLDER_OPEN, ACCENT),
                        ft.Row(
                            [
                                ft.Button(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.FOLDER_OPEN,
                                                size=15,
                                                color=TEXT_PRIMARY,
                                            ),
                                            ft.Text(
                                                "Open JSON", size=13, color=TEXT_PRIMARY
                                            ),
                                        ],
                                        tight=True,
                                        spacing=6,
                                    ),
                                    on_click=trigger_load_dialog,
                                    bgcolor=SURFACE_ALT,
                                    expand=True,
                                    elevation=1,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        padding=_psym(horizontal=12, vertical=12),
                                    ),
                                ),
                                ft.Button(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.SAVE,
                                                size=15,
                                                color=TEXT_PRIMARY,
                                            ),
                                            ft.Text(
                                                "Save JSON", size=13, color=TEXT_PRIMARY
                                            ),
                                        ],
                                        tight=True,
                                        spacing=6,
                                    ),
                                    on_click=trigger_save_dialog,
                                    bgcolor=SURFACE_ALT,
                                    expand=True,
                                    elevation=1,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        padding=_psym(horizontal=12, vertical=12),
                                    ),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=0,
                )
            ),
            # Export actions
            accent_card(
                ft.Column(
                    [
                        section_header("EXPORT", ft.Icons.SEND, ACCENT_LIGHT),
                        ft.Button(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.OPEN_IN_BROWSER, size=16, color="white"
                                    ),
                                    ft.Text(
                                        "Browser HTML Preview", size=13, color="white"
                                    ),
                                ],
                                tight=True,
                                spacing=8,
                            ),
                            on_click=trigger_preview,
                            bgcolor=WARNING,
                            expand=True,
                            elevation=4,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=_psym(horizontal=16, vertical=13),
                            ),
                        ),
                        ft.Container(height=10),
                        ft.Button(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.PICTURE_AS_PDF, size=16, color="white"
                                    ),
                                    ft.Text(
                                        "Export A4 PDF Document",
                                        size=13,
                                        color="white",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                tight=True,
                                spacing=8,
                            ),
                            on_click=trigger_pdf_export,
                            bgcolor=SUCCESS,
                            expand=True,
                            elevation=6,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=_psym(horizontal=16, vertical=14),
                            ),
                        ),
                    ],
                    spacing=0,
                ),
                accent_color=ACCENT_LIGHT,
            ),
            ft.Container(height=24),
        ],
        spacing=0,
        padding=_msym(horizontal=16),
        expand=True,
    )

    # ══════════════════════════════════════════════════
    #  GRADIENT HEADER BANNER
    # ══════════════════════════════════════════════════
    header_banner = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Invoice Designer", size=12, color="#bbdefb"),
                        ],
                        spacing=2,
                    )
                ),
                ft.Container(expand=True),
                theme_icon_btn,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
            colors=[ACCENT_DARK, ACCENT, "#1976d2"],
        ),
        padding=_p(left=20, right=12, top=14, bottom=14),
    )

    # ══════════════════════════════════════════════════
    #  TAB BAR ASSEMBLY
    # ══════════════════════════════════════════════════
    tabs = ft.Tabs(
        length=3,
        selected_index=0,
        animation_duration=250,
        expand=True,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Profile", icon=ft.Icons.PERSON_OUTLINE),
                        ft.Tab(label="Items", icon=ft.Icons.RESTAURANT_MENU),
                        ft.Tab(label="Summary", icon=ft.Icons.SUMMARIZE),
                    ],
                    divider_color=DIVIDER,
                    indicator_color=ACCENT,
                    label_color=ACCENT,
                    unselected_label_color=TEXT_SECONDARY,
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        view_profile,
                        view_items_container,
                        view_totals,
                    ],
                ),
            ],
        ),
    )

    # ── ASSEMBLE PAGE ──
    page.add(
        ft.Column(
            [header_banner, ft.Container(content=tabs, expand=True, bgcolor=SURFACE)],
            spacing=0,
            expand=True,
        )
    )

    trigger_billing_period_auto_calc()
    trigger_invoice_auto_gen()
    update_calculations()
    refresh_items_list()


if __name__ == "__main__":
    ft.run(main)
