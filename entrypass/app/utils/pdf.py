"""
PDF Ticket Generation - HACKFEST2K26
=====================================

Compact half-page ticket with JetBrains Mono font.
Industrial grey aesthetic, centered on page.
"""

import os
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ========== EVENT CONFIGURATION ==========
EVENT = {
    'name': 'HACKFEST2K26',
    'tagline': '36-Hour Hackathon',
    'college': 'M. Kumarasamy College of Engineering, Karur',
    'sponsors': 'IBM  •  Adroit Technologies',
    'schedule': '20 Feb 9:00 AM – 21 Feb 9:00 AM',
}

# ========== GREY INDUSTRIAL PALETTE ==========
GREY_DARK = colors.HexColor('#2a2a2a')
GREY_MED = colors.HexColor('#5a5a5a')
GREY_LIGHT = colors.HexColor('#9a9a9a')
GREY_VLIGHT = colors.HexColor('#d0d0d0')
GREY_BG = colors.HexColor('#e8e8e8')
GREY_PANEL = colors.HexColor('#f2f2f2')
WHITE = colors.HexColor('#ffffff')


def register_fonts():
    """Register JetBrains Mono font if available, fallback to Courier."""
    try:
        # Try to register JetBrains Mono (if available in system)
        pdfmetrics.registerFont(TTFont('JetBrainsMono', 'JetBrainsMono-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('JetBrainsMono-Bold', 'JetBrainsMono-Bold.ttf'))
        return 'JetBrainsMono'
    except:
        # Fallback to Courier (monospace font available in ReportLab)
        return 'Courier'


def generate_ticket_pdf(ticket_data: dict) -> BytesIO:
    """
    Generate compact half-page ticket PDF in memory (BytesIO).
    No files are stored on disk.
    
    Layout: Horizontal, occupies ~50% of page height, centered.
    Left: Event details and participant info
    Right: QR code in grey panel
    
    Returns:
        BytesIO buffer containing the PDF
    """
    ticket_id = ticket_data.get('ticket_id', 'UNKNOWN')
    
    # Fallback if reportlab not available
    if not HAS_REPORTLAB:
        buf = BytesIO()
        buf.write(f"HACKFEST2K26\nTeam: {ticket_data.get('team_name')}\nID: {ticket_data.get('user_id')}\nTicket: {ticket_id}".encode())
        buf.seek(0)
        return buf
    
    buf = BytesIO()
    
    # ========== PAGE SETUP - LANDSCAPE A4 ==========
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    
    # Register fonts
    font_family = register_fonts()
    font_bold = font_family + '-Bold' if font_family == 'JetBrainsMono' else font_family
    
    # ========== TICKET DIMENSIONS - 50% OF PAGE HEIGHT ==========
    ticket_height = page_height * 0.50  # Half page height
    ticket_width = page_width * 0.85    # 85% of page width
    
    # Center ticket on page
    ticket_x = (page_width - ticket_width) / 2
    ticket_y = (page_height - ticket_height) / 2
    
    # ========== BACKGROUND - LIGHT GREY PAGE ==========
    c.setFillColor(GREY_BG)
    c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
    
    # ========== TICKET CONTAINER ==========
    # White ticket background
    c.setFillColor(WHITE)
    c.rect(ticket_x, ticket_y, ticket_width, ticket_height, fill=True, stroke=False)
    
    # ========== SUBTLE VISUAL ENHANCEMENTS ==========
    
    # 1. Very light grey dot pattern background (subtle texture)
    c.setFillColor(colors.HexColor('#f8f8f8'))
    dot_spacing = 12
    dot_size = 0.8
    for x in range(int(ticket_x), int(ticket_x + ticket_width), dot_spacing):
        for y in range(int(ticket_y), int(ticket_y + ticket_height), dot_spacing):
            c.circle(x, y, dot_size, fill=True, stroke=False)
    
    # 2. Thin vertical accent bar on far left edge (dark grey)
    accent_bar_width = 3
    c.setFillColor(GREY_DARK)
    c.rect(ticket_x, ticket_y, accent_bar_width, ticket_height, fill=True, stroke=False)
    
    # Thin border
    c.setStrokeColor(GREY_VLIGHT)
    c.setLineWidth(0.5)
    c.rect(ticket_x, ticket_y, ticket_width, ticket_height, fill=False, stroke=True)
    
    # ========== LAYOUT ZONES ==========
    # Left: 65% - Details
    # Right: 35% - QR Scan Zone
    
    left_width = ticket_width * 0.65
    right_width = ticket_width * 0.35
    
    left_x = ticket_x + 20
    right_x = ticket_x + left_width
    
    # ========== VERTICAL DIVIDER ==========
    c.setStrokeColor(GREY_VLIGHT)
    c.setLineWidth(0.5)
    c.setDash(3, 2)
    c.line(right_x, ticket_y + 10, right_x, ticket_y + ticket_height - 10)
    c.setDash()
    
    # ========== LEFT SECTION - EVENT & DETAILS ==========
    content_y = ticket_y + ticket_height - 25
    
    # Event name
    c.setFillColor(GREY_DARK)
    c.setFont(font_bold, 18)
    c.drawString(left_x, content_y, EVENT['name'])
    
    # 3. Small coding glyph (</>) near event name (hackathon theme)
    c.setFont(font_family, 12)
    c.setFillColor(GREY_LIGHT)
    glyph_x = left_x + c.stringWidth(EVENT['name'], font_bold, 18) + 12
    c.drawString(glyph_x, content_y + 2, "</>")
    
    # 4. College logo (small, top right area)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'mkcelogo.png')
    if os.path.exists(logo_path):
        try:
            logo_height = 25
            logo_width = 25  # Will maintain aspect ratio
            logo_x = right_x - logo_width - 25
            logo_y = content_y - 2
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        except:
            pass  # Silently skip if logo can't be loaded

    
    # Tagline
    content_y -= 18
    c.setFont(font_family, 9)
    c.setFillColor(GREY_MED)
    c.drawString(left_x, content_y, EVENT['tagline'])
    
    # "ENTRY PASS" label
    content_y -= 14
    c.setFont(font_bold, 7)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "ENTRY PASS")
    
    # Thin separator
    content_y -= 10
    c.setStrokeColor(GREY_VLIGHT)
    c.setLineWidth(0.5)
    c.line(left_x, content_y, right_x - 20, content_y)
    
    # Team Name
    content_y -= 18
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "TEAM NAME")
    
    content_y -= 12
    c.setFont(font_bold, 11)
    c.setFillColor(GREY_DARK)
    team_name = ticket_data.get('team_name', 'Team Name')
    if len(team_name) > 35:
        team_name = team_name[:35] + '...'
    c.drawString(left_x, content_y, team_name)
    
    # Team Code (HF26XXXXX) - Prominent for manual entry
    content_y -= 20
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "TEAM CODE (For Manual Entry)")
    
    content_y -= 12
    c.setFont(font_bold, 14)
    c.setFillColor(colors.HexColor('#6366f1'))  # Indigo color for prominence
    c.drawString(left_x, content_y, ticket_data.get('user_id', 'N/A'))
    
    # College Name & Team Size (two columns)
    content_y -= 22
    col2_x = left_x + 240
    
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "COLLEGE")
    c.drawString(col2_x, content_y, "TEAM SIZE")
    
    content_y -= 11
    c.setFont(font_bold, 9)
    c.setFillColor(GREY_DARK)
    college_name = ticket_data.get('college_name', 'N/A')
    if len(college_name) > 28:
        college_name = college_name[:28] + '...'
    c.drawString(left_x, content_y, college_name)
    c.drawString(col2_x, content_y, str(ticket_data.get('team_size', '3')) + " Members")
    
    # Team Leader Email
    content_y -= 18
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "TEAM LEADER EMAIL")
    
    content_y -= 10
    c.setFont(font_family, 8)
    c.setFillColor(GREY_DARK)
    email = ticket_data.get('team_leader_email', 'N/A')
    if len(email) > 40:
        email = email[:40] + '...'
    c.drawString(left_x, content_y, email)
    
    # Event Schedule
    content_y -= 18
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "EVENT SCHEDULE")
    
    content_y -= 10
    c.setFont(font_family, 8)
    c.setFillColor(GREY_DARK)
    c.drawString(left_x, content_y, EVENT['schedule'])
    
    # Sponsors (small, muted)
    content_y -= 16
    c.setFont(font_family, 6)
    c.setFillColor(GREY_LIGHT)
    c.drawString(left_x, content_y, "SPONSORS")
    
    content_y -= 9
    c.setFont(font_family, 7)
    c.drawString(left_x, content_y, EVENT['sponsors'])
    
    # ========== RIGHT SECTION - QR SCAN ZONE ==========
    right_center_x = right_x + (right_width / 2)
    
    # Grey panel background
    panel_padding = 15
    c.setFillColor(GREY_PANEL)
    c.rect(right_x + 5, ticket_y + 5, right_width - 10, ticket_height - 10, fill=True, stroke=False)
    
    # "SCAN AT ENTRY" label
    label_y = ticket_y + ticket_height - 30
    c.setFillColor(GREY_MED)
    c.setFont(font_bold, 7)
    c.drawCentredString(right_center_x, label_y, "SCAN AT ENTRY")
    
    # QR Code - centered vertically in panel
    qr_size = 110
    qr_x = right_center_x - (qr_size / 2)
    qr_y = ticket_y + (ticket_height / 2) - (qr_size / 2)
    
    # White background for QR
    c.setFillColor(WHITE)
    c.rect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, fill=True, stroke=False)
    
    # Thin border
    c.setStrokeColor(GREY_VLIGHT)
    c.setLineWidth(0.5)
    c.rect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, fill=False, stroke=True)
    
    # Draw QR code
    qr_path = ticket_data.get('qr_path')
    if qr_path and os.path.exists(qr_path):
        try:
            c.drawImage(qr_path, qr_x, qr_y, qr_size, qr_size)
        except:
            c.setFillColor(GREY_LIGHT)
            c.setFont(font_family, 8)
            c.drawCentredString(right_center_x, qr_y + qr_size/2, "QR CODE")
    else:
        c.setFillColor(GREY_LIGHT)
        c.setFont(font_family, 8)
        c.drawCentredString(right_center_x, qr_y + qr_size/2, "QR CODE")
    
    # Ticket ID below QR
    below_qr_y = qr_y - 18
    c.setFillColor(GREY_LIGHT)
    c.setFont(font_family, 6)
    c.drawCentredString(right_center_x, below_qr_y, "TICKET ID")
    
    c.setFillColor(GREY_DARK)
    c.setFont(font_bold, 10)
    c.drawCentredString(right_center_x, below_qr_y - 11, ticket_id)
    
    # ========== FOOTER ==========
    footer_y = ticket_y - 12
    c.setFillColor(GREY_LIGHT)
    c.setFont(font_family, 6)
    footer_text = "This ticket is valid for one-time entry only. QR code will be scanned at the gate."
    c.drawCentredString(page_width / 2, footer_y, footer_text)
    
    # ========== SAVE PDF TO BUFFER ==========
    c.save()
    buf.seek(0)
    return buf
