# -*- coding: utf-8 -*-
# ============================================================
# SINGULARITY CORE v5.5 - FULL LOOP SYSTEM
# 6 Agents | Hunter + Negotiator + Closer | Lead Generation
# Critic Validation | Wise Watcher | Agile Liberation
# ============================================================

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# === COMPANY IDENTITY ===
COMPANY_NAME = "Agile Liberation"
COMPANY_TAGLINE = "AI-Powered Automation Solutions"
SENDER_NAME = "Agile Liberation Team"

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    try:
sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("SINGULARITY v5.4 - HUNTER SWARM")
print("=" * 50)

# === PATHS ===
DATA_DIR = os.path.join(os.getcwd(), 'data_sync')
os.makedirs(DATA_DIR, exist_ok=True)
DATA_SYNC_DIR = DATA_DIR
print(f"[OK] Data: {DATA_DIR}")

# === API ===
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
openai_error_message = None

if not OPENAI_API_KEY:
    openai_error_message = "NO API KEY"
    print("[ERROR] No API key")
else:
    print(f"[OK] API: {OPENAI_API_KEY[:8]}...")

# === LLM ===
llm = None
if OPENAI_API_KEY:
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.3)
        print("[OK] LLM ready")
    except Exception as e:
        openai_error_message = str(e)[:100]
        print(f"[ERROR] LLM: {e}")

# === TOOLS ===
search_tool = None
try:
    from crewai.tools import BaseTool
    
    class SearchTool(BaseTool):
        name: str = "search"
        description: str = "Search internet. Input: query string."
        
        def _run(self, query: str) -> str:
            print(f"[SEARCH] {query}")
            try:
                from duckduckgo_search import DDGS
                with DDGS() as d:
                    results = list(d.text(query, max_results=5))
                if results:
                    out = []
                    for r in results:
                        out.append(f"- {r.get('title','')}: {r.get('body','')[:100]} ({r.get('href','')})")
                    return "\n".join(out)
                return "No results"
            except Exception as e:
                return f"Error: {e}"
    
    search_tool = SearchTool()
    print("[OK] Search tool")
except Exception as e:
    print(f"[WARN] Search: {e}")

file_tool = None
try:
    from crewai_tools import FileReadTool
    file_tool = FileReadTool()
    print("[OK] File tool")
except:
    pass

TOOLS = [t for t in [search_tool, file_tool] if t]

# === FILES ===
def list_cloud_files() -> List[str]:
    try:
        return os.listdir(DATA_DIR)
    except:
        return []

def get_cloud_file_path(f: str) -> str:
    return os.path.join(DATA_DIR, f)

def read_file(path: str) -> str:
    try:
        ext = path.lower().split('.')[-1]
        if ext == 'csv':
            import pandas as pd
            return pd.read_csv(path).head(10).to_string()
        elif ext == 'txt':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:2000]
        elif ext == 'xlsx':
            import pandas as pd
            return pd.read_excel(path).head(10).to_string()
        elif ext == 'json':
            with open(path, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), ensure_ascii=False)[:2000]
        return "(unsupported)"
    except Exception as e:
        return f"(error: {e})"

def read_all_cloud_files_content() -> str:
    files = list_cloud_files()
    if not files:
        return ""
    parts = []
    for f in files[:3]:
        parts.append(f"=== {f} ===\n{read_file(os.path.join(DATA_DIR, f))}")
    return "\n\n".join(parts)

# ============================================================
# SYSTEM INSTRUCTIONS - LANGUAGE & TONE & PROOF OF WORK
# ============================================================

LANGUAGE_INSTRUCTIONS = """
## LANGUAGE RULES (CRITICAL):

1. **Default Language**: STRICTLY Professional English for ALL outgoing messages.
   No exceptions. No casual language. No slang.

2. **Tone of Voice**: Professional, confident, solution-oriented.
   - Focus ONLY on solving client's problem
   - Be direct and efficient
   - Show expertise without arrogance
   - Every sentence must add value
"""

