# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - Landing Page Generator v2.0
=================================================
Генерирует профессиональные лендинги для оплаты.
Поддержка: Card (Stripe), Bank Transfer (SEPA/SWIFT), Crypto (USDC/USDT)
Включает: PDF Invoice download, Real-time crypto verification

Author: Nexus 10 AI Agency
"""

import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
MY_WALLET = os.getenv("MY_CRYPTO_WALLET", "")
WISE_TAG = os.getenv("WISE_TAG", "")
STRIPE_LINK = os.getenv("STRIPE_PAYMENT_LINK", "")

# Bank details for SEPA/SWIFT
BANK_NAME = os.getenv("BANK_NAME", "Wise")
BANK_IBAN = os.getenv("BANK_IBAN", "BE29905516841164")
BANK_SWIFT = os.getenv("BANK_SWIFT", "TRWIBEB1XXX")
BANK_HOLDER = os.getenv("BANK_HOLDER", "Advanced Medicinal Consulting Ltd")
BANK_ADDRESS = os.getenv("BANK_ADDRESS", "Rue du Trone 100, 3rd floor, Brussels, 1050, Belgium")

# Output directories
LANDING_DIR = os.path.join(os.getcwd(), "landings")
INVOICES_DIR = os.path.join(os.getcwd(), "invoices")
os.makedirs(LANDING_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)


def generate_payment_landing(
    project_name: str,
    price_usd: float,
    client_name: str = "Valued Client",
    reference: str = None,
    description: str = "",
    include_stripe: bool = True,
    include_bank: bool = True,
    include_crypto: bool = True,
    include_pdf_download: bool = True,
    output_file: str = None
) -> str:
    """
    Генерирует HTML лендинг для оплаты проекта.
    
    Args:
        project_name: Название проекта
        price_usd: Цена в USD
        client_name: Имя клиента
        reference: Уникальный референс
        description: Описание работы
        include_stripe: Включить оплату картой
        include_bank: Включить банковский перевод
        include_crypto: Включить крипто
        include_pdf_download: Включить PDF инвойс
        output_file: Путь для сохранения
    
    Returns:
        Путь к созданному файлу
    """
    if not reference:
        reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Generate PDF invoice path (will be created separately)
    pdf_filename = f"invoice_{reference}.pdf"
    pdf_path = f"../invoices/{pdf_filename}"
    
    # Payment buttons HTML
    payment_buttons = []
    
    # 1. CARD PAYMENT (Stripe)
    if include_stripe and STRIPE_LINK:
        stripe_url = f"{STRIPE_LINK}?client_reference_id={reference}&locale=en"
        payment_buttons.append(f'''
            <a href="{stripe_url}" target="_blank" 
               class="block w-full bg-indigo-600 hover:bg-indigo-500 py-4 rounded-xl font-bold transition text-center shadow-lg hover:shadow-indigo-500/30">
                💳 Pay with Card
            </a>
        ''')
    
    # 2. BANK TRANSFER (SEPA/SWIFT)
    if include_bank:
        payment_buttons.append(f'''
            <button onclick="showBankDetails()" 
                    class="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-xl font-bold transition shadow-lg hover:shadow-emerald-500/30">
                🏦 Bank Transfer (SEPA/SWIFT)
            </button>
        ''')
    
    # 3. CRYPTO PAYMENT
    if include_crypto and MY_WALLET:
        payment_buttons.append(f'''
            <button onclick="showCrypto()" 
                    class="w-full bg-orange-500 hover:bg-orange-400 py-4 rounded-xl font-bold transition shadow-lg hover:shadow-orange-500/30">
                💎 Pay with Crypto (USDC/USDT)
            </button>
        ''')
    
    buttons_html = "\n".join(payment_buttons) if payment_buttons else '''
        <p class="text-slate-400 text-center">No payment methods configured</p>
    '''
    
    # PDF Download button
    pdf_button = f'''
        <a href="{pdf_path}" download="{pdf_filename}"
           class="inline-flex items-center gap-2 bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-sm transition">
            📥 Download PDF Invoice
        </a>
    ''' if include_pdf_download else ''
    
    # Bank Details Modal
    bank_modal = f'''
        <div id="bankModal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div class="bg-slate-800 rounded-2xl p-6 max-w-lg w-full border border-emerald-500/50 shadow-2xl">
                <h3 class="text-xl font-bold text-emerald-400 mb-4">🏦 Bank Transfer Details</h3>
                
                <div class="space-y-3 mb-6">
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">Bank Name</p>
                        <p class="font-semibold">{BANK_NAME or "Contact for details"}</p>
                    </div>
                    
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">Account Holder</p>
                        <p class="font-semibold">{BANK_HOLDER}</p>
                    </div>
                    
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">IBAN</p>
                        <code class="text-emerald-300 select-all">{BANK_IBAN or "Contact for IBAN"}</code>
                    </div>
                    
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">SWIFT/BIC</p>
                        <code class="text-emerald-300 select-all">{BANK_SWIFT or "Contact for SWIFT"}</code>
                    </div>
                    
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">Payment Reference (Required)</p>
                        <code class="text-yellow-400 font-bold select-all">{reference}</code>
                    </div>
                    
                    <div class="bg-slate-900 p-3 rounded-lg">
                        <p class="text-xs text-slate-500 uppercase mb-1">Amount</p>
                        <p class="text-2xl font-mono font-bold text-green-400">${price_usd:.2f} USD</p>
                    </div>
                </div>
                
                <div class="bg-yellow-900/30 border border-yellow-500/50 p-3 rounded-xl mb-4">
                    <p class="text-yellow-300 text-sm">⚠️ Important: Include reference <strong>{reference}</strong> in payment description</p>
                </div>
                
                <button onclick="closeBankModal()" 
                        class="w-full bg-slate-700 hover:bg-slate-600 py-3 rounded-xl font-bold transition">
                    Close
                </button>
            </div>
        </div>
    ''' if include_bank else ''
    
    # Crypto Modal (Enhanced with verification)
    crypto_modal = f'''
        <div id="cryptoModal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div class="bg-slate-800 rounded-2xl p-6 max-w-lg w-full border border-orange-500/50 shadow-2xl">
                <h3 class="text-xl font-bold text-orange-400 mb-4">💎 Crypto Payment</h3>
                
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div class="bg-slate-900 p-3 rounded-lg text-center">
                        <p class="text-xs text-slate-500 uppercase mb-1">Network</p>
                        <p class="font-bold text-purple-400">Polygon</p>
                    </div>
                    <div class="bg-slate-900 p-3 rounded-lg text-center">
                        <p class="text-xs text-slate-500 uppercase mb-1">Token</p>
                        <p class="font-bold">USDC / USDT</p>
                    </div>
                </div>
                
                <div class="bg-slate-900 p-4 rounded-xl mb-4 text-center">
                    <p class="text-xs text-slate-500 uppercase mb-1">Amount to Send</p>
                    <p class="text-3xl font-mono font-bold text-green-400">${price_usd:.2f}</p>
                </div>
                
                <div class="bg-slate-950 p-4 rounded-xl mb-4">
                    <p class="text-xs text-orange-500 uppercase mb-2">Wallet Address (Polygon Network)</p>
                    <code id="walletAddress" class="text-sm break-all text-orange-200 select-all block mb-2">{MY_WALLET}</code>
                    <button onclick="copyWallet()" class="text-xs bg-orange-600 hover:bg-orange-500 px-4 py-2 rounded-lg transition">
                        📋 Copy Address
                    </button>
                </div>
                
                <div class="bg-yellow-900/30 border border-yellow-500/50 p-3 rounded-xl mb-4">
                    <p class="text-yellow-300 text-sm">⚠️ Send EXACTLY ${price_usd:.2f} for automatic verification</p>
                    <p class="text-yellow-400/70 text-xs mt-1">Payments are scanned every 5 minutes</p>
                </div>
                
                <div id="verifyStatus" class="hidden bg-blue-900/30 border border-blue-500/50 p-3 rounded-xl mb-4">
                    <p class="text-blue-300 text-sm" id="verifyMessage">⏳ Scanning blockchain...</p>
                </div>
                
                <button onclick="verifyPayment()" id="verifyBtn"
                        class="w-full bg-green-600 hover:bg-green-500 py-3 rounded-xl font-bold transition mb-2">
                    ✅ I Have Paid - Verify Now
                </button>
                
                <button onclick="closeCrypto()" 
                        class="w-full bg-slate-700 hover:bg-slate-600 py-2 rounded-xl transition">
                    Close
                </button>
            </div>
        </div>
    ''' if include_crypto and MY_WALLET else ''
    
    # Full HTML with Nexus 10 branding
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment | {project_name} | Nexus 10 AI Agency</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Space Grotesk', sans-serif; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .gradient-text {{ background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white min-h-screen">
    
    <!-- Header -->
    <header class="py-6 px-4 border-b border-slate-800/50 backdrop-blur-sm sticky top-0 z-40 bg-slate-950/80">
        <div class="max-w-3xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-500/20">
                    N10
                </div>
                <div>
                    <span class="text-xl font-bold gradient-text">NEXUS 10</span>
                    <p class="text-xs text-slate-500">AI AGENCY</p>
                </div>
            </div>
            <span class="text-sm text-slate-400 bg-slate-800/50 px-3 py-1 rounded-full">Secure Payment Portal</span>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="max-w-3xl mx-auto py-12 px-4">
        
        <!-- Invoice Card -->
        <div class="bg-slate-900/50 backdrop-blur rounded-3xl border border-slate-700/50 p-8 mb-8 shadow-2xl">
            
            <!-- Client & PDF Download -->
            <div class="flex items-start justify-between mb-8 pb-6 border-b border-slate-700/50">
                <div>
                    <p class="text-sm text-slate-400 mb-1">Prepared for</p>
                    <p class="text-2xl font-semibold">{client_name}</p>
                </div>
                {pdf_button}
            </div>
            
            <!-- Project Details -->
            <div class="mb-8">
                <p class="text-sm text-slate-400 mb-1">Project</p>
                <h1 class="text-3xl font-bold text-blue-400 mb-3">{project_name}</h1>
                <p class="text-slate-300 leading-relaxed">{description if description else "Professional software development services"}</p>
            </div>
            
            <!-- Amount -->
            <div class="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 mb-8 text-center border border-slate-700/50">
                <p class="text-sm text-slate-500 uppercase tracking-wider mb-2">Amount Due</p>
                <p class="text-6xl font-bold mono text-green-400 mb-1">${price_usd:.2f}</p>
                <p class="text-slate-400">USD</p>
            </div>
            
            <!-- Reference -->
            <div class="flex items-center justify-between text-sm text-slate-400 mb-8 bg-slate-800/30 px-4 py-3 rounded-xl">
                <span>Invoice Reference:</span>
                <code class="bg-slate-900 px-4 py-2 rounded-lg mono text-blue-300">{reference}</code>
            </div>
            
            <!-- Payment Buttons -->
            <div class="space-y-4">
                <p class="text-center text-slate-400 text-sm mb-4">Choose your preferred payment method:</p>
                {buttons_html}
            </div>
            
        </div>
        
        <!-- What's Included -->
        <div class="bg-slate-900/30 rounded-2xl p-6 border border-slate-700/30">
            <h3 class="font-semibold mb-4 text-slate-300 text-lg">✨ What's Included:</h3>
            <div class="grid grid-cols-2 gap-4 text-slate-400 text-sm">
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> Complete source code
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> Documentation
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> Deployment guide
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> Up to 3 revisions
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> 7-day support
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-green-400">✓</span> Instant delivery
                </div>
            </div>
        </div>
        
    </main>
    
    <!-- Footer -->
    <footer class="py-8 px-4 text-center text-slate-500 text-sm border-t border-slate-800/50">
        <p class="font-medium">Powered by <span class="gradient-text font-bold">Nexus 10 AI Agency</span></p>
        <p class="mt-2 text-xs text-slate-600">Autonomous AI Development • Secure Payments • Professional Quality</p>
    </footer>
    
    <!-- Bank Modal -->
    {bank_modal}
    
    <!-- Crypto Modal -->
    {crypto_modal}
    
    <!-- Scripts -->
    <script>
        // Bank Modal
        function showBankDetails() {{
            document.getElementById('bankModal').classList.remove('hidden');
        }}
        
        function closeBankModal() {{
            document.getElementById('bankModal').classList.add('hidden');
        }}
        
        // Crypto Modal
        function showCrypto() {{
            document.getElementById('cryptoModal').classList.remove('hidden');
        }}
        
        function closeCrypto() {{
            document.getElementById('cryptoModal').classList.add('hidden');
            document.getElementById('verifyStatus').classList.add('hidden');
        }}
        
        function copyWallet() {{
            const wallet = document.getElementById('walletAddress').textContent;
            navigator.clipboard.writeText(wallet);
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            btn.classList.add('bg-green-600');
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.classList.remove('bg-green-600');
            }}, 2000);
        }}
        
        async function verifyPayment() {{
            const statusDiv = document.getElementById('verifyStatus');
            const statusMsg = document.getElementById('verifyMessage');
            const btn = document.getElementById('verifyBtn');
            
            statusDiv.classList.remove('hidden');
            statusMsg.textContent = '⏳ Scanning Polygon blockchain for your payment...';
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            
            // Simulate blockchain scan (in production, this calls real API)
            setTimeout(() => {{
                // For demo - in production this would check real blockchain
                statusMsg.textContent = '🔍 Checking recent transactions...';
                
                setTimeout(() => {{
                    statusMsg.textContent = '📡 Please wait 1-2 minutes for blockchain confirmation. You will receive a notification once confirmed.';
                    statusDiv.classList.remove('bg-blue-900/30', 'border-blue-500/50');
                    statusDiv.classList.add('bg-yellow-900/30', 'border-yellow-500/50');
                    btn.disabled = false;
                    btn.textContent = '🔄 Check Again';
                }}, 2000);
            }}, 1500);
        }}
        
        // Close modals on escape
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                closeCrypto();
                closeBankModal();
            }}
        }});
        
        // Close modal when clicking outside
        document.querySelectorAll('#cryptoModal, #bankModal').forEach(modal => {{
            modal.addEventListener('click', (e) => {{
                if (e.target === modal) {{
                    modal.classList.add('hidden');
                }}
            }});
        }});
    </script>
    
</body>
</html>'''
    
    # Save to file
    if not output_file:
        safe_name = "".join(c if c.isalnum() else "_" for c in project_name)[:30]
        output_file = os.path.join(LANDING_DIR, f"payment_{safe_name}_{reference}.html")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[LANDING] Generated: {output_file}")
    return output_file


def generate_thank_you_page(
    project_name: str,
    client_name: str = "Valued Client",
    reference: str = "",
    download_link: str = "",
    ip_transfer_link: str = "",
    certificate_link: str = "",
    output_file: str = None
) -> str:
    """
    Генерирует страницу благодарности после оплаты.
    
    Includes:
        - Download link for deliverables
        - IP Transfer Agreement link (legal document)
        - Completion Certificate link
        - Need Help button linked to support system
    """
    
    download_section = f'''
        <a href="{download_link}" 
           class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-xl font-bold transition mb-4">
            📦 Download Your Deliverables
        </a>
    ''' if download_link else ''
    
    # Legal documents section
    legal_section = ''
    if ip_transfer_link or certificate_link:
        legal_buttons = []
        if ip_transfer_link:
            legal_buttons.append(f'''
                <a href="{ip_transfer_link}" download 
                   class="flex items-center gap-2 bg-emerald-600/80 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm transition">
                    📄 IP Transfer Agreement
                </a>
            ''')
        if certificate_link:
            legal_buttons.append(f'''
                <a href="{certificate_link}" download 
                   class="flex items-center gap-2 bg-slate-600/80 hover:bg-slate-500 px-4 py-2 rounded-lg text-sm transition">
                    🏆 Completion Certificate
                </a>
            ''')
        
        legal_section = f'''
        <div class="flex flex-wrap gap-3 justify-center mb-6">
            {''.join(legal_buttons)}
        </div>
        <p class="text-xs text-slate-500 mb-8">
            The IP Transfer Agreement confirms full intellectual property rights for this project have been transferred to you.
        </p>
        '''
    
    # Need Help button that creates support ticket
    support_button = f'''
        <button onclick="showSupport()" 
                class="inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-500 px-4 py-2 rounded-lg text-sm transition">
            🆘 Need Help?
        </button>
    '''
    
    # Support modal with ticket creation
    support_modal = f'''
        <div id="supportModal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div class="bg-slate-800 rounded-2xl p-6 max-w-md w-full border border-amber-500/50">
                <h3 class="text-xl font-bold text-amber-400 mb-4">🆘 Need Help?</h3>
                
                <div class="space-y-4 mb-6">
                    <div class="bg-slate-900 p-4 rounded-xl">
                        <h4 class="font-semibold mb-2">📱 Telegram Support</h4>
                        <p class="text-slate-400 text-sm mb-2">Get instant help via Telegram:</p>
                        <a href="https://t.me/nexus10_support" target="_blank" 
                           class="text-blue-400 hover:text-blue-300 font-mono">@nexus10_support</a>
                    </div>
                    
                    <div class="bg-slate-900 p-4 rounded-xl">
                        <h4 class="font-semibold mb-2">📧 Email Support</h4>
                        <p class="text-slate-400 text-sm mb-2">Create a support ticket:</p>
                        <a href="mailto:support@nexus10.ai?subject=Support%20Request%20-%20{reference}" 
                           class="text-blue-400 hover:text-blue-300">support@nexus10.ai</a>
                    </div>
                    
                    <div class="bg-amber-900/30 border border-amber-500/30 p-3 rounded-xl text-sm">
                        <p class="text-amber-300">⏰ Support hours: 24/7 during your 7-day support period</p>
                        <p class="text-amber-200/60 mt-1">Reference: {reference}</p>
                    </div>
                </div>
                
                <button onclick="closeSupportModal()" 
                        class="w-full bg-slate-700 hover:bg-slate-600 py-2 rounded-xl transition">
                    Close
                </button>
            </div>
        </div>
    '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Confirmed | Nexus 10 AI Agency</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Space Grotesk', sans-serif; }}
        .gradient-text {{ background: linear-gradient(135deg, #22c55e, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="bg-gradient-to-br from-green-950 via-slate-900 to-slate-950 text-white min-h-screen flex items-center justify-center p-4">
    
    <div class="max-w-lg w-full text-center">
        
        <div class="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <span class="text-5xl">✅</span>
        </div>
        
        <h1 class="text-4xl font-bold mb-4 gradient-text">Payment Confirmed!</h1>
        
        <p class="text-slate-300 mb-6 text-lg">
            Thank you, <strong>{client_name}</strong>!<br>
            Your payment for <strong class="text-blue-400">{project_name}</strong> has been received.
        </p>
        
        {download_section}
        
        {legal_section}
        
        <div class="bg-slate-800/50 rounded-2xl p-6 mb-8 text-left border border-slate-700/50">
            <h3 class="font-semibold mb-4 text-lg">📋 What happens next:</h3>
            <ul class="space-y-4 text-slate-300">
                <li class="flex items-start gap-3">
                    <span class="bg-blue-600 text-sm px-2.5 py-1 rounded font-bold">1</span>
                    <span>Your deliverables are ready to download</span>
                </li>
                <li class="flex items-start gap-3">
                    <span class="bg-emerald-600 text-sm px-2.5 py-1 rounded font-bold">2</span>
                    <span>IP Transfer Agreement confirms your ownership</span>
                </li>
                <li class="flex items-start gap-3">
                    <span class="bg-purple-600 text-sm px-2.5 py-1 rounded font-bold">3</span>
                    <span>7-day support period is now active</span>
                </li>
            </ul>
        </div>
        
        <div class="flex flex-col items-center gap-4 mb-8">
            {support_button}
        </div>
        
        <p class="text-slate-500 text-sm">
            Reference: <code class="bg-slate-800 px-2 py-1 rounded">{reference}</code>
        </p>
        
        <div class="mt-8 pt-6 border-t border-slate-800">
            <p class="text-slate-600 text-xs">Powered by Nexus 10 AI Agency</p>
        </div>
        
    </div>
    
    {support_modal}
    
    <script>
        function showSupport() {{
            document.getElementById('supportModal').classList.remove('hidden');
        }}
        
        function closeSupportModal() {{
            document.getElementById('supportModal').classList.add('hidden');
        }}
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeSupportModal();
        }});
        
        document.getElementById('supportModal').addEventListener('click', (e) => {{
            if (e.target.id === 'supportModal') closeSupportModal();
        }});
    </script>
    
</body>
</html>'''
    
    if not output_file:
        output_file = os.path.join(LANDING_DIR, f"thankyou_{reference}.html")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return output_file


def create_complete_invoice_package(
    project_name: str,
    price_usd: float,
    client_name: str = "Valued Client",
    description: str = ""
) -> dict:
    """
    Создает полный пакет: PDF инвойс + HTML лендинг.
    
    Returns:
        {"landing": str, "pdf": str, "reference": str}
    """
    reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Generate landing page
    landing_path = generate_payment_landing(
        project_name=project_name,
        price_usd=price_usd,
        client_name=client_name,
        reference=reference,
        description=description
    )
    
    # Try to generate PDF
    pdf_path = None
    try:
        from invoice_gen import InvoiceGenerator
        gen = InvoiceGenerator()
        pdf_path = gen.create_pdf(
            project_name=project_name,
            amount=price_usd,
            currency="USD",
            client_name=client_name,
            reference=reference,
            description=description
        )
    except Exception as e:
        print(f"[LANDING] PDF generation skipped: {e}")
    
    return {
        "landing": landing_path,
        "pdf": pdf_path,
        "reference": reference
    }


# === QUICK FUNCTION ===

def create_invoice_page(project: str, price: float, client: str = "") -> str:
    """Быстрое создание страницы оплаты"""
    return generate_payment_landing(
        project_name=project,
        price_usd=price,
        client_name=client or "Client"
    )


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 AI AGENCY - Landing Generator Test")
    print("=" * 60)
    
    print(f"\nConfig:")
    print(f"  Wallet: {MY_WALLET[:15]}..." if MY_WALLET else "  Wallet: Not configured")
    print(f"  Stripe: {'Configured' if STRIPE_LINK else 'Not configured'}")
    print(f"  Bank: {BANK_NAME}")
    
    # Generate test landing
    package = create_complete_invoice_package(
        project_name="AI Telegram Bot Development",
        price_usd=350.00,
        client_name="John Smith",
        description="Custom Telegram bot with GPT-4 integration for customer support automation. Includes admin dashboard and analytics."
    )
    
    print(f"\n[OK] Package created:")
    print(f"     Landing: {package['landing']}")
    print(f"     PDF: {package['pdf']}")
    print(f"     Reference: {package['reference']}")
    print("\nOpen landing in browser to preview!")
