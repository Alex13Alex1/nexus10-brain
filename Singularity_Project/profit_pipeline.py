# -*- coding: utf-8 -*-
"""
PROFIT PIPELINE v1.0 - Autonomous Revenue Conveyor
===================================================
Единая воронка: Сырой запрос → Оплаченный проект

Flow:
1. INTAKE → Lead arrives (Hunter/Manual)
2. VETTING → Gatekeeper checks profitability (≥20% margin)
3. CLARIFY → Interviewer generates questions if needed
4. SPECIFY → DeepSpec creates atomic requirements
5. QUOTE → Fixed price locked after spec approval
6. PAYMENT → Invoice sent, blockchain/card monitoring
7. EXECUTE → Code generation with self-healing
8. DELIVER → Automatic delivery after payment confirmed
9. CLOSE → Project archived, profit recorded

Author: NEXUS 10 AI Agency
"""

import os
import sys
import time
import json
import sqlite3
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [PIPELINE] %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('profit_pipeline')


class PipelineStage(Enum):
    """Pipeline stages"""
    INTAKE = "intake"
    VETTING = "vetting"
    CLARIFYING = "clarifying"
    SPECIFYING = "specifying"
    QUOTING = "quoting"
    AWAITING_PAYMENT = "awaiting_payment"
    EXECUTING = "executing"
    QA_REVIEW = "qa_review"
    READY_TO_DELIVER = "ready_to_deliver"
    DELIVERED = "delivered"
    PAID = "paid"
    CLOSED = "closed"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class RejectionReason(Enum):
    """Why a project was rejected"""
    LOW_MARGIN = "Margin below 20%"
    BELOW_MINIMUM = "Budget below $50"
    UNCLEAR_REQUIREMENTS = "Requirements too vague"
    CLIENT_UNRESPONSIVE = "Client didn't respond to questions"
    TECHNICAL_INFEASIBLE = "Technically not feasible"
    TIME_CONSTRAINT = "Timeline impossible"


@dataclass
class PipelineProject:
    """Project moving through the pipeline"""
    id: int
    reference: str
    title: str
    description: str
    client_name: str
    client_budget: float
    platform: str
    stage: PipelineStage = PipelineStage.INTAKE
    
    # Gatekeeper results
    estimated_margin: float = 0.0
    estimated_profit: float = 0.0
    estimated_hours: float = 0.0
    gatekeeper_verdict: str = ""
    suggested_price: Optional[float] = None
    counter_offer_sent: bool = False
    
    # Interviewer results
    clarifying_questions: List[str] = field(default_factory=list)
    client_answers: Dict[str, str] = field(default_factory=dict)
    
    # Specification
    spec_id: Optional[int] = None
    fixed_price: Optional[float] = None
    spec_approved: bool = False
    
    # Payment
    payment_method: str = ""
    payment_reference: str = ""
    payment_confirmed: bool = False
    payment_tx_hash: str = ""
    
    # Execution
    code_generated: str = ""
    qa_score: int = 0
    deliverables: Dict[str, str] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = ""
    vetted_at: str = ""
    quoted_at: str = ""
    paid_at: str = ""
    delivered_at: str = ""
    closed_at: str = ""
    
    # Rejection
    rejected: bool = False
    rejection_reason: str = ""


