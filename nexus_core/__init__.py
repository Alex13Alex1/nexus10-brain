# -*- coding: utf-8 -*-
"""
NEXUS CORE - Unified Business Engine
=====================================
Best components from NEXUS 10 AI Agency

Modules:
- pipeline: Business flow from lead to delivery
- gatekeeper: Profitability analysis (≥20% margin)
- blockchain: Crypto payment monitoring
- invoices: PDF invoice generation
- notify: Telegram notifications
- database: Unified SQLite operations

Author: NEXUS 10 AI Agency
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "NEXUS 10 AI Agency"

# Lazy imports for performance
def get_pipeline():
    """Get ProfitPipeline instance"""
    from .pipeline import get_pipeline
    return get_pipeline()

def get_gatekeeper():
    """Get Gatekeeper instance"""
    from .gatekeeper import Gatekeeper
    return Gatekeeper()

def get_blockchain_monitor():
    """Get BlockchainEye instance"""
    from .blockchain import BlockchainEye
    return BlockchainEye()

def get_invoice_generator():
    """Get InvoiceGenerator instance"""
    from .invoices import InvoiceGenerator
    return InvoiceGenerator()

def get_notifier():
    """Get TelegramNotifier instance"""
    from .notify import get_notifier
    return get_notifier()

def get_database():
    """Get NexusDatabase instance"""
    from .database import NexusDatabase
    return NexusDatabase()


# Quick status check
def status():
    """Check all components status"""
    components = {
        "pipeline": False,
        "gatekeeper": False,
        "blockchain": False,
        "invoices": False,
        "notify": False,
        "database": False
    }
    
    try:
        from . import pipeline
        components["pipeline"] = True
    except: pass
    
    try:
        from . import gatekeeper
        components["gatekeeper"] = True
    except: pass
    
    try:
        from . import blockchain
        components["blockchain"] = True
    except: pass
    
    try:
        from . import invoices
        components["invoices"] = True
    except: pass
    
    try:
        from . import notify
        components["notify"] = True
    except: pass
    
    try:
        from . import database
        components["database"] = True
    except: pass
    
    return {
        "version": __version__,
        "components": components,
        "ready": all(components.values())
    }

