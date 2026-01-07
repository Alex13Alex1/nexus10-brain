# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - PDF Invoice Generator
==========================================
Автоматическая генерация профессиональных PDF счетов.

Author: Nexus 10 AI Agency
"""

import os
from datetime import datetime, date
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Config
MY_WALLET = os.getenv("MY_CRYPTO_WALLET", "0xf244499abff0e7c6939f470de0914fc1c848f308")
INVOICES_DIR = os.path.join(os.getcwd(), "invoices")
os.makedirs(INVOICES_DIR, exist_ok=True)

# Bank details - Advanced Medicinal Consulting Ltd (Wise Belgium)
BANK_DETAILS = {
    "bank_name": "Wise",
    "iban": "BE29 9055 1684 1164",
    "swift": "TRWIBEB1XXX",
    "account_holder": "Advanced Medicinal Consulting Ltd",
    "address": "Rue du Trone 100, 3rd floor, Brussels, 1050, Belgium",
    "currency": "EUR/USD"
}


class InvoiceGenerator:
    """
    Генератор профессиональных PDF инвойсов для Nexus 10 AI Agency.
    """
    
    def __init__(self, wallet: str = None, bank_details: Dict = None):
        self.wallet = wallet or MY_WALLET
        self.bank = bank_details or BANK_DETAILS
    
    def create_pdf(self, 
                   project_name: str,
                   amount: float,
                   currency: str = "USD",
                   client_name: str = "Valued Client",
                   reference: str = None,
                   description: str = "") -> str:
        """
        Создает PDF инвойс.
        
        Args:
            project_name: Название проекта
            amount: Сумма к оплате
            currency: Валюта (USD, EUR)
            client_name: Имя клиента
            reference: Уникальный референс
            description: Описание работ
        
        Returns:
            Путь к созданному PDF файлу
        """
        try:
            from fpdf import FPDF
        except ImportError:
            print("[INVOICE] fpdf2 not installed. Run: pip install fpdf2")
            return self._create_text_invoice(project_name, amount, currency, client_name, reference)
        
        if not reference:
            reference = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        pdf = FPDF()
        pdf.add_page()
        
        # === HEADER ===
        pdf.set_fill_color(30, 41, 59)  # Slate-800
        pdf.rect(0, 0, 210, 45, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 24)
        pdf.set_xy(10, 12)
        pdf.cell(0, 10, "NEXUS 10 AI AGENCY", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.set_xy(10, 25)
        pdf.cell(0, 5, "Autonomous AI Development Services", ln=True)
        pdf.set_xy(10, 32)
        pdf.cell(0, 5, "Professional Software Solutions", ln=True)
        
        # Invoice label
        pdf.set_xy(140, 15)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(60, 10, "INVOICE", align='R')
        
        # === INVOICE DETAILS ===
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 10)
        
        # Left column - Client
        pdf.set_xy(10, 55)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 6, "BILL TO:", ln=True)
        pdf.set_font("Helvetica", '', 10)
        pdf.set_x(10)
        pdf.cell(0, 6, client_name, ln=True)
        
        # Right column - Invoice info
        pdf.set_xy(120, 55)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(40, 6, "Invoice Number:")
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(40, 6, reference, ln=True)
        
        pdf.set_xy(120, 61)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(40, 6, "Date:")
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(40, 6, date.today().strftime("%B %d, %Y"), ln=True)
        
        pdf.set_xy(120, 67)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(40, 6, "Due Date:")
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(40, 6, "Upon Receipt", ln=True)
        
        # === LINE ITEMS TABLE ===
        pdf.ln(20)
        
        # Table header
        pdf.set_fill_color(59, 130, 246)  # Blue-500
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(120, 10, "  Description", border=1, fill=True)
        pdf.cell(35, 10, "Amount", border=1, align='C', fill=True)
        pdf.cell(35, 10, "Total", border=1, align='C', fill=True, ln=True)
        
        # Table row
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 10)
        
        desc_text = project_name
        if description:
            desc_text += f"\n{description[:80]}"
        
        pdf.cell(120, 12, f"  {project_name}", border=1)
        pdf.cell(35, 12, f"{amount:.2f} {currency}", border=1, align='C')
        pdf.cell(35, 12, f"{amount:.2f} {currency}", border=1, align='C', ln=True)
        
        # Subtotal / Total
        pdf.ln(5)
        pdf.set_x(120)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(35, 8, "Subtotal:", align='R')
        pdf.cell(35, 8, f"{amount:.2f} {currency}", align='C', ln=True)
        
        pdf.set_x(120)
        pdf.set_fill_color(34, 197, 94)  # Green-500
        pdf.set_text_color(255, 255, 255)
        pdf.cell(35, 10, "TOTAL DUE:", align='R', fill=True)
        pdf.cell(35, 10, f"{amount:.2f} {currency}", align='C', fill=True, ln=True)
        
        # === PAYMENT DETAILS ===
        pdf.set_text_color(0, 0, 0)
        pdf.ln(15)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "Payment Methods:", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.ln(3)
        
        # Crypto
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 6, "Option 1: Cryptocurrency (Polygon Network)", ln=True)
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, f"   Token: USDT or USDC", ln=True)
        pdf.cell(0, 5, f"   Network: Polygon (MATIC)", ln=True)
        pdf.cell(0, 5, f"   Wallet: {self.wallet}", ln=True)
        
        pdf.ln(5)
        
        # Bank Transfer
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 6, "Option 2: Bank Transfer (SEPA/SWIFT)", ln=True)
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, f"   Bank: {self.bank['bank_name']}", ln=True)
        pdf.cell(0, 5, f"   IBAN: {self.bank['iban']}", ln=True)
        pdf.cell(0, 5, f"   SWIFT/BIC: {self.bank['swift']}", ln=True)
        pdf.cell(0, 5, f"   Account Holder: {self.bank['account_holder']}", ln=True)
        pdf.cell(0, 5, f"   Reference: {reference}", ln=True)
        
        # === FOOTER ===
        pdf.set_y(-40)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "Thank you for your business!", ln=True, align='C')
        pdf.cell(0, 5, "Payment is due upon receipt. Please include the reference number with your payment.", ln=True, align='C')
        pdf.cell(0, 5, "Powered by Nexus 10 AI Agency - Autonomous Development System", ln=True, align='C')
        
        # Save
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"invoice_{safe_name}_{reference}.pdf")
        pdf.output(file_path)
        
        print(f"[INVOICE] PDF created: {file_path}")
        return file_path
    
    def _create_text_invoice(self, project_name: str, amount: float, 
                             currency: str, client_name: str, reference: str) -> str:
        """Fallback: создает текстовый инвойс если fpdf недоступен"""
        if not reference:
            reference = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        content = f"""
