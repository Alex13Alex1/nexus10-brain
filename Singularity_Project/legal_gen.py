# -*- coding: utf-8 -*-
"""
LEGAL GENERATOR v1.0 - IP Transfer Agreement & Contracts
=========================================================
Generates professional legal documents for code transfer:
- Intellectual Property Transfer Agreement
- Terms of Service acknowledgment
- Project completion certificate

Generated ONLY after payment confirmed.

Author: NEXUS 10 AI Agency
"""

import os
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass

# Try reportlab first, fall back to fpdf
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    USE_REPORTLAB = True
except ImportError:
    USE_REPORTLAB = False
    try:
        from fpdf import FPDF
    except ImportError:
        print("[LEGAL_GEN] WARNING: Neither reportlab nor fpdf installed")


# === CONSTANTS ===
COMPANY_NAME = "NEXUS 10 AI Agency"
COMPANY_ADDRESS = "Advanced Medicinal Consulting Ltd\nRue du Trône 100, 3rd floor\nBrussels, 1050, Belgium"
COMPANY_EMAIL = "legal@nexus10.agency"

OUTPUT_DIR = os.path.join(os.getcwd(), "legal_documents")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@dataclass
class ContractData:
    """Data for contract generation"""
    client_name: str
    project_name: str
    project_reference: str
    amount: float
    currency: str = "USD"
    payment_date: str = ""
    payment_method: str = ""
    payment_tx_hash: str = ""
    description: str = ""


# =============================================================================
# IP TRANSFER AGREEMENT TEXT
# =============================================================================

IP_TRANSFER_TEMPLATE = """
INTELLECTUAL PROPERTY TRANSFER AGREEMENT

Agreement Date: {date}
Agreement Reference: {reference}

PARTIES:

TRANSFEROR (Developer):
{company_name}
{company_address}

TRANSFEREE (Client):
{client_name}

PROJECT DETAILS:
Project Name: {project_name}
Project Reference: {reference}
Total Amount Paid: {amount} {currency}
Payment Date: {payment_date}
Payment Method: {payment_method}

1. TRANSFER OF INTELLECTUAL PROPERTY RIGHTS

1.1 Upon receipt of full payment in the amount of {amount} {currency}, the Transferor 
hereby irrevocably transfers to the Transferee all right, title, and interest in and 
to the following intellectual property:

   (a) All source code, object code, and related documentation developed for the 
       project "{project_name}";
   (b) All algorithms, methods, processes, and techniques embodied in the deliverables;
   (c) All copyrights, patent rights (if any), trade secrets, and other intellectual 
       property rights associated with the deliverables.

1.2 This transfer is exclusive and worldwide, with no territorial limitations.

2. REPRESENTATIONS AND WARRANTIES

2.1 The Transferor represents and warrants that:
   (a) The Transferor is the sole owner of the intellectual property being transferred;
   (b) The deliverables do not infringe upon any third-party intellectual property rights;
   (c) No part of the deliverables is subject to any lien, encumbrance, or claim.

2.2 The Transferee acknowledges that:
   (a) The deliverables are provided "as-is" after the 7-day support period;
   (b) The Transferor makes no warranties regarding fitness for a particular purpose 
       beyond the agreed specifications.

3. RETAINED RIGHTS

3.1 The Transferor retains the right to:
   (a) Use general knowledge, skills, and experience gained during the project;
   (b) Use non-proprietary frameworks, libraries, and tools in future projects;
   (c) Reference the project for portfolio purposes (without disclosing proprietary details).

4. CONFIDENTIALITY

4.1 Both parties agree to maintain confidentiality regarding:
   (a) Proprietary business information;
   (b) Technical specifications unique to the project;
   (c) Financial terms of this agreement.

5. SUPPORT PERIOD

5.1 The Transferor agrees to provide technical support for a period of 7 (seven) days 
following delivery, including:
   (a) Bug fixes for issues within the original scope;
   (b) Clarification of documentation;
   (c) Assistance with initial deployment.

6. PAYMENT CONFIRMATION

6.1 Payment has been received and confirmed:
   - Amount: {amount} {currency}
   - Date: {payment_date}
   - Method: {payment_method}
   - Transaction Reference: {tx_hash}

7. GOVERNING LAW

7.1 This Agreement shall be governed by and construed in accordance with the laws 
of Belgium, without regard to its conflict of law provisions.

8. ENTIRE AGREEMENT

8.1 This Agreement constitutes the entire agreement between the parties and supersedes 
all prior negotiations, representations, or agreements relating to this subject matter.


ACKNOWLEDGED AND AGREED:

Transferor: {company_name}
Date: {date}

Transferee: {client_name}
Date: {date}

---

Document generated automatically by {company_name}
Reference: {reference}
"""


