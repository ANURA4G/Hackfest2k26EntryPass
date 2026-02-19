"""
Bulk Import Script - Import teams from Excel and generate entry pass PDFs
=========================================================================

Reads app.xlsx, creates a ticket for each team, generates QR codes,
builds PDF entry passes, and saves them to static/pdf/<team_name>.pdf
"""

import os
import sys
import uuid
import pandas as pd
from datetime import datetime

# Ensure app packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.json_store import add_ticket, get_all_tickets
from utils.qr import generate_qr_payload, generate_qr_image_tempfile
from utils.pdf import generate_ticket_pdf

# ── Paths ──────────────────────────────────────────────────────
EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.xlsx')
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdf')
os.makedirs(PDF_DIR, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────
def generate_ticket_id() -> str:
    return str(uuid.uuid4())[:8].upper()


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    keepchars = (' ', '_', '-')
    return "".join(c for c in name if c.isalnum() or c in keepchars).strip()


# ── Main ───────────────────────────────────────────────────────
def main():
    # Read Excel
    excel_path = os.path.normpath(EXCEL_PATH)
    if not os.path.exists(excel_path):
        print(f"ERROR: Excel file not found at {excel_path}")
        sys.exit(1)

    df = pd.read_excel(excel_path)
    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]
    print(f"Found {len(df)} rows in Excel\n")

    # Existing team codes to skip duplicates
    existing_codes = {t.get('user_id') for t in get_all_tickets()}

    created = 0
    skipped = 0

    for idx, row in df.iterrows():
        team_code = str(row.get('Team Code', '')).strip()
        team_name = str(row.get('Team Name', '')).strip()

        # Skip rows with missing essentials
        if not team_code or team_code == 'nan' or not team_name or team_name == 'nan':
            print(f"  Row {idx+1}: SKIPPED (missing Team Code or Team Name)")
            skipped += 1
            continue

        team_code_upper = team_code.upper()

        # Skip if already exists
        if team_code_upper in existing_codes:
            print(f"  Row {idx+1}: SKIPPED duplicate code {team_code_upper} ({team_name})")
            skipped += 1
            continue

        # ── Parse row data ──────────────────────────────────
        team_size = int(row.get('Team Size', 3) if pd.notna(row.get('Team Size')) else 3)
        college_name = str(row.get('Institution Name', '')).strip()
        email = str(row.get('Email Address', row.get('Email', ''))).strip()
        if email == 'nan':
            email = ''
        leader_name = str(row.get('Team Leader Name', '')).strip()

        # Build member list from columns
        member_cols = [
            'Team Member 1 Name (Leader)',
            'Team Member 2 Name',
            'Team Member 3 Name',
            'Team Member 4 Name',
        ]
        team_members = []
        for i, col in enumerate(member_cols, start=1):
            name = str(row.get(col, '')).strip()
            if name and name != 'nan':
                team_members.append({
                    'name': name,
                    'position': 'Team Leader' if i == 1 else f'Member {i}',
                    'member_id': i
                })

        # If no members parsed, at least add the leader
        if not team_members and leader_name and leader_name != 'nan':
            team_members.append({
                'name': leader_name,
                'position': 'Team Leader',
                'member_id': 1
            })

        # Extra metadata
        project_domain = str(row.get('Project Domain', '')).strip()
        project_title = str(row.get('Project Title', '')).strip()
        tshirt_sizes = str(row.get('Enter T-Shirt Sizes (Collective Format)', '')).strip()
        food_pref = str(row.get('Food Preference  (Veg / Non-Veg)', '')).strip()
        if food_pref == 'nan':
            food_pref = ''
        if tshirt_sizes == 'nan':
            tshirt_sizes = ''
        if project_domain == 'nan':
            project_domain = ''
        if project_title == 'nan':
            project_title = ''

        # ── Create ticket ───────────────────────────────────
        ticket_id = generate_ticket_id()
        user_id = team_code_upper

        qr_payload = generate_qr_payload(ticket_id, user_id, team_name)

        ticket_data = {
            'ticket_id': ticket_id,
            'user_id': user_id,
            'team_name': team_name,
            'college_name': college_name,
            'team_leader_email': email,
            'team_size': team_size,
            'team_members': team_members,
            'slot': '20 Feb 9:00 AM - 21 Feb 9:00 AM',
            'event_name': 'HACKFEST2K26',
            'qr_payload': qr_payload,
            'project_domain': project_domain,
            'project_title': project_title,
            'tshirt_sizes': tshirt_sizes,
            'food_preference': food_pref,
            'created_at': datetime.now().isoformat(),
            'created_by': 'bulk_import'
        }

        add_ticket(ticket_data)
        existing_codes.add(user_id)

        # ── Generate PDF ────────────────────────────────────
        temp_qr_path = generate_qr_image_tempfile(qr_payload)

        pdf_info = {
            'ticket_id': ticket_id,
            'user_id': user_id,
            'team_name': team_name,
            'college_name': college_name,
            'team_leader_email': email,
            'team_size': team_size,
            'slot': '20 Feb 9:00 AM - 21 Feb 9:00 AM',
            'event_name': 'HACKFEST2K26',
            'qr_path': temp_qr_path
        }

        pdf_buffer = generate_ticket_pdf(pdf_info)

        # Save PDF with team name
        safe_name = sanitize_filename(team_name)
        pdf_filename = f"{safe_name}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)

        with open(pdf_path, 'wb') as f:
            f.write(pdf_buffer.read())

        # Clean up temp QR image
        try:
            os.unlink(temp_qr_path)
        except OSError:
            pass

        created += 1
        print(f"  [{created:3d}] {team_code_upper:12s}  {team_name:30s}  -> {pdf_filename}")

    print(f"\nDone!  Created: {created}  |  Skipped: {skipped}")
    print(f"PDFs saved to: {PDF_DIR}")


if __name__ == '__main__':
    main()