PROOF_OF_WORK_POLICY = """
## PROOF OF WORK POLICY (MANDATORY):

### DEMO POLICY - NEVER SEND FULL WORK BEFORE PAYMENT:
1. **For Code Projects**: Send only a snippet (10-20 lines max), never full source
2. **For Data/Scraping**: Send partial CSV (first 5 rows only) or screenshot
3. **For Reports**: Send executive summary or table of contents only
4. **For Bots**: Send screenshot of logs or test output, not the bot itself

### DEMO EXAMPLES:
- "Here's a preview of the scraper output (first 5 rows attached)"
- "Screenshot of the bot successfully processing your test data"
- "Log excerpt showing 1000 records processed in 2.3 seconds"

### WHAT TO NEVER SEND:
- Full source code
- Complete datasets
- Working executables
- API keys or credentials
- Anything that makes payment unnecessary

### INVOICE IDENTITY:
- All invoices generated via Wise API
- Each invoice has unique Reference: SNG-XXXXXX
- Reference must be included in payment description
- Payment verified automatically by system
"""

NEGOTIATOR_INSTRUCTIONS = f"""You are the NEGOTIATOR - Expert Deal Maker for {COMPANY_NAME}.

{LANGUAGE_INSTRUCTIONS}

{PROOF_OF_WORK_POLICY}

## COMPANY IDENTITY:
- Company: {COMPANY_NAME}
- Tagline: {COMPANY_TAGLINE}
- ALL proposals must be signed as "{SENDER_NAME}"

## YOUR MISSION:
- Craft VALUE-FIRST proposals that hook clients instantly
- Offer immediate demo to prove capability
- Never promise full delivery before payment
- Generate Wise invoice reference for every deal

## THE HOOK - VALUE FIRST APPROACH:
1. State EXACTLY how you solve their problem (specific, not generic)
2. Offer FREE demo immediately (following Demo Policy)
3. Show proof of similar past work
4. Make next step crystal clear

## WORKFLOW:
1. Analyze the project - identify the REAL pain point
2. Craft the Hook - "I can [specific solution] in [timeframe]"
3. Offer Demo - "Let me show you with a quick preview"
4. Present Price with Wise Reference
5. Close with urgency

## OUTPUT FORMAT:
Structure your response as:

**FROM: {SENDER_NAME}**

**SUBJECT:** [Benefit-focused, specific to their problem]

**THE HOOK:**
"I can [exact solution] for you. Here's how..."
[2-3 sentences showing you understand their specific need]

**DEMO OFFER:**
"To prove this works, I'll send you [specific demo item] within [timeframe] - free."

**SOLUTION BREAKDOWN:**
- [Specific deliverable 1]
- [Specific deliverable 2]
- [Specific deliverable 3]

**INVESTMENT:**
$[amount] | Reference: SNG-[XXXXXX]
Timeline: [X days]
Pay to: {COMPANY_NAME} via Wise

**NEXT STEP:**
"Reply 'GO' and I'll start your demo immediately."

---
Best regards,
{SENDER_NAME}

Remember: VALUE FIRST. Show them you can solve it BEFORE discussing price.
"""

