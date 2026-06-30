"""
Generates the 5 demo contract PDFs into backend/sample_contracts/.
Run once. Checked into the repo so Qdrant can load them on startup.
"""
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUT_DIR = Path(__file__).parent.parent / "sample_contracts"
OUT_DIR.mkdir(exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, spaceAfter=12)
heading_style = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=12, spaceAfter=6)
body_style = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=10, spaceAfter=8, leading=14)


def build_pdf(filename: str, elements: list) -> None:
    path = OUT_DIR / filename
    doc = SimpleDocTemplate(str(path), pagesize=LETTER,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    doc.build(elements)
    print(f"  Written: {path}")


def T(text: str) -> Paragraph:
    return Paragraph(text, title_style)

def H(text: str) -> Paragraph:
    return Paragraph(text, heading_style)

def P(text: str) -> Paragraph:
    return Paragraph(text, body_style)

def SP() -> Spacer:
    return Spacer(1, 0.15 * inch)


# ---------------------------------------------------------------------------
# 1. NDA
# ---------------------------------------------------------------------------
build_pdf("nda_acme_example.pdf", [
    T("MUTUAL NON-DISCLOSURE AGREEMENT"),
    P("This Mutual Non-Disclosure Agreement (the <b>\"Agreement\"</b>) is entered into as of "
      "<b>January 1, 2024</b> (the <b>\"Effective Date\"</b>) by and between:"),
    P("<b>Acme Corp</b>, a Delaware corporation (<b>\"Disclosing Party\"</b>), and "
      "<b>Example LLC</b>, a Delaware limited liability company (<b>\"Receiving Party\"</b>)."),
    SP(),
    H("1. Purpose"),
    P("The parties wish to explore a potential business relationship (the \"Purpose\") and may "
      "disclose confidential information to each other in connection with the Purpose."),
    SP(),
    H("2. Confidential Information"),
    P("\"Confidential Information\" means any information disclosed by one party to the other "
      "that is designated as confidential or that reasonably should be understood to be "
      "confidential given the nature of the information and circumstances of disclosure."),
    SP(),
    H("3. Confidentiality Obligations"),
    P("The Receiving Party agrees to hold all Confidential Information in strict confidence for "
      "a period of <b>five (5) years</b> following the termination of this Agreement. The "
      "Receiving Party shall not disclose Confidential Information to any third party without "
      "the prior written consent of the Disclosing Party."),
    SP(),
    H("4. Termination"),
    P("Either party may terminate this Agreement by providing <b>thirty (30) days</b> prior "
      "written notice to the other party. The confidentiality obligations in Section 3 shall "
      "survive termination of this Agreement for the period stated therein."),
    SP(),
    H("5. Non-Competition"),
    P("During the term of this Agreement and for a period of <b>two (2) years</b> following "
      "termination, the Receiving Party shall not, directly or indirectly, compete with the "
      "Disclosing Party's business operations in any market in which the Disclosing Party "
      "operates as of the Effective Date."),
    SP(),
    H("6. Governing Law"),
    P("This Agreement shall be governed by and construed in accordance with the laws of the "
      "<b>State of Delaware</b>, without regard to its conflict of law provisions."),
    SP(),
    H("7. Entire Agreement"),
    P("This Agreement constitutes the entire agreement between the parties with respect to the "
      "subject matter hereof and supersedes all prior agreements and understandings."),
    SP(),
    P("<b>ACME CORP</b><br/>By: ___________________________<br/>Name: John Smith<br/>"
      "Title: CEO<br/>Date: January 1, 2024"),
    SP(),
    P("<b>EXAMPLE LLC</b><br/>By: ___________________________<br/>Name: Jane Doe<br/>"
      "Title: Managing Member<br/>Date: January 1, 2024"),
])

# ---------------------------------------------------------------------------
# 2. Software Vendor Agreement
# ---------------------------------------------------------------------------
build_pdf("vendor_techcorp_widgets.pdf", [
    T("SOFTWARE VENDOR AGREEMENT"),
    P("This Software Vendor Agreement (the <b>\"Agreement\"</b>) is entered into as of "
      "<b>March 15, 2024</b> (the <b>\"Effective Date\"</b>) by and between:"),
    P("<b>TechCorp Supplies Inc</b>, a California corporation (<b>\"Vendor\"</b>), and "
      "<b>Widgets Manufacturing Co</b>, a California corporation (<b>\"Client\"</b>)."),
    SP(),
    H("1. Services"),
    P("Vendor agrees to provide software development and licensing services to Client as "
      "described in individual Statements of Work executed by both parties."),
    SP(),
    H("2. Payment Terms"),
    P("Client shall pay Vendor monthly invoices within <b>thirty (30) days</b> of receipt "
      "(<b>Net 30</b>). Invoices shall be issued on the first business day of each calendar "
      "month. Late payments shall accrue interest at 1.5% per month."),
    SP(),
    H("3. Term and Termination"),
    P("This Agreement commences on the Effective Date and continues until terminated. Either "
      "party may terminate this Agreement for any reason upon <b>sixty (60) days</b> prior "
      "written notice to the other party. Termination does not relieve Client of outstanding "
      "payment obligations."),
    SP(),
    H("4. Non-Competition"),
    P("During the term of this Agreement, <b>Vendor shall not provide identical or "
      "substantially similar services to any direct competitor of Client</b> without Client's "
      "prior written consent. For purposes of this section, \"direct competitor\" means any "
      "entity that derives more than 30% of its revenue from the same product category as "
      "Client's primary product line."),
    SP(),
    H("5. Intellectual Property"),
    P("All work product developed by Vendor specifically for Client under a Statement of Work "
      "shall be considered work-for-hire and owned exclusively by Client upon full payment."),
    SP(),
    H("6. Limitation of Liability"),
    P("In no event shall either party be liable for indirect, incidental, consequential, or "
      "punitive damages, even if advised of the possibility of such damages."),
    SP(),
    H("7. Governing Law"),
    P("This Agreement shall be governed by the laws of the <b>State of California</b>. "
      "Any disputes shall be resolved in the state or federal courts located in "
      "Santa Clara County, California."),
    SP(),
    P("<b>TECHCORP SUPPLIES INC</b><br/>By: ___________________________<br/>"
      "Name: Robert Chen<br/>Title: President<br/>Date: March 15, 2024"),
    SP(),
    P("<b>WIDGETS MANUFACTURING CO</b><br/>By: ___________________________<br/>"
      "Name: Maria Garcia<br/>Title: COO<br/>Date: March 15, 2024"),
])

# ---------------------------------------------------------------------------
# 3. Professional Services Agreement
# ---------------------------------------------------------------------------
build_pdf("services_consulting_client.pdf", [
    T("PROFESSIONAL SERVICES AGREEMENT"),
    P("This Professional Services Agreement (the <b>\"Agreement\"</b>) is entered into as of "
      "<b>June 1, 2024</b> (the <b>\"Effective Date\"</b>) by and between:"),
    P("<b>Consulting Group LLC</b>, a New York limited liability company (<b>\"Consultant\"</b>), "
      "and <b>Client Industries Inc</b>, a New York corporation (<b>\"Client\"</b>)."),
    SP(),
    H("1. Services"),
    P("Consultant shall provide management consulting and advisory services as mutually agreed "
      "in writing. Consultant is an independent contractor and not an employee of Client."),
    SP(),
    H("2. Compensation"),
    P("Client shall pay Consultant at the rate of <b>$150.00 per hour</b>. Consultant shall "
      "invoice Client bi-weekly. Client shall remit payment within <b>fifteen (15) days</b> "
      "of receipt of each invoice (<b>Net 15</b>)."),
    SP(),
    H("3. Term and Termination"),
    P("This Agreement commences on the Effective Date and shall continue until terminated. "
      "Either party may terminate this Agreement upon <b>thirty (30) days</b> written notice "
      "to the other party."),
    SP(),
    H("4. Confidentiality"),
    P("Each party agrees to keep confidential all proprietary information of the other party "
      "disclosed during the performance of this Agreement and to use such information solely "
      "for the purpose of performing obligations under this Agreement."),
    SP(),
    H("5. Intellectual Property"),
    P("All deliverables created by Consultant specifically for Client under this Agreement "
      "shall be owned by Client upon full payment of all fees due."),
    SP(),
    H("6. Indemnification"),
    P("Each party shall indemnify and hold harmless the other from claims arising from its own "
      "negligence or willful misconduct in connection with performance of this Agreement."),
    SP(),
    H("7. No Non-Solicitation or Non-Competition"),
    P("This Agreement contains <b>no non-solicitation or non-competition obligations</b> on "
      "either party. Both parties are free to engage with third parties, including each "
      "other's competitors, without restriction."),
    SP(),
    H("8. Governing Law"),
    P("This Agreement shall be governed by and construed in accordance with the laws of the "
      "<b>State of New York</b>."),
    SP(),
    P("<b>CONSULTING GROUP LLC</b><br/>By: ___________________________<br/>"
      "Name: Amanda Torres<br/>Title: Managing Partner<br/>Date: June 1, 2024"),
    SP(),
    P("<b>CLIENT INDUSTRIES INC</b><br/>By: ___________________________<br/>"
      "Name: David Park<br/>Title: VP Operations<br/>Date: June 1, 2024"),
])

# ---------------------------------------------------------------------------
# 4. Commercial Lease
# ---------------------------------------------------------------------------
build_pdf("lease_harbor_startup.pdf", [
    T("COMMERCIAL LEASE AGREEMENT"),
    P("This Commercial Lease Agreement (the <b>\"Lease\"</b>) is entered into as of "
      "<b>September 1, 2024</b> (the <b>\"Commencement Date\"</b>) by and between:"),
    P("<b>Harbor Properties LLC</b>, a Texas limited liability company (<b>\"Landlord\"</b>), "
      "and <b>Startup Co</b>, a Texas corporation (<b>\"Tenant\"</b>)."),
    SP(),
    H("1. Premises"),
    P("Landlord hereby leases to Tenant the commercial office space located at "
      "400 Harbor Blvd, Suite 200, Austin, Texas 78701 (the \"Premises\")."),
    SP(),
    H("2. Lease Term"),
    P("The lease term shall be <b>twelve (12) months</b>, commencing on the Commencement Date "
      "and expiring on August 31, 2025, unless sooner terminated as provided herein."),
    SP(),
    H("3. Rent"),
    P("Tenant shall pay Landlord a monthly base rent of <b>$8,500.00</b>, due on the "
      "<b>first (1st) day of each calendar month</b>. Rent shall be paid by ACH transfer "
      "to Landlord's designated bank account."),
    SP(),
    H("4. Early Termination"),
    P("Tenant may terminate this Lease prior to its expiration by providing <b>sixty (60) "
      "days</b> prior written notice to Landlord, together with an early termination fee "
      "equal to <b>two (2) months' base rent</b> ($17,000.00)."),
    SP(),
    H("5. Security Deposit"),
    P("Upon execution of this Lease, Tenant shall pay Landlord a security deposit of "
      "$17,000.00 (equal to two months' rent). The deposit shall be returned within "
      "30 days after lease expiration, less any deductions for damage beyond normal wear."),
    SP(),
    H("6. Use of Premises"),
    P("Tenant shall use the Premises solely for general office and administrative purposes "
      "and for no other purpose without Landlord's prior written consent."),
    SP(),
    H("7. Governing Law"),
    P("This Lease shall be governed by and construed in accordance with the laws of the "
      "<b>State of Texas</b>."),
    SP(),
    P("<b>HARBOR PROPERTIES LLC</b><br/>By: ___________________________<br/>"
      "Name: Patricia Williams<br/>Title: Managing Member<br/>Date: September 1, 2024"),
    SP(),
    P("<b>STARTUP CO</b><br/>By: ___________________________<br/>"
      "Name: Kevin Lee<br/>Title: CEO<br/>Date: September 1, 2024"),
])

# ---------------------------------------------------------------------------
# 5. Ambiguous Vendor Agreement
# ---------------------------------------------------------------------------
build_pdf("vendor_ambiguous_dynamic_vague.pdf", [
    T("VENDOR SERVICES AGREEMENT"),
    P("This Vendor Services Agreement (the <b>\"Agreement\"</b>) is entered into <b>as of "
      "the date of execution</b> by and between:"),
    P("<b>Dynamic Solutions Inc</b> (<b>\"Vendor\"</b>) and <b>Vague Corp Ltd</b> "
      "(<b>\"Client\"</b>)."),
    SP(),
    H("1. Services"),
    P("Vendor agrees to provide certain services to Client as may be discussed and agreed "
      "upon by the parties from time to time. The scope of services may be updated by "
      "mutual agreement."),
    SP(),
    H("2. Payment Terms"),
    P("Compensation for services rendered under this Agreement shall be as set forth in "
      "<b>Exhibit A</b>, which is incorporated herein by reference."),
    SP(),
    H("3. Term and Termination"),
    P("This Agreement shall commence upon execution and shall continue until terminated. "
      "Either party may terminate this Agreement upon <b>reasonable notice</b> to the "
      "other party. What constitutes reasonable notice shall be determined by the "
      "circumstances at the time of termination."),
    SP(),
    H("4. Restrictive Covenant"),
    P("During the term of this Agreement, Vendor shall not engage in activities that are "
      "<b>similar to the services provided hereunder</b> for any third party without "
      "Client's prior written consent. The parties agree to discuss the appropriate "
      "scope of this restriction as needed."),
    SP(),
    H("5. Confidentiality"),
    P("The parties agree to maintain the confidentiality of information shared under this "
      "Agreement and to use such information only for the purposes contemplated herein."),
    SP(),
    H("6. Governing Law"),
    P("This Agreement shall be governed by <b>the applicable jurisdiction</b> as determined "
      "by the location of the dispute or such other factors as may be relevant."),
    SP(),
    H("7. Entire Agreement"),
    P("This Agreement, together with Exhibit A and any subsequently executed Statements of "
      "Work, constitutes the entire agreement between the parties."),
    SP(),
    P("<b>DYNAMIC SOLUTIONS INC</b><br/>By: ___________________________<br/>"
      "Name: ___________________________<br/>Title: ___________________________<br/>"
      "Date: ___________________________"),
    SP(),
    P("<b>VAGUE CORP LTD</b><br/>By: ___________________________<br/>"
      "Name: ___________________________<br/>Title: ___________________________<br/>"
      "Date: ___________________________"),
])

print("All 5 demo contracts generated.")