class ProfitPipeline:
    """
    Main orchestrator that moves projects through the profit pipeline.
    
    Usage:
        pipeline = ProfitPipeline()
        
        # Add new lead
        project = pipeline.intake(title, description, budget, client)
        
        # Process automatically
        pipeline.process(project)
        
        # Or step by step
        pipeline.vet(project)
        pipeline.clarify(project)
        pipeline.specify(project)
        ...
    """
    
    def __init__(self, 
                 auto_mode: bool = True,
                 notify_callback: Callable = None):
        """
        Initialize pipeline.
        
        Args:
            auto_mode: If True, automatically process through stages
            notify_callback: Function to call with notifications (e.g., send to Telegram)
        """
        self.auto_mode = auto_mode
        self.notify = notify_callback or self._default_notify
        self.running = False
        self.monitor_thread = None
        
        # Initialize components
        self._init_components()
        
        # Database
        self.db_path = os.path.join(os.getcwd(), 'data', 'pipeline.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
        logger.info("ProfitPipeline initialized")
    
    def _init_components(self):
        """Initialize all pipeline components"""
        try:
            from gatekeeper import Gatekeeper
            self.gatekeeper = Gatekeeper()
        except Exception as e:
            logger.error(f"Gatekeeper init failed: {e}")
            self.gatekeeper = None
        
        try:
            from interviewer import Interviewer
            self.interviewer = Interviewer()
        except Exception as e:
            logger.error(f"Interviewer init failed: {e}")
            self.interviewer = None
        
        try:
            from deep_spec import DeepSpecGenerator
            self.spec_generator = DeepSpecGenerator()
        except Exception as e:
            logger.error(f"DeepSpec init failed: {e}")
            self.spec_generator = None
        
        try:
            from engineer_agent import self_healing_generate
            self.code_generator = self_healing_generate
        except Exception as e:
            logger.error(f"Engineer init failed: {e}")
            self.code_generator = None
        
        try:
            from qa_validator import QAValidator
            self.qa_validator = QAValidator()
        except Exception as e:
            logger.error(f"QA Validator init failed: {e}")
            self.qa_validator = None
    
    def _init_db(self):
        """Initialize pipeline database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE,
                title TEXT,
                description TEXT,
                client_name TEXT,
                client_budget REAL,
                platform TEXT,
                stage TEXT,
                estimated_margin REAL,
                estimated_profit REAL,
                suggested_price REAL,
                fixed_price REAL,
                payment_confirmed INTEGER DEFAULT 0,
                qa_score INTEGER,
                rejected INTEGER DEFAULT 0,
                rejection_reason TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                stage TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _default_notify(self, message: str, level: str = "info"):
        """Default notification (just log)"""
        logger.info(f"[NOTIFY] {message}")
    
    def _log_action(self, project_id: int, stage: str, action: str, details: str = ""):
        """Log pipeline action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pipeline_log (project_id, stage, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, stage, action, details, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    # =========================================================================
    # STAGE 1: INTAKE
    # =========================================================================
    
    def intake(self,
               title: str,
               description: str,
               client_budget: float,
               client_name: str = "Unknown",
               platform: str = "direct") -> PipelineProject:
        """
        Intake a new lead into the pipeline.
        
        Args:
            title: Project title
            description: Full project description
            client_budget: Client's proposed budget
            client_name: Client identifier
            platform: Source platform (upwork, direct, etc.)
            
        Returns:
            PipelineProject ready for processing
        """
        reference = f"NX10-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        project = PipelineProject(
            id=0,  # Will be set by DB
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pipeline_projects 
            (reference, title, description, client_name, client_budget, platform, stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reference, title, description, client_name, client_budget, platform, 
              PipelineStage.INTAKE.value, project.created_at, project.created_at))
        project.id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._log_action(project.id, "INTAKE", "Project added to pipeline", 
                        f"Budget: ${client_budget}, Platform: {platform}")
        
        self.notify(f"📥 New lead: {title} (${client_budget}) from {platform}")
        
        logger.info(f"Intake: {reference} - {title} (${client_budget})")
        
        return project
    
    # =========================================================================
    # STAGE 2: VETTING (Gatekeeper)
    # =========================================================================
    
    def vet(self, project: PipelineProject) -> bool:
        """
        Vet project profitability using Gatekeeper.
        
        Returns:
            True if project should proceed, False if rejected/needs negotiation
        """
        if not self.gatekeeper:
            logger.error("Gatekeeper not available")
            return False
        
        project.stage = PipelineStage.VETTING
        
        # Analyze profitability
        analysis = self.gatekeeper.evaluate(
            budget=project.client_budget,
            complexity="MEDIUM",  # Will be refined later
            description=project.description,
            platform=project.platform
        )
        
        project.estimated_margin = analysis.margin_percent
        project.estimated_profit = analysis.net_profit
        project.estimated_hours = analysis.estimated_hours
        project.gatekeeper_verdict = analysis.verdict.value
        project.suggested_price = analysis.suggested_price
        project.vetted_at = datetime.now().isoformat()
        
        # Update database
        self._update_project(project)
        
        self._log_action(project.id, "VETTING", analysis.verdict.value,
                        f"Margin: {analysis.margin_percent}%, Profit: ${analysis.net_profit}")
        
        if analysis.verdict.value == "ACCEPT":
            logger.info(f"Vet ACCEPTED: {project.reference} - {analysis.margin_percent}% margin")
            self.notify(f"✅ Vet passed: {project.title} - {analysis.margin_percent}% margin")
            return True
        
        elif analysis.verdict.value == "NEGOTIATE":
            logger.info(f"Vet NEGOTIATE: {project.reference} - need ${analysis.suggested_price}")
            
            # Generate counter-offer
            counter_offer = self.gatekeeper.generate_negotiation_email(
                analysis, project.title, project.client_name
            )
            
            self._log_action(project.id, "VETTING", "Counter-offer generated",
                           f"Suggested: ${analysis.suggested_price}")
            
            self.notify(f"💬 Negotiate: {project.title} - suggest ${analysis.suggested_price}")
            
            # Store counter-offer for sending
            project.counter_offer_sent = False
            project.stage = PipelineStage.BLOCKED
            self._update_project(project)
            
            return False
        
        else:  # DECLINE
            logger.info(f"Vet REJECTED: {project.reference} - {analysis.reason}")
            project.rejected = True
            project.rejection_reason = RejectionReason.LOW_MARGIN.value if analysis.margin_percent > 0 else RejectionReason.BELOW_MINIMUM.value
            project.stage = PipelineStage.REJECTED
            self._update_project(project)
            
            self.notify(f"❌ Rejected: {project.title} - {project.rejection_reason}")
            
            return False
    
    # =========================================================================
    # STAGE 3: CLARIFYING (Interviewer)
    # =========================================================================
    
    def clarify(self, project: PipelineProject) -> bool:
        """
        Check if requirements are clear, generate questions if needed.
        
        Returns:
            True if requirements clear, False if waiting for answers
        """
        if not self.interviewer:
            logger.warning("Interviewer not available, skipping clarification")
            return True
        
        project.stage = PipelineStage.CLARIFYING
        
        # Analyze requirements
        result = self.interviewer.analyze_and_ask(project.description, use_ai=True)
        
        if result.confidence_score >= 0.7 or len(result.questions) == 0:
            # Requirements clear enough
            logger.info(f"Clarify OK: {project.reference} - confidence {result.confidence_score:.0%}")
            return True
        
        # Need more info
        project.clarifying_questions = result.questions
        project.stage = PipelineStage.BLOCKED
        self._update_project(project)
        
        self._log_action(project.id, "CLARIFYING", "Questions generated",
                        f"{len(result.questions)} questions, confidence: {result.confidence_score:.0%}")
        
        # Format questions for client
        formatted = self.interviewer.format_questions_for_client(result, project.title)
        
        self.notify(f"❓ Need clarification for: {project.title}\n{formatted}")
        
        logger.info(f"Clarify BLOCKED: {project.reference} - {len(result.questions)} questions pending")
        
        return False
    
    def answer_questions(self, project: PipelineProject, answers: Dict[str, str]) -> bool:
        """
        Process client's answers to clarifying questions.
        
        Args:
            project: The project
            answers: Dict mapping question -> answer
            
        Returns:
            True if all questions answered, False otherwise
        """
        project.client_answers = answers
        
        # Check if all answered
        unanswered = [q for q in project.clarifying_questions if q not in answers]
        
        if unanswered:
            self._log_action(project.id, "CLARIFYING", "Partial answers",
                           f"{len(unanswered)} questions still pending")
            return False
        
        # All answered - enhance description
        enhanced = project.description + "\n\n--- CLIENT CLARIFICATIONS ---\n"
        for q, a in answers.items():
            enhanced += f"\nQ: {q}\nA: {a}\n"
        
        project.description = enhanced
        project.stage = PipelineStage.SPECIFYING
        self._update_project(project)
        
        self._log_action(project.id, "CLARIFYING", "All questions answered", "")
        
        return True
    
    # =========================================================================
    # STAGE 4: SPECIFYING (Deep Spec)
    # =========================================================================
    
    def specify(self, project: PipelineProject) -> bool:
        """
        Generate detailed specification with atomic requirements.
        
        Returns:
            True if spec generated successfully
        """
        if not self.spec_generator:
            logger.warning("DeepSpec not available")
            return False
        
        project.stage = PipelineStage.SPECIFYING
        
        # Generate spec
        spec = self.spec_generator.generate(
            title=project.title,
            description=project.description,
            budget_hint=project.suggested_price or project.client_budget,
            project_id=project.id
        )
        
        project.spec_id = 1  # Would be from DB
        project.estimated_hours = spec.total_hours
        project.fixed_price = spec.fixed_price
        
        self._update_project(project)
        
        self._log_action(project.id, "SPECIFYING", "Specification generated",
                        f"{len(spec.requirements)} requirements, {spec.total_hours}h, ${spec.fixed_price}")
        
        # Format for client
        client_view = self.spec_generator.format_for_client(spec)
        
        self.notify(f"📋 Spec ready: {project.title}\n{len(spec.requirements)} requirements, ${spec.fixed_price}")
        
        logger.info(f"Specify OK: {project.reference} - {len(spec.requirements)} reqs, ${spec.fixed_price}")
        
        return True
    
    def approve_spec(self, project: PipelineProject, final_price: float = None):
        """
        Mark specification as approved - LOCKS THE PRICE.
        
        After this, price cannot change!
        """
        if final_price:
            project.fixed_price = final_price
        
        project.spec_approved = True
        project.stage = PipelineStage.QUOTING
        project.quoted_at = datetime.now().isoformat()
        
        self._update_project(project)
        
        self._log_action(project.id, "SPECIFYING", "Specification APPROVED",
                        f"Fixed price: ${project.fixed_price}")
        
        self.notify(f"✅ Spec approved: {project.title} - FIXED PRICE: ${project.fixed_price}")
        
        logger.info(f"Spec APPROVED: {project.reference} - ${project.fixed_price} LOCKED")
    
    # =========================================================================
    # STAGE 5: PAYMENT
    # =========================================================================
    
    def send_invoice(self, project: PipelineProject) -> Dict[str, str]:
        """
        Generate and send invoice/landing page.
        
        Returns:
            Dict with landing_url, pdf_path, payment_reference
        """
        project.stage = PipelineStage.AWAITING_PAYMENT
        project.payment_reference = project.reference
        
        result = {"reference": project.reference}
        
        # Generate landing page
        try:
            from landing_gen import generate_payment_landing
            landing_path = generate_payment_landing(
                project_name=project.title,
                amount=project.fixed_price or project.client_budget,
                currency="USD",
                reference=project.reference,
                client_name=project.client_name
            )
            result["landing_path"] = landing_path
        except Exception as e:
            logger.error(f"Landing generation failed: {e}")
        
        # Generate PDF invoice
        try:
            from invoice_gen import InvoiceGenerator
            wallet = os.getenv("MY_CRYPTO_WALLET", "")
            iban = os.getenv("BANK_IBAN", "")
            swift = os.getenv("BANK_SWIFT", "")
            bank = os.getenv("BANK_NAME", "")
            
            gen = InvoiceGenerator(wallet, iban, swift, bank)
            pdf_path = gen.create_pdf(
                project.title,
                project.fixed_price or project.client_budget,
                "USD",
                project.client_name,
                project.reference
            )
            result["pdf_path"] = pdf_path
        except Exception as e:
            logger.error(f"Invoice PDF generation failed: {e}")
        
        self._update_project(project)
        
        self._log_action(project.id, "PAYMENT", "Invoice sent", json.dumps(result))
        
        self.notify(f"💰 Invoice sent: {project.title} - ${project.fixed_price}")
        
        return result
    
    def check_payment(self, project: PipelineProject) -> bool:
        """
        Check if payment has been received.
        
        Checks:
        1. Blockchain (crypto)
        2. Stripe webhook flag
        3. Manual confirmation
        """
        if project.payment_confirmed:
            return True
        
        # Check crypto payment
        try:
            from blockchain_eye import check_crypto_payment
            
            wallet = os.getenv("MY_CRYPTO_WALLET", "")
            expected_amount = project.fixed_price or project.client_budget
            
            confirmed, tx_hash = check_crypto_payment(expected_amount, wallet)
            
            if confirmed:
                project.payment_confirmed = True
                project.payment_tx_hash = tx_hash or ""
                project.payment_method = "crypto"
                project.paid_at = datetime.now().isoformat()
                project.stage = PipelineStage.PAID
                
                self._update_project(project)
                
                self._log_action(project.id, "PAYMENT", "Crypto payment confirmed",
                               f"TX: {tx_hash}")
                
                self.notify(f"💰 PAYMENT RECEIVED: {project.title} - ${expected_amount} (crypto)")
                
                logger.info(f"Payment CONFIRMED: {project.reference} - {tx_hash}")
                
                return True
        except Exception as e:
            logger.debug(f"Crypto check failed: {e}")
        
        return False
    
    def confirm_payment_manual(self, project: PipelineProject, 
                                method: str = "manual",
                                tx_ref: str = ""):
        """Manually confirm payment"""
        project.payment_confirmed = True
        project.payment_method = method
        project.payment_tx_hash = tx_ref
        project.paid_at = datetime.now().isoformat()
        project.stage = PipelineStage.PAID
        
        self._update_project(project)
        
        self._log_action(project.id, "PAYMENT", f"Payment confirmed ({method})", tx_ref)
        
        self.notify(f"💰 Payment confirmed: {project.title} ({method})")
    
    # =========================================================================
    # STAGE 6: EXECUTION
    # =========================================================================
    
    def execute(self, project: PipelineProject) -> bool:
        """
        Execute the project - generate code with self-healing.
        
        Returns:
            True if execution successful
        """
        if not project.payment_confirmed:
            logger.warning(f"Cannot execute {project.reference} - not paid")
            return False
        
        if not self.code_generator:
            logger.error("Code generator not available")
            return False
        
        project.stage = PipelineStage.EXECUTING
        self._update_project(project)
        
        self.notify(f"🔧 Executing: {project.title}")
        
        # Generate with self-healing
        result = self.code_generator(project.description)
        
        if result.get("success"):
            project.code_generated = result.get("code", "")
            project.qa_score = result.get("final_score", 0)
            
            # Build deliverables
            project.deliverables = {
                "main.py": project.code_generated,
                "README.md": f"# {project.title}\n\n{project.description[:500]}",
                "requirements.txt": "\n".join(result.get("requirements", []))
            }
            
            project.stage = PipelineStage.QA_REVIEW
            self._update_project(project)
            
            self._log_action(project.id, "EXECUTION", "Code generated",
                           f"QA Score: {project.qa_score}, Attempts: {result.get('attempts', 1)}")
            
            self.notify(f"✅ Code generated: {project.title} - QA {project.qa_score}/100")
            
            return True
        else:
            self._log_action(project.id, "EXECUTION", "Failed", result.get("error", ""))
            self.notify(f"❌ Execution failed: {project.title} - {result.get('error', '')[:100]}")
            return False
    
    # =========================================================================
    # STAGE 7: DELIVERY
    # =========================================================================
    
    def deliver(self, project: PipelineProject) -> bool:
        """
        Deliver project to client.
        
        Only proceeds if payment confirmed.
        Generates IP Transfer Agreement automatically.
        """
        if not project.payment_confirmed:
            logger.warning(f"Cannot deliver {project.reference} - not paid")
            self.notify(f"⚠️ Delivery blocked: {project.title} - awaiting payment")
            return False
        
        project.stage = PipelineStage.DELIVERED
        project.delivered_at = datetime.now().isoformat()
        
        # Generate IP Transfer Agreement
        legal_path = None
        try:
            from legal_gen import generate_ip_transfer, generate_completion_certificate
            
            legal_path = generate_ip_transfer(
                client_name=project.client_name,
                project_name=project.title,
                reference=project.reference,
                amount=project.fixed_price or project.client_budget,
                payment_date=project.paid_at[:10] if project.paid_at else datetime.now().strftime("%Y-%m-%d"),
                payment_method=project.payment_method or "Bank Transfer",
                tx_hash=project.payment_tx_hash
            )
            
            project.deliverables["IP_Transfer_Agreement.pdf"] = legal_path
            
            # Also generate completion certificate
            cert_path = generate_completion_certificate(
                client_name=project.client_name,
                project_name=project.title,
                reference=project.reference
            )
            project.deliverables["Completion_Certificate.pdf"] = cert_path
            
            logger.info(f"Legal documents generated for {project.reference}")
            
        except Exception as e:
            logger.error(f"Legal doc generation failed: {e}")
        
        self._update_project(project)
        
        self._log_action(project.id, "DELIVERY", "Project delivered with legal docs",
                        f"Files: {list(project.deliverables.keys())}")
        
        self.notify(f"📦 DELIVERED: {project.title} to {project.client_name}\n"
                   f"📄 IP Transfer Agreement generated")
        
        logger.info(f"Delivered: {project.reference}")
        
        return True
    
    def close(self, project: PipelineProject):
        """Close and archive project"""
        project.stage = PipelineStage.CLOSED
        project.closed_at = datetime.now().isoformat()
        
        self._update_project(project)
        
        # Record profit
        try:
            from database import NexusDB
            db = NexusDB()
            
            db.add_project(
                title=project.title,
                budget=project.fixed_price or project.client_budget,
                currency="USD",
                description=project.description[:500],
                client=project.client_name,
                platform=project.platform
            )
        except Exception as e:
            logger.error(f"Failed to record in main DB: {e}")
        
        self._log_action(project.id, "CLOSE", "Project closed",
                        f"Profit: ${project.estimated_profit}")
        
        self.notify(f"🏁 CLOSED: {project.title} - Profit: ${project.estimated_profit}")
        
        logger.info(f"Closed: {project.reference} - ${project.estimated_profit} profit")
    
    # =========================================================================
    # FULL PIPELINE PROCESSING
    # =========================================================================
    
    def process(self, project: PipelineProject) -> PipelineStage:
        """
        Process project through all applicable stages.
        
        Returns:
            Final stage reached
        """
        logger.info(f"Processing: {project.reference} from stage {project.stage.value}")
        
        # Stage flow
        if project.stage == PipelineStage.INTAKE:
            if not self.vet(project):
                return project.stage
            project.stage = PipelineStage.VETTING
        
        if project.stage == PipelineStage.VETTING:
            if not self.clarify(project):
                return project.stage
            project.stage = PipelineStage.CLARIFYING
        
        if project.stage in [PipelineStage.CLARIFYING, PipelineStage.SPECIFYING]:
            if not self.specify(project):
                return project.stage
            # Wait for spec approval
            return PipelineStage.QUOTING
        
        if project.stage == PipelineStage.QUOTING:
            self.send_invoice(project)
            return PipelineStage.AWAITING_PAYMENT
        
        if project.stage == PipelineStage.AWAITING_PAYMENT:
            if not self.check_payment(project):
                return project.stage
            project.stage = PipelineStage.PAID
        
        if project.stage == PipelineStage.PAID:
            if not self.execute(project):
                return project.stage
            project.stage = PipelineStage.QA_REVIEW
        
        if project.stage == PipelineStage.QA_REVIEW:
            if project.qa_score >= 70:
                project.stage = PipelineStage.READY_TO_DELIVER
        
        if project.stage == PipelineStage.READY_TO_DELIVER:
            if self.deliver(project):
                project.stage = PipelineStage.DELIVERED
        
        if project.stage == PipelineStage.DELIVERED:
            self.close(project)
            return PipelineStage.CLOSED
        
        return project.stage
    
    # =========================================================================
    # MONITORING
    # =========================================================================
    
    def start_payment_monitor(self, interval_seconds: int = 300):
        """Start background payment monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._payment_monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Payment monitor started (interval: {interval_seconds}s)")
    
    def stop_payment_monitor(self):
        """Stop payment monitoring"""
        self.running = False
        logger.info("Payment monitor stopped")
    
    def _payment_monitor_loop(self, interval: int):
        """Background loop checking for payments"""
        while self.running:
            try:
                # Get projects awaiting payment
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM pipeline_projects 
                    WHERE stage = ? AND payment_confirmed = 0
                ''', (PipelineStage.AWAITING_PAYMENT.value,))
                
                rows = cursor.fetchall()
                conn.close()
                
                for row in rows:
                    project = self._row_to_project(row)
                    if self.check_payment(project):
                        # Payment confirmed - continue processing
                        if self.auto_mode:
                            self.process(project)
                            
            except Exception as e:
                logger.error(f"Payment monitor error: {e}")
            
            time.sleep(interval)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _update_project(self, project: PipelineProject):
        """Update project in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pipeline_projects SET
                stage = ?, estimated_margin = ?, estimated_profit = ?,
                suggested_price = ?, fixed_price = ?, payment_confirmed = ?,
                qa_score = ?, rejected = ?, rejection_reason = ?, updated_at = ?
            WHERE id = ?
        ''', (
            project.stage.value, project.estimated_margin, project.estimated_profit,
            project.suggested_price, project.fixed_price, 1 if project.payment_confirmed else 0,
            project.qa_score, 1 if project.rejected else 0, project.rejection_reason,
            datetime.now().isoformat(), project.id
        ))
        
        conn.commit()
        conn.close()
    
    def _row_to_project(self, row) -> PipelineProject:
        """Convert DB row to PipelineProject"""
        return PipelineProject(
            id=row[0],
            reference=row[1],
            title=row[2],
            description=row[3],
            client_name=row[4],
            client_budget=row[5],
            platform=row[6],
            stage=PipelineStage(row[7]) if row[7] else PipelineStage.INTAKE,
            estimated_margin=row[8] or 0,
            estimated_profit=row[9] or 0,
            suggested_price=row[10],
            fixed_price=row[11],
            payment_confirmed=bool(row[12]),
            qa_score=row[13] or 0,
            rejected=bool(row[14]),
            rejection_reason=row[15] or ""
        )
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT stage, COUNT(*) FROM pipeline_projects GROUP BY stage")
        by_stage = dict(cursor.fetchall())
        
        cursor.execute("SELECT SUM(estimated_profit) FROM pipeline_projects WHERE stage = 'closed'")
        total_profit = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM pipeline_projects WHERE rejected = 1")
        rejected = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "by_stage": by_stage,
            "total_profit": total_profit,
            "rejected_count": rejected,
            "monitor_running": self.running
        }


# =============================================================================
# SINGLETON
# =============================================================================

_pipeline_instance: Optional[ProfitPipeline] = None

def get_pipeline() -> ProfitPipeline:
    """Get or create pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ProfitPipeline()
    return _pipeline_instance


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  PROFIT PIPELINE v1.0 - Test")
    print("=" * 60)
    
    pipeline = ProfitPipeline(auto_mode=False)
    
    # Test intake
    project = pipeline.intake(
        title="Test Telegram Bot",
        description="Create a bot that monitors prices and sends alerts",
        client_budget=200,
        client_name="Test Client",
        platform="direct"
    )
    
    print(f"\nIntake: {project.reference}")
    
    # Test vetting
    print("\n[Vetting...]")
    result = pipeline.vet(project)
    print(f"Verdict: {project.gatekeeper_verdict}")
    print(f"Margin: {project.estimated_margin}%")
    
    # Get status
    print("\n[Pipeline Status]")
    status = pipeline.get_pipeline_status()
    print(f"By stage: {status['by_stage']}")