================================================================================
                         NEXUS 10 AI AGENCY - INVOICE
================================================================================

Invoice Number: {reference}
Date: {date.today().strftime("%B %d, %Y")}
Due Date: Upon Receipt

--------------------------------------------------------------------------------
BILL TO: {client_name}
--------------------------------------------------------------------------------

DESCRIPTION                                              AMOUNT
--------------------------------------------------------------------------------
{project_name:<55} {amount:>10.2f} {currency}
--------------------------------------------------------------------------------
                                            TOTAL:    {amount:>10.2f} {currency}

================================================================================
                              PAYMENT METHODS
================================================================================

OPTION 1: Cryptocurrency (Polygon Network)
  Token: USDT or USDC
  Network: Polygon (MATIC)
  Wallet: {self.wallet}

OPTION 2: Bank Transfer (SEPA/SWIFT)
  Bank: {self.bank['bank_name']}
  IBAN: {self.bank['iban']}
  SWIFT: {self.bank['swift']}
  Reference: {reference}

================================================================================
Thank you for your business!
Powered by Nexus 10 AI Agency
================================================================================
"""
        
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"invoice_{safe_name}_{reference}.txt")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[INVOICE] Text invoice created: {file_path}")
        return file_path


# === QUICK FUNCTIONS ===

def generate_invoice(project_name: str, amount: float, 
                     client_name: str = "Client",
                     currency: str = "USD",
                     reference: str = None) -> str:
    """Quick invoice generation"""
    gen = InvoiceGenerator()
    return gen.create_pdf(project_name, amount, currency, client_name, reference)


def generate_invoice_from_order(order: Dict) -> str:
    """Generate invoice from order dict"""
    gen = InvoiceGenerator()
    return gen.create_pdf(
        project_name=order.get('title', 'Project'),
        amount=order.get('estimated_price', 100),
        currency=order.get('currency', 'USD'),
        client_name=order.get('client_name', 'Valued Client'),
        reference=order.get('reference', None),
        description=order.get('description', '')
    )


# === COPYRIGHT TRANSFER AGREEMENT ===

class CopyrightGenerator:
    """
    Генератор документов о передаче авторских прав.
    """
    
    def __init__(self):
        self.company = "NEXUS 10 AI AGENCY"
    
    def create_copyright_pdf(self, 
                             client_name: str,
                             project_name: str,
                             amount: float,
                             currency: str = "USD",
                             reference: str = None) -> str:
        """
        Создает PDF документ о передаче авторских прав.
        """
        try:
            from fpdf import FPDF
        except ImportError:
            print("[COPYRIGHT] fpdf2 not installed")
            return self._create_text_copyright(client_name, project_name, reference)
        
        if not reference:
            reference = f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        pdf = FPDF()
        pdf.add_page()
        
        # === HEADER ===
        pdf.set_fill_color(30, 41, 59)
        pdf.rect(0, 0, 210, 40, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 18)
        pdf.set_xy(10, 12)
        pdf.cell(0, 10, "COPYRIGHT TRANSFER AGREEMENT", ln=True, align='C')
        
        pdf.set_font("Helvetica", '', 10)
        pdf.set_xy(10, 25)
        pdf.cell(0, 5, f"Reference: {reference}", ln=True, align='C')
        
        # === BODY ===
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(50)
        
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "PARTIES:", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.ln(3)
        pdf.multi_cell(0, 6, f"""