class LegalGenerator:
    """
    Generates legal documents for project delivery.
    
    Usage:
        gen = LegalGenerator()
        
        # After payment confirmed
        pdf_path = gen.generate_ip_transfer(
            client_name="John Smith",
            project_name="Telegram Bot",
            reference="NX10-20260107",
            amount=500,
            payment_date="2026-01-07",
            payment_method="Crypto (USDT)"
        )
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_ip_transfer(self,
                              client_name: str,
                              project_name: str,
                              reference: str,
                              amount: float,
                              currency: str = "USD",
                              payment_date: str = None,
                              payment_method: str = "Bank Transfer",
                              tx_hash: str = "") -> str:
        """
        Generate IP Transfer Agreement PDF.
        
        Args:
            client_name: Name of the client receiving IP
            project_name: Name of the project
            reference: Project reference number
            amount: Payment amount
            currency: Payment currency
            payment_date: Date of payment (defaults to today)
            payment_method: Payment method used
            tx_hash: Transaction hash/reference
            
        Returns:
            Path to generated PDF file
        """
        if not payment_date:
            payment_date = datetime.now().strftime("%Y-%m-%d")
        
        # Prepare data
        data = ContractData(
            client_name=client_name,
            project_name=project_name,
            project_reference=reference,
            amount=amount,
            currency=currency,
            payment_date=payment_date,
            payment_method=payment_method,
            payment_tx_hash=tx_hash or "N/A"
        )
        
        # Generate filename
        safe_project = project_name.replace(" ", "_").replace("/", "-")[:30]
        filename = f"IP_Transfer_{safe_project}_{reference}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        if USE_REPORTLAB:
            self._generate_reportlab(filepath, data)
        else:
            self._generate_fpdf(filepath, data)
        
        print(f"[LEGAL_GEN] Generated: {filepath}")
        return filepath
    
    def _generate_reportlab(self, filepath: str, data: ContractData):
        """Generate PDF using ReportLab"""
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=10
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leading=14
        )
        
        story = []
        
        # Title
        story.append(Paragraph("INTELLECTUAL PROPERTY TRANSFER AGREEMENT", title_style))
        story.append(Spacer(1, 20))
        
        # Date and Reference
        story.append(Paragraph(
            f"<b>Agreement Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>"
            f"<b>Reference:</b> {data.project_reference}",
            body_style
        ))
        story.append(Spacer(1, 20))
        
        # Parties
        story.append(Paragraph("PARTIES", heading_style))
        story.append(Paragraph(
            f"<b>TRANSFEROR (Developer):</b><br/>"
            f"{COMPANY_NAME}<br/>"
            f"{COMPANY_ADDRESS.replace(chr(10), '<br/>')}",
            body_style
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"<b>TRANSFEREE (Client):</b><br/>{data.client_name}",
            body_style
        ))
        story.append(Spacer(1, 15))
        
        # Project Details
        story.append(Paragraph("PROJECT DETAILS", heading_style))
        project_data = [
            ["Project Name:", data.project_name],
            ["Reference:", data.project_reference],
            ["Amount Paid:", f"{data.amount} {data.currency}"],
            ["Payment Date:", data.payment_date],
            ["Payment Method:", data.payment_method],
        ]
        
        t = Table(project_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
        
        # Main clauses
        story.append(Paragraph("1. TRANSFER OF INTELLECTUAL PROPERTY RIGHTS", heading_style))
        story.append(Paragraph(
            f"Upon receipt of full payment in the amount of {data.amount} {data.currency}, "
            f"the Transferor hereby irrevocably transfers to the Transferee ({data.client_name}) "
            f"all right, title, and interest in and to the intellectual property developed for "
            f"the project \"{data.project_name}\", including all source code, documentation, "
            f"copyrights, and related rights. This transfer is exclusive and worldwide.",
            body_style
        ))
        
        story.append(Paragraph("2. REPRESENTATIONS AND WARRANTIES", heading_style))
        story.append(Paragraph(
            "The Transferor represents that they are the sole owner of the intellectual property, "
            "the deliverables do not infringe upon third-party rights, and no part is subject to "
            "any lien or claim. The deliverables are provided 'as-is' after the 7-day support period.",
            body_style
        ))
        
        story.append(Paragraph("3. SUPPORT PERIOD", heading_style))
        story.append(Paragraph(
            "Technical support is provided for 7 days following delivery, including bug fixes "
            "within original scope, documentation clarification, and deployment assistance.",
            body_style
        ))
        
        story.append(Paragraph("4. PAYMENT CONFIRMATION", heading_style))
        story.append(Paragraph(
            f"Payment confirmed: {data.amount} {data.currency} received on {data.payment_date} "
            f"via {data.payment_method}. Transaction reference: {data.payment_tx_hash}",
            body_style
        ))
        
        story.append(Spacer(1, 30))
        
        # Signatures
        story.append(Paragraph("ACKNOWLEDGED AND AGREED:", heading_style))
        story.append(Paragraph(
            f"<b>Transferor:</b> {COMPANY_NAME}<br/>"
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            body_style
        ))
        story.append(Spacer(1, 15))
        story.append(Paragraph(
            f"<b>Transferee:</b> {data.client_name}<br/>"
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            body_style
        ))
        
        story.append(Spacer(1, 40))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(
            f"Document generated automatically by {COMPANY_NAME}<br/>"
            f"Reference: {data.project_reference}",
            footer_style
        ))
        
        doc.build(story)
    
    def _generate_fpdf(self, filepath: str, data: ContractData):
        """Generate PDF using FPDF (fallback)"""
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, "INTELLECTUAL PROPERTY TRANSFER AGREEMENT", ln=True, align='C')
        pdf.ln(10)
        
        # Date and Reference
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Agreement Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
        pdf.cell(0, 8, f"Reference: {data.project_reference}", ln=True)
        pdf.ln(10)
        
        # Parties
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "PARTIES", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, f"TRANSFEROR: {COMPANY_NAME}\n{COMPANY_ADDRESS}")
        pdf.ln(5)
        pdf.cell(0, 8, f"TRANSFEREE: {data.client_name}", ln=True)
        pdf.ln(10)
        
        # Project Details
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "PROJECT DETAILS", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"Project Name: {data.project_name}", ln=True)
        pdf.cell(0, 6, f"Amount Paid: {data.amount} {data.currency}", ln=True)
        pdf.cell(0, 6, f"Payment Date: {data.payment_date}", ln=True)
        pdf.cell(0, 6, f"Payment Method: {data.payment_method}", ln=True)
        pdf.ln(10)
        
        # Transfer clause
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "1. TRANSFER OF INTELLECTUAL PROPERTY RIGHTS", ln=True)
        pdf.set_font("Arial", '', 10)
        transfer_text = (
            f"Upon receipt of full payment ({data.amount} {data.currency}), "
            f"the Transferor irrevocably transfers to {data.client_name} all rights, "
            f"title, and interest in the intellectual property for project '{data.project_name}', "
            f"including all source code, documentation, and copyrights. "
            f"This transfer is exclusive and worldwide."
        )
        pdf.multi_cell(0, 6, transfer_text)
        pdf.ln(5)
        
        # Support
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. SUPPORT PERIOD", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, "Technical support provided for 7 days following delivery.")
        pdf.ln(5)
        
        # Payment confirmation
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. PAYMENT CONFIRMATION", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"Payment of {data.amount} {data.currency} confirmed.", ln=True)
        pdf.cell(0, 6, f"Transaction: {data.payment_tx_hash}", ln=True)
        pdf.ln(15)
        
        # Signatures
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "ACKNOWLEDGED AND AGREED:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Transferor: {COMPANY_NAME}", ln=True)
        pdf.cell(0, 8, f"Transferee: {data.client_name}", ln=True)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
        
        # Footer
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 6, f"Generated by {COMPANY_NAME} | Ref: {data.project_reference}", align='C')
        
        pdf.output(filepath)
    
    def generate_completion_certificate(self,
                                         client_name: str,
                                         project_name: str,
                                         reference: str,
                                         completion_date: str = None) -> str:
        """Generate project completion certificate"""
        if not completion_date:
            completion_date = datetime.now().strftime("%Y-%m-%d")
        
        safe_project = project_name.replace(" ", "_")[:30]
        filename = f"Completion_Certificate_{safe_project}_{reference}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Simple completion certificate using FPDF
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        # Border
        pdf.set_draw_color(0, 100, 150)
        pdf.set_line_width(2)
        pdf.rect(10, 10, 190, 277)
        
        # Title
        pdf.set_font("Arial", 'B', 24)
        pdf.ln(30)
        pdf.cell(0, 20, "CERTIFICATE OF COMPLETION", ln=True, align='C')
        
        pdf.set_font("Arial", '', 14)
        pdf.ln(20)
        pdf.cell(0, 10, "This is to certify that", ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 18)
        pdf.ln(5)
        pdf.cell(0, 15, project_name, ln=True, align='C')
        
        pdf.set_font("Arial", '', 14)
        pdf.ln(5)
        pdf.cell(0, 10, "has been successfully completed for", ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 16)
        pdf.ln(5)
        pdf.cell(0, 15, client_name, ln=True, align='C')
        
        pdf.set_font("Arial", '', 12)
        pdf.ln(20)
        pdf.cell(0, 8, f"Completion Date: {completion_date}", ln=True, align='C')
        pdf.cell(0, 8, f"Reference: {reference}", ln=True, align='C')
        
        pdf.ln(30)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 8, COMPANY_NAME, ln=True, align='C')
        
        pdf.output(filepath)
        print(f"[LEGAL_GEN] Certificate generated: {filepath}")
        return filepath


# =============================================================================
# SINGLETON
# =============================================================================

_legal_gen_instance: Optional[LegalGenerator] = None

def get_legal_generator() -> LegalGenerator:
    """Get or create LegalGenerator singleton"""
    global _legal_gen_instance
    if _legal_gen_instance is None:
        _legal_gen_instance = LegalGenerator()
    return _legal_gen_instance


# =============================================================================
# QUICK FUNCTIONS
# =============================================================================

def generate_ip_transfer(client_name: str, project_name: str, reference: str,
                         amount: float, payment_date: str = None,
                         payment_method: str = "Bank Transfer",
                         tx_hash: str = "") -> str:
    """Quick IP transfer document generation"""
    gen = get_legal_generator()
    return gen.generate_ip_transfer(
        client_name=client_name,
        project_name=project_name,
        reference=reference,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        tx_hash=tx_hash
    )


def generate_completion_certificate(client_name: str, project_name: str,
                                     reference: str) -> str:
    """Quick completion certificate generation"""
    gen = get_legal_generator()
    return gen.generate_completion_certificate(
        client_name=client_name,
        project_name=project_name,
        reference=reference
    )


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  LEGAL GENERATOR v1.0 - Test")
    print("=" * 60)
    
    gen = LegalGenerator()
    
    # Test IP Transfer
    print("\n[Generating IP Transfer Agreement...]")
    ip_path = gen.generate_ip_transfer(
        client_name="John Smith",
        project_name="E-Commerce Telegram Bot",
        reference="NX10-20260107123456",
        amount=500,
        payment_date="2026-01-07",
        payment_method="Crypto (USDT on Polygon)",
        tx_hash="0x123abc456def789..."
    )
    print(f"Generated: {ip_path}")
    
    # Test Completion Certificate
    print("\n[Generating Completion Certificate...]")
    cert_path = gen.generate_completion_certificate(
        client_name="John Smith",
        project_name="E-Commerce Telegram Bot",
        reference="NX10-20260107123456"
    )
    print(f"Generated: {cert_path}")
    
    print("\n" + "=" * 60)







