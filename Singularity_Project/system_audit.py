# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - System Audit
=================================
Полная проверка всех систем оплаты и агентов.
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()


def check_payment_systems():
    """Проверка всех систем оплаты"""
    print("=" * 60)
    print("PAYMENT SYSTEMS AUDIT")
    print("=" * 60)
    
    issues = []
    
    # 1. Stripe
    stripe_link = os.getenv('STRIPE_PAYMENT_LINK', '')
    print("\n[1] STRIPE (Card Payments)")
    if stripe_link:
        print("    Status: CONFIGURED")
        print(f"    Link: {stripe_link[:50]}...")
    else:
        print("    Status: NOT CONFIGURED")
        issues.append("Add STRIPE_PAYMENT_LINK to .env")
    
    # 2. Wise  
    wise_tag = os.getenv('WISE_TAG', '')
    print("\n[2] WISE (Bank Transfer)")
    if wise_tag:
        print("    Status: CONFIGURED")
        print(f"    Tag: {wise_tag}")
    else:
        print("    Status: NOT CONFIGURED")
        issues.append("Add WISE_TAG to .env")
    
    # 3. Crypto
    wallet = os.getenv('MY_CRYPTO_WALLET', '')
    polygonscan = os.getenv('POLYGONSCAN_API_KEY', '')
    print("\n[3] CRYPTO (Polygon USDT/USDC)")
    if wallet:
        print(f"    Wallet: CONFIGURED - {wallet[:15]}...")
    else:
        print("    Wallet: NOT CONFIGURED")
        issues.append("Add MY_CRYPTO_WALLET to .env")
    
    if polygonscan:
        print("    Polygonscan API: CONFIGURED")
    else:
        print("    Polygonscan API: NOT CONFIGURED")
        issues.append("Add POLYGONSCAN_API_KEY to .env")
    
    # 4. Bank Details
    bank_iban = os.getenv('BANK_IBAN', '')
    bank_swift = os.getenv('BANK_SWIFT', '')
    print("\n[4] BANK (SEPA/SWIFT)")
    if bank_iban:
        print("    IBAN: CONFIGURED")
    else:
        print("    IBAN: NOT SET - landing shows placeholder")
        
    if bank_swift:
        print("    SWIFT: CONFIGURED")
    else:
        print("    SWIFT: NOT SET - landing shows placeholder")
    
    # 5. Telegram
    tg_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    admin_id = os.getenv('TELEGRAM_ADMIN_ID', os.getenv('ADMIN_ID', ''))
    print("\n[5] TELEGRAM")
    if tg_token:
        print("    Bot Token: CONFIGURED")
    else:
        print("    Bot Token: NOT CONFIGURED")
        issues.append("Add TELEGRAM_BOT_TOKEN to .env")
        
    if admin_id:
        print(f"    Admin ID: {admin_id}")
    else:
        print("    Admin ID: NOT CONFIGURED")
        issues.append("Add TELEGRAM_ADMIN_ID to .env")
    
    # 6. OpenAI
    openai_key = os.getenv('OPENAI_API_KEY', '')
    print("\n[6] OPENAI")
    if openai_key:
        print(f"    API Key: CONFIGURED - {openai_key[:12]}...")
    else:
        print("    API Key: NOT CONFIGURED")
        issues.append("Add OPENAI_API_KEY to .env")
    
    return issues


def check_agents():
    """Проверка агентов"""
    print("\n" + "=" * 60)
    print("AGENTS AUDIT")
    print("=" * 60)
    
    issues = []
    
    try:
        from agents import NexusAgents, get_all_agents
        
        # Test initialization
        print("\n[1] Agent Initialization")
        agents = NexusAgents()
        print("    Status: OK")
        print(f"    LLM: {agents.llm.model_name}")
        print(f"    Tools loaded: {len(agents.tools)}")
        
        # List agents
        print("\n[2] Available Agents:")
        agent_roles = {
            "Hunter": "Job search and lead generation",
            "Architect": "Task decomposition and planning",
            "Doer": "Code writing and implementation",
            "QA Critic": "Quality assurance and testing",
            "Collector": "Invoicing and payment tracking",
            "Strategist": "Process optimization and learning"
        }
        
        for name, desc in agent_roles.items():
            print(f"    - {name}: {desc}")
        
        # Check tools
        print("\n[3] Agent Tools:")
        for tool in agents.tools:
            tool_name = getattr(tool, 'name', str(type(tool).__name__))
            print(f"    - {tool_name}")
        
        if len(agents.tools) < 2:
            issues.append("Limited tools - add more search capabilities")
            
    except Exception as e:
        print(f"    ERROR: {e}")
        issues.append(f"Agent init error: {e}")
    
    return issues