1. DEVELOPER: {self.company}
   (hereinafter "Developer")

2. CLIENT: {client_name}
   (hereinafter "Client")
        """)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "PROJECT:", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 6, f"   {project_name}", ln=True)
        pdf.cell(0, 6, f"   Total Value: {amount:.2f} {currency}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "TERMS OF TRANSFER:", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.ln(3)
        
        terms = """
1. OWNERSHIP TRANSFER
   Upon receipt of full payment, all intellectual property rights, including but 
   not limited to copyright, source code, designs, documentation, and any 
   derivative works created under this agreement, shall be transferred to the Client.

2. SCOPE OF RIGHTS
   The Client receives exclusive, worldwide, perpetual rights to:
   - Use, modify, and distribute the deliverables
   - Create derivative works
   - Sublicense to third parties
   - Commercialize without royalty obligations to Developer

3. DEVELOPER RIGHTS
   The Developer retains:
   - Right to use generic, non-proprietary techniques and knowledge
   - Right to reference the project in portfolio (without disclosing confidential details)
   - No rights to the specific deliverables after transfer

4. WARRANTIES
   Developer warrants that:
   - All work is original or properly licensed
   - No third-party rights are infringed
   - Deliverables are free from known defects at time of delivery

5. EFFECTIVE DATE
   This transfer becomes effective upon confirmation of full payment.
        """
        
        pdf.multi_cell(0, 5, terms)
        
        # === SIGNATURES ===
        pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "SIGNATURES:", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.ln(5)
        
        pdf.cell(95, 6, f"Date: {date.today().strftime('%B %d, %Y')}", border=0)
        pdf.cell(95, 6, f"Date: {date.today().strftime('%B %d, %Y')}", border=0, ln=True)
        
        pdf.ln(10)
        pdf.cell(95, 6, "_" * 30, border=0)
        pdf.cell(95, 6, "_" * 30, border=0, ln=True)
        
        pdf.cell(95, 6, f"{self.company}", border=0)
        pdf.cell(95, 6, f"{client_name}", border=0, ln=True)
        
        pdf.cell(95, 6, "(Developer)", border=0)
        pdf.cell(95, 6, "(Client)", border=0, ln=True)
        
        # === FOOTER ===
        pdf.set_y(-30)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "This document is legally binding upon signature by both parties.", ln=True, align='C')
        pdf.cell(0, 5, f"Generated by {self.company} - Autonomous Development System", ln=True, align='C')
        
        # Save
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"copyright_{safe_name}_{reference}.pdf")
        pdf.output(file_path)
        
        print(f"[COPYRIGHT] PDF created: {file_path}")
        return file_path
    
    def _create_text_copyright(self, client_name: str, project_name: str, reference: str) -> str:
        """Fallback text version"""
        if not reference:
            reference = f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        content = f"""