CLOSER_INSTRUCTIONS = f"""You are the CLOSER - Deal Finalizer & Secure Delivery Expert.

{LANGUAGE_INSTRUCTIONS}

{PROOF_OF_WORK_POLICY}

## YOUR MISSION:
- Deliver DEMO/PREVIEW before payment (following Demo Policy)
- Generate Wise invoice with unique reference
- Deliver FULL work ONLY after payment confirmed
- Ensure client satisfaction and repeat business

## DELIVERY STAGES:

### STAGE 1: DEMO DELIVERY (Before Payment)
Send ONLY:
- Partial output (5 rows, 20 lines, 1 page)
- Screenshots of working system
- Log excerpts proving functionality
- Performance metrics

### STAGE 2: INVOICE (After Demo Approved)
- Generate Wise Reference: SNG-XXXXXX
- Include clear payment instructions
- Set deadline for payment

### STAGE 3: FULL DELIVERY (After Payment Confirmed)
- Send complete source code
- Include all files and documentation
- Provide support instructions

## OUTPUT FORMAT - DEMO DELIVERY:

**SUBJECT:** Your [Project] Demo is Ready

**DEMO PREVIEW:**
[Describe what's attached - screenshot, partial data, log excerpt]

"As promised, here's a preview of your [deliverable]:
[Specific demo item description]"

**RESULTS ACHIEVED:**
- [Metric 1]: [Value]
- [Metric 2]: [Value]
- [Metric 3]: [Value]

**FULL DELIVERY:**
"The complete [deliverable] is ready. To receive the full package:"

**PAYMENT DETAILS:**
Amount: $[X]
Reference: SNG-[XXXXXX]
Method: Bank transfer (Wise)

**WHAT YOU'LL RECEIVE:**
- [Full item 1]
- [Full item 2]
- [Documentation]
- [X days support]

**NEXT STEP:**
"Once payment with reference SNG-[XXXXXX] is received, I'll send the complete package within 1 hour."

---
Remember: DEMO proves value. PAYMENT unlocks full delivery. No exceptions.
"""

HUNTER_INSTRUCTIONS = """You are the HUNTER - Lead Generation Expert.

## CRITICAL: ALL OUTPUT IN ENGLISH ONLY!

## YOUR MISSION:
Search the web for real freelance opportunities in:
- Python automation
- AI integration  
- Data scraping
- Web scraping
- Bot development
- API integration

## TARGET PLATFORMS:
1. Upwork - search "python automation" OR "web scraping" OR "AI"
2. Freelancer - similar searches
3. Reddit r/forhire, r/slavelabour
4. RemoteOK, We Work Remotely
5. Niche forums and job boards

## BUDGET FILTER:
- Minimum: $100
- Maximum: $500
- Sweet spot: $150-$300

## OUTPUT FORMAT (STRICT):
For each lead found, output:

---
**LEAD #[N]**

**Platform:** [Upwork/Freelancer/Reddit/etc]
**Title:** [Exact job title]
**Budget:** $[amount] or [hourly rate]
**URL:** [Direct link if available]

**Client Need:** [1-2 sentence summary]

**Quick Solve Strategy:**
[Your 2-3 sentence approach to solve this fast]

**Proposal Hook:**
[Opening line that grabs attention]

**Wise Payment Link:**
Reference: SNG-[generated]
Amount: $[suggested first milestone]
---

## SEARCH QUERIES TO USE:
- "python automation" site:upwork.com
- "web scraping project" budget
- "need bot developer" 
- "data scraping" hiring
- "AI integration" freelance

## RULES:
1. Only real, actionable leads
2. Include actual URLs when found
3. Focus on tasks YOU can solve quickly
4. Prioritize fixed-price over hourly
5. Skip vague or enterprise-level projects
"""

# === AGENTS ===
print("\n--- AGENTS ---")

researcher = None
analyst = None
critic = None
negotiator = None
closer = None
hunter = None
AGENTS = {}

if llm:
    try:
        from crewai import Agent
        
        # RESEARCHER