def check_communication():
    """Проверка коммуникации между агентами"""
    print("\n" + "=" * 60)
    print("AGENT COMMUNICATION AUDIT")
    print("=" * 60)
    
    issues = []
    
    print("\n[1] Communication Flow:")
    flow = """
    Hunter (finds leads)
       |
       v
    Architect (plans work)
       |
       v
    Doer (writes code)
       |
       v
    QA Critic (validates)
       |
       v
    Collector (invoices)
       |
       v
    Strategist (learns)
    """
    print(flow)
    
    print("[2] Data Handoff Points:")
    handoffs = [
        ("Hunter -> Architect", "Lead data with requirements"),
        ("Architect -> Doer", "Technical plan and specifications"),
        ("Doer -> QA", "Generated code for review"),
        ("QA -> Collector", "Approval status and score"),
        ("Collector -> Client", "Invoice and payment links"),
        ("All -> Strategist", "Metrics and outcomes")
    ]
    
    for src_dest, data in handoffs:
        print(f"    {src_dest}: {data}")
    
    print("\n[3] Delegation Settings:")
    print("    Hunter: allow_delegation=False (works alone)")
    print("    Others: allow_delegation=True by default")
    
    print("\n[4] Potential Issues:")
    potential_issues = [
        "No automatic retry if QA rejects code",
        "No direct communication channel between agents",
        "Client feedback loop not automated"
    ]
    for issue in potential_issues:
        print(f"    - {issue}")
        issues.append(issue)
    
    return issues


def check_support_system():
    """Проверка системы поддержки"""
    print("\n" + "=" * 60)
    print("SUPPORT SYSTEM AUDIT")
    print("=" * 60)
    
    issues = []
    
    print("\n[1] Current Support Channels:")
    print("    Landing page says: 'Contact via Telegram'")
    print("    BUT: No automated support bot configured")
    print("    BUT: No support email configured")
    print("    BUT: No ticket system")
    
    print("\n[2] Who Handles Support?")
    print("    Current: MANUAL - Admin receives Telegram messages")
    print("    Problem: No 24/7 coverage")
    print("    Problem: No AI-assisted responses")
    
    print("\n[3] What's Missing:")
    missing = [
        "Automated FAQ responses",
        "Ticket tracking system",
        "Support hours definition",
        "Escalation process",
        "Client satisfaction tracking"
    ]
    for item in missing:
        print(f"    - {item}")
        issues.append(f"Support: {item}")
    
    print("\n[4] Recommendations:")
    recommendations = [
        "Add /support command to Telegram bot",
        "Create AI-powered FAQ responder",
        "Define support hours on landing page",
        "Add client_dialog.py integration",
        "Create support ticket database"
    ]
    for rec in recommendations:
        print(f"    + {rec}")
    
    return issues


def main():
    """Run full audit"""
    print("\n" + "=" * 60)
    print("NEXUS 10 AI AGENCY - FULL SYSTEM AUDIT")
    print("=" * 60)
    
    all_issues = []
    
    # Payment systems
    all_issues.extend(check_payment_systems())
    
    # Agents
    all_issues.extend(check_agents())
    
    # Communication
    all_issues.extend(check_communication())
    
    # Support
    all_issues.extend(check_support_system())
    
    # Summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    
    if all_issues:
        print(f"\nFound {len(all_issues)} issues to address:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\nNo critical issues found!")
    
    # Overall score
    total_checks = 20
    passed = total_checks - len(all_issues)
    score = int((passed / total_checks) * 100)
    
    print(f"\nOVERALL SCORE: {score}/100")
    
    if score >= 80:
        print("Status: PRODUCTION READY")
    elif score >= 60:
        print("Status: NEEDS IMPROVEMENTS")
    else:
        print("Status: NOT READY")


if __name__ == "__main__":
    main()


