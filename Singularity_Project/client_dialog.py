# -*- coding: utf-8 -*-
"""
CLIENT DIALOG SYSTEM - AI-powered client communication
=======================================================
Automatically answers client questions and handles negotiations
"""

import os
import openai
from datetime import datetime
from typing import Dict, Optional

# API
openai.api_key = os.getenv('OPENAI_API_KEY', '')

# System prompt for client communication
CLIENT_DIALOG_PROMPT = """You are a professional freelance developer assistant.
You communicate with clients on behalf of NEXUS-6 Development.

Your communication style:
- Professional but friendly
- Confident and knowledgeable
- Clear and concise
- Always helpful

Key information about our services:
- We specialize in Python development
- Minimum project budget: $50 USD
- Typical delivery: 3-7 days depending on complexity
- We provide: Complete code, documentation, 24h support
- Payment: Stripe (cards) or Wise (bank transfer)

Rules:
1. NEVER share full code before payment - only snippets/previews
2. Always confirm project scope before starting
3. If asked about price, give estimate based on complexity
4. If client wants discount, max 10% for first order
5. Always be professional, never argue
6. If unsure, say you'll check and get back

Current project context will be provided in the message."""


def analyze_client_message(message: str, order_context: Dict = None) -> Dict:
    """
    Analyze client message and generate appropriate response
    
    Args:
        message: Client's message
        order_context: Current order details (if any)
    
    Returns:
        {response, intent, suggested_action, confidence}
    """
    if not openai.api_key:
        return {
            "response": "I'll get back to you shortly.",
            "intent": "unknown",
            "suggested_action": None,
            "confidence": 0.0
        }
    
    # Build context
    context = ""
    if order_context:
        context = """
Current Order Context:
- Reference: {}
- Title: {}
- Price: ${}
- Status: {}
""".format(
            order_context.get('reference', 'N/A'),
            order_context.get('title', 'N/A'),
            order_context.get('estimated_price', 'TBD'),
            order_context.get('status', 'N/A')
        )
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CLIENT_DIALOG_PROMPT},
                {"role": "user", "content": f"""
Client message: "{message}"

{context}

Respond to the client professionally. Also analyze:
1. What is the client's intent? (question/ready_to_pay/negotiating/unclear)
2. Should we suggest an action? (send_invoice/provide_estimate/clarify/none)

Format your response as:
RESPONSE: [your response to client]
INTENT: [intent]
ACTION: [suggested action]
"""}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        full_response = response.choices[0].message.content
        
        # Parse response
        client_response = ""
        intent = "unknown"
        action = None
        
        lines = full_response.split('\n')
        for line in lines:
            if line.startswith("RESPONSE:"):
                client_response = line.replace("RESPONSE:", "").strip()
            elif line.startswith("INTENT:"):
                intent = line.replace("INTENT:", "").strip().lower()
            elif line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip().lower()
                if action == "none":
                    action = None
        
        # If parsing failed, use full response
        if not client_response:
            client_response = full_response
        
        return {
            "response": client_response,
            "intent": intent,
            "suggested_action": action,
            "confidence": 0.85
        }
        
    except Exception as e:
        return {
            "response": "Thank you for your message. I'll review and get back to you shortly.",
            "intent": "error",
            "suggested_action": None,
            "confidence": 0.0,
            "error": str(e)
        }


def generate_invoice_message(order: Dict) -> str:
    """Generate invoice message for client"""
    price = order.get('final_price') or order.get('estimated_price', 100)
    ref = order.get('reference', 'TBD')
    title = order.get('title', 'Project')
    
    return """**Invoice for Your Project**

Project: {}
Reference: `{}`
Amount: **${:.2f} USD**

**Payment Options:**
• Credit/Debit Card (Stripe) - Instant
• Bank Transfer (Wise) - 1-2 business days

Click the payment button below or use the links provided.

After payment confirmation, you'll receive:
✓ Complete source code
✓ Documentation
✓ Setup instructions
✓ 24h support

Thank you for choosing NEXUS-6 Development!""".format(title[:50], ref, price)


def generate_scope_confirmation(order: Dict) -> str:
    """Generate scope confirmation message"""
    title = order.get('title', 'Project')
    description = order.get('description', '')
    price = order.get('estimated_price', 100)
    
    return """**Project Scope Confirmation**

**Project:** {}

**Deliverables:**
• Complete Python solution
• Source code with documentation
• Setup/installation guide
• 1 week of support

**Estimated Price:** ${:.0f} USD
**Timeline:** 3-5 business days

Please confirm if this scope is correct, or let me know if you need any adjustments.

Reply "Confirmed" to proceed, or describe any changes needed.""".format(title, price)


def handle_negotiation(client_offer: str, original_price: float) -> Dict:
    """Handle price negotiation"""
    # Parse offer
    import re
    match = re.search(r'\$?(\d+)', client_offer)
    offered_price = float(match.group(1)) if match else 0
    
    min_acceptable = original_price * 0.85  # Max 15% discount
    
    if offered_price >= original_price:
        return {
            "accept": True,
            "final_price": original_price,
            "response": "Great! The price is ${:.0f}. I'll prepare the invoice for you.".format(original_price)
        }
    elif offered_price >= min_acceptable:
        # Accept with small negotiation
        counter = max(offered_price, original_price * 0.9)
        return {
            "accept": True,
            "final_price": counter,
            "response": "I can do ${:.0f} for this project. Does that work for you?".format(counter)
        }
    else:
        return {
            "accept": False,
            "final_price": original_price,
            "response": "I appreciate your offer, but ${:.0f} is the minimum I can do for this scope. The quality and support I provide is worth it. Would you like to proceed?".format(min_acceptable)
        }


# Quick response templates
QUICK_RESPONSES = {
    "timeline": "Typical delivery is 3-5 business days, depending on complexity. For urgent projects, I can expedite for an additional 20%.",
    "payment": "I accept payment via Stripe (cards) or Wise (bank transfer). Payment is required before delivery of the final code.",
    "support": "All projects include 24 hours of support after delivery. Extended support packages are available.",
    "revision": "I include 2 rounds of revisions in the base price. Additional revisions can be arranged.",
    "nda": "Yes, I can sign an NDA. Please share your document and I'll review it.",
    "portfolio": "I've completed 50+ Python projects including bots, scrapers, APIs, and automation tools. I can share relevant examples.",
    "start": "Once we confirm the scope and I receive payment, I can start immediately.",
}


def get_quick_response(topic: str) -> Optional[str]:
    """Get quick response for common topics"""
    topic_lower = topic.lower()
    
    for key, response in QUICK_RESPONSES.items():
        if key in topic_lower:
            return response
    
    return None


# Test
if __name__ == "__main__":
    print("Testing Client Dialog System...")
    
    test_messages = [
        "How much would a Telegram bot cost?",
        "Can you do it for $30?",
        "I'm ready to pay, send me the invoice",
        "What's your timeline?"
    ]
    
    for msg in test_messages:
        print(f"\nClient: {msg}")
        result = analyze_client_message(msg, {"title": "Telegram Bot", "estimated_price": 100})
        print(f"Bot: {result['response']}")
        print(f"Intent: {result['intent']}, Action: {result['suggested_action']}")