researcher = Agent(
            role='Researcher',
            goal='Search internet for information',
            backstory='You search the web. Use search tool. Output facts with URLs.',
            tools=[search_tool] if search_tool else [],
    llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        AGENTS['Researcher'] = 'Ready'
        print("[OK] Researcher")
        
        # ANALYST
        analyst = Agent(
            role='Analyst',
            goal='Analyze data and create forecasts',
            backstory='You analyze data. Create forecasts with HIGH/MEDIUM/LOW probability.',
            tools=[file_tool] if file_tool else [],
    llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
)
        AGENTS['Analyst'] = 'Ready'
        print("[OK] Analyst")

        # CRITIC
critic = Agent(
            role='Critic',
            goal='Verify information and check quality',
            backstory='You verify facts. Check for errors. Give final verdict.',
            tools=[search_tool] if search_tool else [],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        AGENTS['Critic'] = 'Ready'
        print("[OK] Critic")
        
        # NEGOTIATOR
        negotiator = Agent(
            role='Negotiator',
            goal='Craft compelling proposals and negotiate deals',
            backstory=NEGOTIATOR_INSTRUCTIONS,
            tools=[search_tool] if search_tool else [],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        AGENTS['Negotiator'] = 'Ready'
        print("[OK] Negotiator")
        
        # CLOSER
        closer = Agent(
            role='Closer',
            goal='Finalize deals and deliver results to clients',
            backstory=CLOSER_INSTRUCTIONS,
            tools=[file_tool] if file_tool else [],
    llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        AGENTS['Closer'] = 'Ready'
        print("[OK] Closer")
        
        # HUNTER
        hunter = Agent(
            role='Hunter',
            goal='Find real freelance opportunities on Upwork, Freelancer, and other platforms',
            backstory=HUNTER_INSTRUCTIONS,
            tools=[search_tool] if search_tool else [],
    llm=llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
        AGENTS['Hunter'] = 'Ready'
        print("[OK] Hunter")
        
        print(f"\n[OK] {len(AGENTS)} agents ready")
        
    except Exception as e:
        print(f"[ERROR] Agents: {e}")

AGENTS_LOADED = len(AGENTS) > 0

# === STATUS ===
def get_agents_status() -> Dict[str, Any]:
    return {
        "loaded": AGENTS_LOADED,
        "count": len(AGENTS),
        "agents": AGENTS,
        "cloud_files": list_cloud_files(),
        "cloud_files_count": len(list_cloud_files()),
        "cloud_path": DATA_DIR,
        "search_available": search_tool is not None,
        "file_tools_available": file_tool is not None
    }

# === ANALYSIS ===
def run_singularity_analysis(task: str, context: str = "") -> Dict[str, Any]:
    print(f"\n[ANALYSIS] {task}")
    
    if openai_error_message:
        return {"success": False, "error": openai_error_message}
    
    if not AGENTS_LOADED:
        return {"success": False, "error": "No agents"}
    
    try:
        from crewai import Task, Crew, Process
        
        files = list_cloud_files()
        data = context or read_all_cloud_files_content()
        
        t1 = Task(
            description=f"Research: {task}\n\nUse search tool. Find current info.\n{data[:1000]}",
            expected_output="Research with sources",
    agent=researcher
)

        t2 = Task(
            description=f"Analyze: {task}\n\nCreate 3 forecasts with probability.",
            expected_output="Forecasts",
            agent=analyst,
            context=[t1]
        )
        
        t3 = Task(
            description=f"Verify: {task}\n\nCheck the forecasts. Final verdict.",
            expected_output="Verification",
            agent=critic,
            context=[t2]
        )
        
        crew = Crew(
            agents=[researcher, analyst, critic],
            tasks=[t1, t2, t3],
    process=Process.sequential,
    verbose=True
)

        result = crew.kickoff()
        
        return {
            "success": True,
            "result": str(result),
            "files_used": files
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return {"success": False, "error": str(e)[:300]}

def analyze_file(path: str, query: str) -> Dict[str, Any]:
    if not os.path.isabs(path):
        path = get_cloud_file_path(os.path.basename(path))
    
    if not os.path.exists(path):
        return {"success": False, "error": "Not found"}
    
    content = read_file(path)
    
    if not analyst:
        return {"success": True, "result": content}
    
    try:
        from crewai import Task, Crew
        t = Task(
            description=f"Analyze:\n{content}\n\nQuery: {query}",
            expected_output="Analysis",
            agent=analyst
        )
        return {"success": True, "result": str(Crew(agents=[analyst], tasks=[t], verbose=True).kickoff())}
    except Exception as e:
        return {"success": False, "error": str(e)}

def quick_query(q: str) -> str:
    if not researcher:
        return "Not available"
    try:
        from crewai import Task, Crew
        t = Task(description=f"Search: {q}", expected_output="Answer", agent=researcher)
        return str(Crew(agents=[researcher], tasks=[t], verbose=True).kickoff())
    except Exception as e:
        return f"Error: {e}"

# ============================================================
# BUSINESS FUNCTIONS - NEGOTIATOR & CLOSER
# ============================================================

def generate_wise_reference() -> str:
    """Generate unique Wise payment reference"""
    try:
        from wise_engine import generate_reference
        return generate_reference()
    except:
        import uuid
        return f"SNG-{uuid.uuid4().hex[:6].upper()}"

def create_demo_preview(content: str, content_type: str = "code") -> str:
    """
    Create a safe demo preview following Proof of Work policy
    
    Args:
        content: Full content
        content_type: "code", "data", "text", "log"
    
    Returns:
        Safe preview (partial content)
    """
    lines = content.split('\n')
    
    if content_type == "code":
        # Max 20 lines for code
        preview = '\n'.join(lines[:20])
        if len(lines) > 20:
            preview += f"\n\n... [{len(lines) - 20} more lines - full code after payment] ..."
    
    elif content_type == "data":
        # Max 5 rows for CSV/data
        preview = '\n'.join(lines[:6])  # header + 5 rows
        if len(lines) > 6:
            preview += f"\n\n... [{len(lines) - 6} more rows available after payment] ..."
    
    elif content_type == "log":
        # First 15 and last 5 lines for logs
        if len(lines) > 20:
            preview = '\n'.join(lines[:15])
            preview += "\n\n... [log continues] ...\n\n"
            preview += '\n'.join(lines[-5:])
        else:
            preview = content
    
    else:
        # Generic text - first 500 chars
        preview = content[:500]
        if len(content) > 500:
            preview += f"\n\n... [{len(content) - 500} more characters after payment] ..."
    
    return preview

def create_proposal(project_description: str, budget: str = "", platform: str = "general") -> Dict[str, Any]:
    """Create a VALUE-FIRST proposal with Wise Reference using Negotiator agent"""
    
    if not negotiator:
        return {"success": False, "error": "Negotiator not available"}
    
    # Generate Wise reference for this proposal
    wise_ref = generate_wise_reference()
    
    # Always English for professional proposals
    lang_hint = "RESPOND IN PROFESSIONAL ENGLISH ONLY. No casual language."
    
    # Platform context
    platform_hint = ""
    if platform.lower() in ['upwork', 'freelancer', 'fiverr']:
        platform_hint = f"Platform: {platform}. Follow platform guidelines."
    
    try:
        from crewai import Task, Crew
        
        task = Task(
            description=f"""Create a VALUE-FIRST proposal for this project:

PROJECT DESCRIPTION:
{project_description}

BUDGET: {budget if budget else "Propose competitive rate"}
{platform_hint}

WISE PAYMENT REFERENCE: {wise_ref}

{lang_hint}

CRITICAL REQUIREMENTS:
1. Start with THE HOOK - show you understand their EXACT problem
2. Offer DEMO immediately - what preview can you send them?
3. Be SPECIFIC about deliverables (no generic promises)
4. Include the Wise Reference {wise_ref} for payment
5. End with clear NEXT STEP

Remember: VALUE FIRST. They should feel you've already started solving their problem.""",
            expected_output="Professional VALUE-FIRST proposal with demo offer and Wise reference",
            agent=negotiator
        )
        
        result = Crew(agents=[negotiator], tasks=[task], verbose=True).kickoff()
        
        return {
            "success": True,
            "result": str(result),
            "wise_reference": wise_ref,
            "language": "English"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}

def create_delivery_message(
    project_summary: str, 
    deliverables: str, 
    payment_ref: str = "",
    delivery_stage: str = "demo"  # "demo" or "full"
) -> Dict[str, Any]:
    """
    Create delivery message using Closer agent
    
    Args:
        project_summary: What was done
        deliverables: What's being delivered
        payment_ref: Existing Wise reference (or generate new)
        delivery_stage: "demo" (before payment) or "full" (after payment)
    """
    
    if not closer:
        return {"success": False, "error": "Closer not available"}
    
    # Generate or use existing Wise reference
    wise_ref = payment_ref if payment_ref else generate_wise_reference()
    
    # Always English
    lang_hint = "RESPOND IN PROFESSIONAL ENGLISH ONLY."
    
    try:
        from crewai import Task, Crew
        
        if delivery_stage == "demo":
            stage_instructions = f"""THIS IS A DEMO DELIVERY (Before Payment):

CRITICAL - Follow Proof of Work Policy:
- Send ONLY partial preview (5 rows, 20 lines, screenshot description)
- NEVER include full source code or complete data
- Show just enough to PROVE it works
- Make them WANT the full version

Include Wise Reference: {wise_ref}
Tell them: Full delivery upon payment with reference {wise_ref}
"""
        else:
            stage_instructions = f"""THIS IS A FULL DELIVERY (Payment Confirmed):

- Include ALL deliverables
- Provide complete documentation
- Offer support period
- Thank them and offer future work

Payment Reference Used: {wise_ref}
"""
        
        task = Task(
            description=f"""Create a {delivery_stage.upper()} delivery message:

PROJECT SUMMARY:
{project_summary}

DELIVERABLES:
{deliverables}

WISE PAYMENT REFERENCE: {wise_ref}

{stage_instructions}

{lang_hint}

Structure:
1. Clear subject line
2. What's being delivered (demo vs full)
3. Results/metrics achieved
4. Payment instructions (for demo) or Thank you (for full)
5. Next steps""",
            expected_output=f"Professional {delivery_stage} delivery message with Wise reference",
            agent=closer
        )
        
        result = Crew(agents=[closer], tasks=[task], verbose=True).kickoff()
        
        return {
            "success": True,
            "result": str(result),
            "wise_reference": wise_ref,
            "delivery_stage": delivery_stage,
            "language": "English"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}

def handle_objection(objection: str, context: str = "") -> Dict[str, Any]:
    """Handle client objection using Negotiator"""
    
    if not negotiator:
        return {"success": False, "error": "Negotiator not available"}
    
    is_russian = any(c in objection for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    lang_hint = "Respond in Russian." if is_russian else "Respond in English."
    
    try:
        from crewai import Task, Crew
        
        task = Task(
            description=f"""Handle this client objection professionally:

OBJECTION:
{objection}

CONTEXT:
{context if context else "General negotiation"}

{lang_hint}

Respond by:
1. Acknowledging the concern
2. Reframing the value proposition
3. Offering solution/compromise
4. Moving toward close""",
            expected_output="Professional objection handling response",
            agent=negotiator
        )
        
        result = Crew(agents=[negotiator], tasks=[task], verbose=True).kickoff()
        return {"success": True, "result": str(result)}
        
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}

# ============================================================
# HUNTER FUNCTIONS - LEAD GENERATION
# ============================================================

def hunt_leads(
    skills: str = "Python automation, AI integration, data scraping",
    budget_min: int = 100,
    budget_max: int = 500,
    num_leads: int = 3
) -> Dict[str, Any]:
    """
    Hunt for real freelance opportunities using Hunter agent
    
    Args:
        skills: Target skills/services
        budget_min: Minimum budget
        budget_max: Maximum budget
        num_leads: Number of leads to find
    
    Returns:
        {
            "success": bool,
            "leads": [...],
            "raw_result": str
        }
    """
    
    if not AGENTS.get('Hunter'):
        return {"success": False, "error": "Hunter agent not available"}
    
    print(f"\n[HUNTER] Searching for {num_leads} leads...")
    print(f"[HUNTER] Skills: {skills}")
    print(f"[HUNTER] Budget: ${budget_min} - ${budget_max}")
    
    try:
        from crewai import Task, Crew
        
        # Import Wise for payment reference generation
        try:
            from wise_engine import generate_reference
        except:
            def generate_reference():
                import uuid
                return f"SNG-{uuid.uuid4().hex[:6].upper()}"
        
        task = Task(
            description=f"""HUNT FOR FREELANCE LEADS NOW!

TARGET SKILLS: {skills}

BUDGET RANGE: ${budget_min} - ${budget_max}

REQUIRED OUTPUT: Find exactly {num_leads} real, actionable leads.

SEARCH THESE PLATFORMS (use your search tool!):
1. Search: "python automation" site:upwork.com posted today
2. Search: "web scraping project" budget ${budget_min}-${budget_max}
3. Search: "AI bot developer" freelance
4. Search: "data scraping" hiring now
5. Search: reddit forhire python

For EACH lead provide:
- Platform name
- Job title
- Budget (exact or estimated)
- URL (if found)
- Client need summary
- Quick solve strategy (how YOU would complete it fast)
- Proposal opening hook
- Suggested Wise payment reference

GENERATE PAYMENT REFERENCES:
{generate_reference()} for lead 1
{generate_reference()} for lead 2
{generate_reference()} for lead 3

OUTPUT EVERYTHING IN ENGLISH. 
SEARCH NOW. FIND REAL OPPORTUNITIES.
""",
            expected_output=f"{num_leads} detailed leads with quick solve strategies and payment references",
            agent=hunter
        )
        
        result = Crew(
            agents=[hunter],
            tasks=[task],
            verbose=True
        ).kickoff()
        
        result_str = str(result)
        
        return {
            "success": True,
            "leads_count": num_leads,
            "skills": skills,
            "budget_range": f"${budget_min}-${budget_max}",
            "result": result_str
        }
        
    except Exception as e:
        print(f"[HUNTER] Error: {e}")
        return {"success": False, "error": str(e)[:300]}

def total_hunt(num_leads: int = 5) -> Dict[str, Any]:
    """
    TOTAL HUNT - Global search across ALL platforms
    
    Searches: Upwork, Reddit, GitHub Bounties, Freelancer, RemoteOK, etc.
    Budget: $50 - $5000
    Focus: Python automation, AI agents, Web scraping, API integrations
    
    Returns 5 best opportunities with Demo packages and Wise Invoices
    """
    
    if not AGENTS.get('Hunter'):
        return {"success": False, "error": "Hunter agent not available"}
    
    print(f"\n{'='*60}")
    print("TOTAL HUNT ACTIVATED - GLOBAL SEARCH")
    print(f"{'='*60}")
    
    # Generate Wise references for each lead
    wise_refs = [generate_wise_reference() for _ in range(num_leads)]
    
    try:
        from crewai import Task, Crew
        
        task = Task(
            description=f"""TOTAL HUNT - GLOBAL SEARCH MISSION

You are hunting for the {num_leads} BEST opportunities across ALL platforms.

PLATFORMS TO SEARCH (use search tool for each):
1. Upwork - "python automation" OR "AI agent" OR "web scraping"
2. Reddit - r/forhire, r/slavelabour, r/Jobs4Bitcoins  
3. GitHub - bounties, issues with "help wanted" + "python"
4. Freelancer.com - python, automation, scraping projects
5. RemoteOK - python remote jobs
6. We Work Remotely - developer positions
7. Toptal, Gun.io - high-end projects
8. Discord servers - AI/automation communities

SEARCH QUERIES TO EXECUTE:
- "python automation" hiring budget site:upwork.com
- "web scraper" needed reddit
- "AI agent" setup freelance
- "API integration" project $500
- github bounty python "help wanted"
- "telegram bot" developer needed

BUDGET RANGE: $50 - $5000
FOCUS: Python automation, AI agents, Web scraping, API integrations

FOR EACH OF THE {num_leads} BEST LEADS, PROVIDE:

---
**LEAD #[N] - [PLATFORM]**

**Title:** [Exact job title]
**Budget:** $[amount] (or hourly rate)
**URL:** [Direct link]
**Posted:** [When - today/yesterday/this week]

**Client Problem:**
[2-3 sentences - what exactly they need solved]

**Our Solution:**
[Specific approach - how we solve it in X days]

**Demo Package (Proof of Work):**
- What we'll show: [screenshot/partial data/log excerpt]
- Delivery time: [X hours for demo]

**Wise Invoice:**
Reference: {wise_refs[0] if len(wise_refs) > 0 else 'SNG-XXXXXX'}
Amount: $[suggested price]
Milestone 1: $[first payment]

**Proposal Hook:**
"[Opening line that grabs attention and shows we understand their problem]"

---

WISE REFERENCES TO USE:
{chr(10).join([f'Lead {i+1}: {ref}' for i, ref in enumerate(wise_refs)])}

OUTPUT IN PROFESSIONAL ENGLISH ONLY.
SEARCH NOW. FIND REAL OPPORTUNITIES. BE SPECIFIC.""",
            expected_output=f"{num_leads} detailed leads with demo packages and Wise invoices",
            agent=hunter
        )
        
        # Step 1: Hunter finds leads
        hunt_result = Crew(
            agents=[hunter],
            tasks=[task],
            verbose=True
        ).kickoff()
        
        raw_leads = str(hunt_result)
        
        print("\n[CRITIC] Verifying leads...")
        
        # Step 2: Critic validates leads
        if critic:
            verify_task = Task(
                description=f"""VERIFY THESE LEADS - Quality Control Check

You are the CRITIC. Your job is to validate the leads found by Hunter.

LEADS TO VERIFY:
{raw_leads}

CHECK EACH LEAD FOR:
1. REALITY CHECK: Does this look like a real job posting? (not spam, not too good to be true)
2. BUDGET VALIDATION: Is the budget realistic for the scope?
3. CONTACT CLARITY: Is there a clear way to respond?
4. TIMING: Is this recent enough to be relevant?
5. SKILL MATCH: Does it match Python/AI/scraping expertise?

OUTPUT FORMAT:
For each lead, add a VERIFICATION STATUS:
- VERIFIED: Lead passes all checks
- WARNING: Potential issues (explain)
- REJECTED: Do not pursue (explain why)

Keep all original lead details, just add your verification verdict.
If a lead is suspicious, recommend NOT pursuing it.

CRITICAL: Only VERIFIED leads should be acted upon.""",
                expected_output="Verified leads with quality scores",
                agent=critic,
                verbose=True
            )
            
            verified_result = Crew(
                agents=[critic],
                tasks=[verify_task],
                verbose=True
            ).kickoff()
            
            result_str = str(verified_result)
            print("[CRITIC] Verification complete")
    else:
            result_str = raw_leads
            print("[WARNING] Critic not available - leads unverified")
        
        print(f"\n{'='*60}")
        print(f"TOTAL HUNT COMPLETE - {COMPANY_NAME}")
        print(f"{'='*60}")
        
        return {
            "success": True,
            "leads_count": num_leads,
            "wise_references": wise_refs,
            "platforms": "Upwork, Reddit, GitHub, Freelancer, RemoteOK, WWR",
            "budget_range": "$50-$5000",
            "verified": critic is not None,
            "company": COMPANY_NAME,
            "result": result_str
        }
        
    except Exception as e:
        print(f"[HUNT ERROR] {e}")
        return {"success": False, "error": str(e)[:300]}

def hunt_specific(query: str, platform: str = "all") -> Dict[str, Any]:
    """
    Hunt for specific type of project
    
    Args:
        query: Specific search query
        platform: Target platform (upwork, freelancer, all)
    """
    
    if not AGENTS.get('Hunter'):
        return {"success": False, "error": "Hunter agent not available"}
    
    try:
        from crewai import Task, Crew
        
        platform_hint = ""
        if platform.lower() == "upwork":
            platform_hint = "Focus ONLY on Upwork. Add site:upwork.com to searches."
        elif platform.lower() == "freelancer":
            platform_hint = "Focus ONLY on Freelancer.com"
        
        task = Task(
            description=f"""SPECIFIC HUNT REQUEST:

QUERY: {query}

{platform_hint}

Search for this specific type of project.
Find 2-3 matching opportunities.

For each opportunity provide:
1. Platform & Title
2. Budget estimate
3. How to solve it quickly
4. Proposal opening line

ALL OUTPUT IN ENGLISH.""",
            expected_output="Matching opportunities with strategies",
            agent=hunter
        )
        
        result = Crew(agents=[hunter], tasks=[task], verbose=True).kickoff()
        return {"success": True, "result": str(result)}
        
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print(f"\nStatus: {get_agents_status()}")
