# -*- coding: utf-8 -*-
"""
NEXUS CORE - Profit Pipeline
=============================
Unified business flow from lead to delivery.

Flow:
1. INTAKE → Lead arrives
2. VETTING → Gatekeeper checks profitability
3. QUOTE → Price locked after approval
4. PAYMENT → Invoice + monitoring
5. EXECUTE → Code generation
6. DELIVER → Delivery after payment
7. CLOSE → Archive, record profit

Ported from: Singularity_Project/profit_pipeline.py
Author: NEXUS 10 AI Agency
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [PIPELINE] %(message)s'
)
logger = logging.getLogger('pipeline')


class PipelineStage(Enum):
    """Pipeline stages"""
    INTAKE = "intake"
    VETTING = "vetting"
    QUOTING = "quoting"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    EXECUTING = "executing"
    DELIVERED = "delivered"
    CLOSED = "closed"
    REJECTED = "rejected"


@dataclass
class PipelineProject:
    """Project in the pipeline"""
    id: int = 0
    reference: str = ""
    title: str = ""
    description: str = ""
    client_name: str = ""
    client_budget: float = 0.0
    platform: str = "direct"
    stage: PipelineStage = PipelineStage.INTAKE
    
    # Analysis
    estimated_margin: float = 0.0
    estimated_profit: float = 0.0
    suggested_price: Optional[float] = None
    fixed_price: Optional[float] = None
    
    # Payment
    payment_confirmed: bool = False
    payment_method: str = ""
    payment_tx_hash: str = ""
    
    # Timestamps
    created_at: str = ""
    paid_at: str = ""
    delivered_at: str = ""


class ProfitPipeline:
    """
    Main pipeline orchestrator.
    
    Usage:
        pipeline = ProfitPipeline()
        
        # Add lead
        project = pipeline.intake("Bot Development", "Telegram bot", 200)
        
        # Process
        pipeline.vet(project)
        pipeline.send_invoice(project)
        # ... wait for payment ...
        pipeline.deliver(project)
    """
    
    def __init__(self, notify_callback: Callable = None):
        self.notify = notify_callback or self._default_notify
        self._init_components()
    
    def _init_components(self):
        """Initialize pipeline components"""
        try:
            from .gatekeeper import Gatekeeper
            self.gatekeeper = Gatekeeper()
        except Exception as e:
            logger.warning(f"Gatekeeper not available: {e}")
            self.gatekeeper = None
        
        try:
            from .invoices import InvoiceGenerator
            self.invoice_gen = InvoiceGenerator()
        except Exception as e:
            logger.warning(f"InvoiceGenerator not available: {e}")
            self.invoice_gen = None
        
        try:
            from .blockchain import BlockchainEye
            self.blockchain = BlockchainEye()
        except Exception as e:
            logger.warning(f"BlockchainEye not available: {e}")
            self.blockchain = None
        
        try:
            from .database import NexusDatabase
            self.db = NexusDatabase()
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            self.db = None
    
    def _default_notify(self, message: str, level: str = "info"):
        """Default notification (just log)"""
        logger.info(f"[NOTIFY] {message}")
    
    # === STAGE 1: INTAKE ===
    
    def intake(self, title: str, description: str, client_budget: float,
               client_name: str = "Client", platform: str = "direct") -> PipelineProject:
        """Intake a new lead"""
        reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        project = PipelineProject(
            reference=reference,
            title=title,
            description=description,
            client_name=client_name,
            client_budget=client_budget,
            platform=platform,
            stage=PipelineStage.INTAKE,
            created_at=datetime.now().isoformat()
        )
        
        # Save to database
        if self.db:
            project.id = self.db.add_project(
                title=title,
                budget=client_budget,
                description=description,
                client_name=client_name,
                platform=platform,
                reference=reference
            )
        
        self.notify(f"📥 New lead: {title} (${client_budget})")
        logger.info(f"Intake: {reference} - {title}")
        
        return project
    
    # === STAGE 2: VETTING ===
    
    def vet(self, project: PipelineProject) -> bool:
        """Vet project profitability"""
        if not self.gatekeeper:
            logger.warning("Gatekeeper not available, auto-accepting")
            return True
        
        project.stage = PipelineStage.VETTING
        
        analysis = self.gatekeeper.evaluate(
            budget=project.client_budget,
            complexity="MEDIUM",
            description=project.description,
            platform=project.platform
        )
        
        project.estimated_margin = analysis.margin_percent
        project.estimated_profit = analysis.net_profit
        project.suggested_price = analysis.suggested_price
        
        from .gatekeeper import Verdict
        
        if analysis.verdict == Verdict.ACCEPT:
            self.notify(f"✅ Accepted: {project.title} ({analysis.margin_percent}% margin)")
            project.stage = PipelineStage.QUOTING
            return True
        elif analysis.verdict == Verdict.NEGOTIATE:
            self.notify(f"💬 Negotiate: {project.title} - suggest ${analysis.suggested_price}")
            return False
        else:
            self.notify(f"❌ Rejected: {project.title} - {analysis.reason}")
            project.stage = PipelineStage.REJECTED
            return False
    
    # === STAGE 3: INVOICE ===
    
    def send_invoice(self, project: PipelineProject) -> Optional[str]:
        """Generate and return invoice path"""
        project.stage = PipelineStage.AWAITING_PAYMENT
        
        if not self.invoice_gen:
            logger.warning("Invoice generator not available")
            return None
        
        price = project.fixed_price or project.suggested_price or project.client_budget
        
        pdf_path = self.invoice_gen.create_pdf(
            project_name=project.title,
            amount=price,
            currency="USD",
            client_name=project.client_name,
            reference=project.reference
        )
        
        self.notify(f"💰 Invoice sent: {project.title} - ${price}")
        
        # Start blockchain monitoring
        if self.blockchain:
            self.blockchain.register_pending_payment(
                project.reference, 
                price,
                callback=lambda ref, tx: self._on_payment_confirmed(project, tx)
            )
        
        return pdf_path
    
    def _on_payment_confirmed(self, project: PipelineProject, tx: Dict):
        """Callback when payment is confirmed"""
        project.payment_confirmed = True
        project.payment_method = "crypto"
        project.payment_tx_hash = tx.get("hash", "")
        project.paid_at = datetime.now().isoformat()
        project.stage = PipelineStage.PAID
        
        if self.db:
            self.db.mark_project_paid(project.id, "crypto", project.payment_tx_hash)
        
        self.notify(f"💰 PAYMENT CONFIRMED: {project.title}")
    
    # === STAGE 4: CHECK PAYMENT ===
    
    def check_payment(self, project: PipelineProject) -> bool:
        """Check if payment received"""
        if project.payment_confirmed:
            return True
        
        if not self.blockchain:
            return False
        
        price = project.fixed_price or project.client_budget
        result = self.blockchain.check_payment(price)
        
        if result["found"]:
            self._on_payment_confirmed(project, result)
            return True
        
        return False
    
    def confirm_payment_manual(self, project: PipelineProject, 
                                method: str = "manual", tx_ref: str = ""):
        """Manually confirm payment"""
        project.payment_confirmed = True
        project.payment_method = method
        project.payment_tx_hash = tx_ref
        project.paid_at = datetime.now().isoformat()
        project.stage = PipelineStage.PAID
        
        if self.db:
            self.db.mark_project_paid(project.id, method, tx_ref)
        
        self.notify(f"💰 Payment confirmed: {project.title} ({method})")
    
    # === STAGE 5: DELIVER ===
    
    def deliver(self, project: PipelineProject) -> bool:
        """Deliver project"""
        if not project.payment_confirmed:
            self.notify(f"⚠️ Cannot deliver: {project.title} - not paid")
            return False
        
        project.stage = PipelineStage.DELIVERED
        project.delivered_at = datetime.now().isoformat()
        
        if self.db:
            self.db.mark_project_delivered(project.id)
        
        self.notify(f"📦 DELIVERED: {project.title}")
        
        return True
    
    # === STAGE 6: CLOSE ===
    
    def close(self, project: PipelineProject):
        """Close and archive project"""
        project.stage = PipelineStage.CLOSED
        
        if self.db:
            self.db.update_project_status(project.id, "closed")
        
        self.notify(f"🏁 CLOSED: {project.title} - Profit: ${project.estimated_profit}")
    
    # === STATUS ===
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        stats = {}
        
        if self.db:
            stats = self.db.get_stats()
        
        stats["gatekeeper_ready"] = self.gatekeeper is not None
        stats["invoices_ready"] = self.invoice_gen is not None
        stats["blockchain_ready"] = self.blockchain is not None
        
        return stats


# === SINGLETON ===
_pipeline_instance: Optional[ProfitPipeline] = None


def get_pipeline() -> ProfitPipeline:
    """Get or create pipeline singleton"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ProfitPipeline()
    return _pipeline_instance


# === QUICK FUNCTIONS ===

def intake_project(title: str, description: str, budget: float) -> PipelineProject:
    """Quick intake"""
    return get_pipeline().intake(title, description, budget)


def vet_project(project: PipelineProject) -> bool:
    """Quick vet"""
    return get_pipeline().vet(project)


def get_pipeline_status() -> Dict:
    """Quick status"""
    return get_pipeline().get_status()