================================================================================
              COPYRIGHT TRANSFER AGREEMENT
              Reference: {reference}
================================================================================

PARTIES:
1. DEVELOPER: NEXUS 10 AI AGENCY
2. CLIENT: {client_name}

PROJECT: {project_name}
DATE: {date.today().strftime("%B %d, %Y")}

================================================================================
TERMS:

Upon receipt of full payment, all intellectual property rights to the 
developed code, designs, and assets are transferred to the Client.

The Client receives exclusive, worldwide, perpetual rights to use, modify,
distribute, and commercialize the deliverables.

================================================================================
SIGNATURES:

_____________________________          _____________________________
NEXUS 10 AI AGENCY                     {client_name}
(Developer)                            (Client)

================================================================================
"""
        
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"copyright_{safe_name}_{reference}.txt")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path


# === COMBINED PACKAGE GENERATOR ===

def generate_pdf_package(client_name: str, amount: float, project_name: str = "Project",
                         currency: str = "USD") -> Dict[str, str]:
    """
    Generate complete document package: Invoice + Copyright Agreement.
    
    Returns:
        Dict with paths: {"invoice": path, "copyright": path}
    """
    invoice_gen = InvoiceGenerator()
    copyright_gen = CopyrightGenerator()
    
    reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    invoice_path = invoice_gen.create_pdf(
        project_name=project_name,
        amount=amount,
        currency=currency,
        client_name=client_name,
        reference=reference
    )
    
    copyright_path = copyright_gen.create_copyright_pdf(
        client_name=client_name,
        project_name=project_name,
        amount=amount,
        currency=currency,
        reference=reference
    )
    
    return {
        "invoice": invoice_path,
        "copyright": copyright_path,
        "reference": reference
    }


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 AI AGENCY - Document Generator Test")
    print("=" * 60)
    
    # Test Invoice
    print("\n[1] Testing Invoice Generator...")
    inv_gen = InvoiceGenerator()
    invoice_path = inv_gen.create_pdf(
        project_name="AI Telegram Bot Development",
        amount=250.00,
        currency="USD",
        client_name="John Smith",
        description="Custom bot with GPT-4 integration"
    )
    print(f"    Invoice: {invoice_path}")
    
    # Test Copyright
    print("\n[2] Testing Copyright Generator...")
    cr_gen = CopyrightGenerator()
    copyright_path = cr_gen.create_copyright_pdf(
        client_name="John Smith",
        project_name="AI Telegram Bot Development",
        amount=250.00,
        currency="USD"
    )
    print(f"    Copyright: {copyright_path}")
    
    # Test Combined Package
    print("\n[3] Testing Combined Package...")
    package = generate_pdf_package(
        client_name="Jane Doe",
        amount=500.00,
        project_name="E-Commerce Platform",
        currency="USD"
    )
    print(f"    Invoice: {package['invoice']}")
    print(f"    Copyright: {package['copyright']}")
    print(f"    Reference: {package['reference']}")
    
    print("\n" + "=" * 60)
    print("[OK] All documents generated successfully!")
    print("=" * 60)


