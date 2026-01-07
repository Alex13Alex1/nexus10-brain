# -*- coding: utf-8 -*-
"""
NEXUS CORE - Invoice Generator
===============================
Professional PDF invoice generation.

Ported from: Singularity_Project/invoice_gen.py
Author: NEXUS 10 AI Agency
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

# Bank details
BANK_DETAILS = {
    "bank_name": os.getenv("BANK_NAME", "Wise"),
    "iban": os.getenv("BANK_IBAN", "BE29 9055 1684 1164"),
    "swift": os.getenv("BANK_SWIFT", "TRWIBEB1XXX"),
    "account_holder": os.getenv("BANK_HOLDER", "Advanced Medicinal Consulting Ltd"),
    "address": os.getenv("BANK_ADDRESS", "Rue du Trone 100, 3rd floor, Brussels, 1050, Belgium"),
    "currency": "EUR/USD"
}


class InvoiceGenerator:
    """Professional PDF invoice generator."""
    
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
        Create PDF invoice.
        
        Returns:
            Path to created PDF file
        """
        try:
            from fpdf import FPDF
        except ImportError:
            print("[INVOICE] fpdf2 not installed. Creating text invoice.")
            return self._create_text_invoice(project_name, amount, currency, client_name, reference)
        
        if not reference:
            reference = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        pdf = FPDF()
        pdf.add_page()
        
        # === HEADER ===
        pdf.set_fill_color(30, 41, 59)
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
        
        pdf.set_xy(140, 15)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(60, 10, "INVOICE", align='R')
        
        # === INVOICE DETAILS ===
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 10)
        
        pdf.set_xy(10, 55)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 6, "BILL TO:", ln=True)
        pdf.set_font("Helvetica", '', 10)
        pdf.set_x(10)
        pdf.cell(0, 6, client_name, ln=True)
        
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
        
        # === TABLE ===
        pdf.ln(20)
        
        pdf.set_fill_color(59, 130, 246)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(120, 10, "  Description", border=1, fill=True)
        pdf.cell(35, 10, "Amount", border=1, align='C', fill=True)
        pdf.cell(35, 10, "Total", border=1, align='C', fill=True, ln=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 10)
        
        pdf.cell(120, 12, f"  {project_name}", border=1)
        pdf.cell(35, 12, f"{amount:.2f} {currency}", border=1, align='C')
        pdf.cell(35, 12, f"{amount:.2f} {currency}", border=1, align='C', ln=True)
        
        pdf.ln(5)
        pdf.set_x(120)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(35, 8, "Subtotal:", align='R')
        pdf.cell(35, 8, f"{amount:.2f} {currency}", align='C', ln=True)
        
        pdf.set_x(120)
        pdf.set_fill_color(34, 197, 94)
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
        
        # Bank
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
        pdf.cell(0, 5, "Payment is due upon receipt. Please include the reference number.", ln=True, align='C')
        pdf.cell(0, 5, "Powered by NEXUS 10 AI Agency", ln=True, align='C')
        
        # Save
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"invoice_{safe_name}_{reference}.pdf")
        pdf.output(file_path)
        
        print(f"[INVOICE] PDF created: {file_path}")
        return file_path
    
    def _create_text_invoice(self, project_name: str, amount: float, 
                             currency: str, client_name: str, reference: str) -> str:
        """Fallback: text invoice if fpdf unavailable"""
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
Powered by NEXUS 10 AI Agency
================================================================================
"""
        
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        file_path = os.path.join(INVOICES_DIR, f"invoice_{safe_name}_{reference}.txt")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
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



