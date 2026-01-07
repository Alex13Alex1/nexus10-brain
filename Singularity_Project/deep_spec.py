# -*- coding: utf-8 -*-
"""
DEEP SPEC v1.0 - Atomic Requirements Generator
==============================================
Creates detailed, testable specifications using
the Atomic Requirements methodology.

Each requirement is:
- Unique ID
- Clear acceptance criteria
- Estimated hours
- Testable/verifiable

Invoice is fixed ONLY after spec approval.

Author: NEXUS 10 AI Agency
"""

import os
import json
import openai
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

openai.api_key = os.getenv("OPENAI_API_KEY", "")


class RequirementPriority(Enum):
    CRITICAL = "CRITICAL"    # Must have - blocks delivery
    HIGH = "HIGH"            # Should have - important
    MEDIUM = "MEDIUM"        # Could have - nice to have
    LOW = "LOW"              # Won't have (this release)


class RequirementStatus(Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"


@dataclass
class AtomicRequirement:
    """Single atomic requirement - smallest testable unit"""
    id: str                           # e.g., "REQ-001"
    title: str                        # Short title
    description: str                  # Detailed description
    acceptance_criteria: List[str]    # How to verify it's done
    priority: RequirementPriority
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent requirements
    status: RequirementStatus = RequirementStatus.DRAFT
    category: str = "feature"         # feature, bugfix, enhancement
    notes: str = ""


@dataclass
class ProjectSpecification:
    """Complete project specification"""
    project_id: Optional[int]
    title: str
    version: int
    created_at: str
    requirements: List[AtomicRequirement]
    total_hours: float
    fixed_price: Optional[float]
    status: str = "DRAFT"
    approved_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "version": self.version,
            "created_at": self.created_at,
            "status": self.status,
            "approved_at": self.approved_at,
            "total_hours": self.total_hours,
            "fixed_price": self.fixed_price,
            "requirements": [asdict(r) for r in self.requirements]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class DeepSpecGenerator:
    """
    Generates detailed project specifications.
    
    Process:
    1. Analyze enhanced description (after interviewer)
    2. Generate atomic requirements
    3. Estimate hours per requirement
    4. Calculate fixed price
    5. Client approves -> Price locked
    
    Usage:
        spec_gen = DeepSpecGenerator()
        spec = spec_gen.generate(
            title="Telegram Bot",
            description="...",
            budget_hint=300
        )
        
        # Show to client, get approval
        
        spec_gen.approve(spec, final_price=350)
    """
    
    def __init__(self, hourly_rate: float = 30.0):
        self.hourly_rate = hourly_rate
        self.use_ai = bool(openai.api_key)
    
    def generate(self,
                 title: str,
                 description: str,
                 budget_hint: float = None,
                 project_id: int = None) -> ProjectSpecification:
        """
        Generate complete specification from description.
        
        Args:
            title: Project title
            description: Full description (after clarifications)
            budget_hint: Client's budget for reference
            project_id: Database project ID
            
        Returns:
            ProjectSpecification with atomic requirements
        """
        if self.use_ai:
            requirements = self._generate_ai(title, description)
        else:
            requirements = self._generate_rule_based(description)
        
        # Calculate totals
        total_hours = sum(r.estimated_hours for r in requirements)
        
        # Calculate price with margin
        base_price = total_hours * self.hourly_rate
        suggested_price = round(base_price * 1.25 / 10) * 10  # 25% margin, round to $10
        
        # If budget hint provided, adjust if reasonable
        if budget_hint:
            if budget_hint >= base_price:
                suggested_price = budget_hint
            # Otherwise keep our calculated price
        
        return ProjectSpecification(
            project_id=project_id,
            title=title,
            version=1,
            created_at=datetime.now().isoformat(),
            requirements=requirements,
            total_hours=total_hours,
            fixed_price=suggested_price,
            status="DRAFT"
        )
    
    def _generate_ai(self, title: str, description: str) -> List[AtomicRequirement]:
        """Use AI to generate requirements"""
        prompt = f"""You are a senior software architect creating a project specification.

PROJECT: {title}

DESCRIPTION:
{description}

Create a detailed specification using ATOMIC REQUIREMENTS methodology.
Each requirement must be:
- Small enough to complete in 1-8 hours
- Testable with clear acceptance criteria
- Independent where possible

Output JSON array with this exact structure:
[
  {{
    "id": "REQ-001",
    "title": "Short title",
    "description": "Detailed description of what needs to be done",
    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
    "priority": "CRITICAL|HIGH|MEDIUM|LOW",
    "estimated_hours": 2.0,
    "dependencies": [],
    "category": "feature|setup|integration|testing"
  }}
]

Generate 5-15 requirements covering all aspects. Be specific and technical.
Output ONLY valid JSON, no other text.
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            requirements = []
            for item in data:
                req = AtomicRequirement(
                    id=item.get("id", f"REQ-{len(requirements)+1:03d}"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    acceptance_criteria=item.get("acceptance_criteria", []),
                    priority=RequirementPriority[item.get("priority", "MEDIUM").upper()],
                    estimated_hours=float(item.get("estimated_hours", 2)),
                    dependencies=item.get("dependencies", []),
                    category=item.get("category", "feature")
                )
                requirements.append(req)
            
            return requirements
            
        except Exception as e:
            print(f"[DEEP_SPEC] AI error: {e}")
            return self._generate_rule_based(description)
    
    def _generate_rule_based(self, description: str) -> List[AtomicRequirement]:
        """Generate requirements using rules (fallback)"""
        desc_lower = description.lower()
        requirements = []
        req_num = 1
        
        # Always include setup
        requirements.append(AtomicRequirement(
            id=f"REQ-{req_num:03d}",
            title="Project Setup",
            description="Initialize project structure, virtual environment, and dependencies",
            acceptance_criteria=[
                "Project folder created with standard structure",
                "requirements.txt with all dependencies",
                "README.md with setup instructions"
            ],
            priority=RequirementPriority.CRITICAL,
            estimated_hours=1.0,
            category="setup"
        ))
        req_num += 1
        
        # Detect features from keywords
        features = [
            (["api", "rest", "endpoint"], "API Development", "Create REST API endpoints", 4.0),
            (["database", "db", "store", "save"], "Database Integration", "Set up database and models", 3.0),
            (["bot", "telegram"], "Telegram Bot", "Implement Telegram bot functionality", 4.0),
            (["auth", "login", "user"], "Authentication", "Implement user authentication", 3.0),
            (["scraper", "crawl", "parse"], "Data Scraping", "Implement web scraping functionality", 5.0),
            (["ai", "gpt", "openai"], "AI Integration", "Integrate AI/LLM functionality", 4.0),
            (["payment", "stripe"], "Payment Integration", "Implement payment processing", 4.0),
            (["email", "notification"], "Notifications", "Implement email/notification system", 2.0),
        ]
        
        for keywords, title, desc, hours in features:
            if any(kw in desc_lower for kw in keywords):
                requirements.append(AtomicRequirement(
                    id=f"REQ-{req_num:03d}",
                    title=title,
                    description=desc,
                    acceptance_criteria=[
                        f"{title} implemented and functional",
                        "Unit tests passing",
                        "Documentation updated"
                    ],
                    priority=RequirementPriority.HIGH,
                    estimated_hours=hours,
                    dependencies=["REQ-001"],
                    category="feature"
                ))
                req_num += 1
        
        # Always include testing
        requirements.append(AtomicRequirement(
            id=f"REQ-{req_num:03d}",
            title="Testing & QA",
            description="Write tests and perform quality assurance",
            acceptance_criteria=[
                "All core functions have tests",
                "Tests pass in CI",
                "Code review completed"
            ],
            priority=RequirementPriority.HIGH,
            estimated_hours=2.0,
            dependencies=[r.id for r in requirements[:-1]],
            category="testing"
        ))
        req_num += 1
        
        # Documentation
        requirements.append(AtomicRequirement(
            id=f"REQ-{req_num:03d}",
            title="Documentation",
            description="Complete documentation and deployment guide",
            acceptance_criteria=[
                "README with full setup guide",
                "API documentation (if applicable)",
                "Deployment instructions"
            ],
            priority=RequirementPriority.MEDIUM,
            estimated_hours=1.5,
            category="documentation"
        ))
        
        return requirements
    
    def approve(self, spec: ProjectSpecification, final_price: float = None):
        """
        Approve specification and lock price.
        
        After this, price cannot change!
        """
        spec.status = "APPROVED"
        spec.approved_at = datetime.now().isoformat()
        
        if final_price:
            spec.fixed_price = final_price
        
        # Save to database
        self._save_to_db(spec)
        
        return spec
    
    def _save_to_db(self, spec: ProjectSpecification):
        """Save specification to database"""
        if not spec.project_id:
            return
        
        try:
            from database import NexusDB
            db = NexusDB()
            
            spec_id = db.save_specification(
                project_id=spec.project_id,
                requirements=spec.to_json(),
                fixed_price=spec.fixed_price
            )
            
            if spec.status == "APPROVED":
                db.approve_specification(spec_id, spec.fixed_price)
            
            return spec_id
        except Exception as e:
            print(f"[DEEP_SPEC] DB save error: {e}")
            return None
    
    def format_for_client(self, spec: ProjectSpecification) -> str:
        """Format specification for client review"""
        lines = [
            "",
            "=" * 60,
            f"  PROJECT SPECIFICATION",
            f"  {spec.title}",
            "=" * 60,
            "",
            f"Version: {spec.version}",
            f"Date: {spec.created_at[:10]}",
            f"Status: {spec.status}",
            "",
            "-" * 60,
            "  REQUIREMENTS BREAKDOWN",
            "-" * 60,
            ""
        ]
        
        # Group by priority
        for priority in RequirementPriority:
            reqs = [r for r in spec.requirements if r.priority == priority]
            if reqs:
                lines.append(f"[{priority.value}]")
                for req in reqs:
                    lines.append(f"  {req.id}: {req.title}")
                    lines.append(f"      Est: {req.estimated_hours}h")
                    lines.append(f"      Criteria:")
                    for ac in req.acceptance_criteria[:2]:
                        lines.append(f"        - {ac}")
                    lines.append("")
        
        lines.extend([
            "-" * 60,
            "  SUMMARY",
            "-" * 60,
            f"  Total Requirements: {len(spec.requirements)}",
            f"  Total Estimated Hours: {spec.total_hours}h",
            "",
            f"  FIXED PRICE: ${spec.fixed_price:.0f} USD",
            "",
            "  This price includes:",
            "    - All requirements listed above",
            "    - Up to 3 revision rounds",
            "    - 7-day post-delivery support",
            "    - Complete documentation",
            "",
            "-" * 60,
            "",
            "  Please review and confirm to proceed.",
            "  Price is locked upon your approval.",
            "",
            "=" * 60,
            ""
        ])
        
        return "\n".join(lines)
    
    def format_for_development(self, spec: ProjectSpecification) -> str:
        """Format specification for development team"""
        lines = [
            f"# {spec.title} - Technical Specification",
            f"Version {spec.version} | {spec.created_at[:10]}",
            "",
            "## Requirements",
            ""
        ]
        
        for req in spec.requirements:
            lines.extend([
                f"### {req.id}: {req.title}",
                f"**Priority:** {req.priority.value}",
                f"**Estimate:** {req.estimated_hours}h",
                f"**Category:** {req.category}",
                "",
                req.description,
                "",
                "**Acceptance Criteria:**"
            ])
            for ac in req.acceptance_criteria:
                lines.append(f"- [ ] {ac}")
            
            if req.dependencies:
                lines.append(f"\n**Dependencies:** {', '.join(req.dependencies)}")
            
            lines.append("")
        
        lines.extend([
            "---",
            f"**Total Hours:** {spec.total_hours}h",
            f"**Fixed Price:** ${spec.fixed_price:.0f}",
        ])
        
        return "\n".join(lines)


# === SINGLETON ===
_spec_generator = None

def get_spec_generator() -> DeepSpecGenerator:
    """Get or create DeepSpecGenerator singleton"""
    global _spec_generator
    if _spec_generator is None:
        _spec_generator = DeepSpecGenerator()
    return _spec_generator


# === QUICK FUNCTIONS ===

def create_specification(title: str, description: str, 
                         budget_hint: float = None) -> Dict:
    """Quick specification creation"""
    gen = get_spec_generator()
    spec = gen.generate(title, description, budget_hint)
    
    return {
        "title": spec.title,
        "requirements_count": len(spec.requirements),
        "total_hours": spec.total_hours,
        "suggested_price": spec.fixed_price,
        "spec_object": spec,
        "client_view": gen.format_for_client(spec)
    }


def get_minimum_price(description: str) -> float:
    """Get minimum price for a project based on spec"""
    gen = get_spec_generator()
    spec = gen.generate("Project", description)
    return spec.fixed_price


# === TEST ===
if __name__ == "__main__":
    print("=" * 60)
    print("  DEEP SPEC v1.0 - Atomic Requirements Test")
    print("=" * 60)
    
    gen = DeepSpecGenerator()
    
    # Test with sample project
    description = """
    Create a Telegram bot for my e-commerce store that:
    - Sends me notifications when new orders arrive
    - Allows me to reply to customers through Telegram
    - Shows daily sales summary at 6 PM
    - Integrates with Shopify API
    
    Should handle about 50 orders per day.
    Need basic error handling and logging.
    """
    
    print("\n[Generating specification...]")
    spec = gen.generate("E-Commerce Telegram Bot", description, budget_hint=300)
    
    print("\n[Client View]")
    print(gen.format_for_client(spec))
    
    print("\n[Development View]")
    print(gen.format_for_development(spec)[:1000] + "...")







