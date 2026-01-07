# -*- coding: utf-8 -*-
"""
INTERVIEWER v1.0 - Requirements Clarification Agent
====================================================
Generates targeted clarifying questions when project
requirements are insufficient for accurate cost estimation.

Rule: Project DOES NOT proceed until all questions answered.

Author: NEXUS 10 AI Agency
"""

import os
import json
import openai
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY", "")


@dataclass 
class ClarificationSet:
    """Set of clarifying questions"""
    project_id: Optional[int]
    questions: List[str]
    answers: Dict[str, str]
    is_complete: bool
    confidence_score: float  # 0-1, how confident we are in estimates
    missing_areas: List[str]


# Categories of information we need
REQUIREMENT_CATEGORIES = {
    "scope": {
        "name": "Scope & Features",
        "questions": [
            "What are the core features that must be included?",
            "Are there any features that are nice-to-have vs. must-have?",
            "What should the system NOT do (out of scope)?"
        ]
    },
    "technical": {
        "name": "Technical Requirements",
        "questions": [
            "What programming language/framework preference do you have?",
            "Does this need to integrate with any existing systems?",
            "Are there specific APIs or services that must be used?"
        ]
    },
    "data": {
        "name": "Data & Storage",
        "questions": [
            "What kind of data will the system handle?",
            "Do you need a database? If so, what volume of data?",
            "Are there any data privacy requirements (GDPR, etc.)?"
        ]
    },
    "users": {
        "name": "Users & Access",
        "questions": [
            "Who will use this system (single user, team, public)?",
            "Do you need user authentication/login?",
            "Are there different user roles with different permissions?"
        ]
    },
    "timeline": {
        "name": "Timeline & Delivery",
        "questions": [
            "What is your target deadline for this project?",
            "Can the project be delivered in phases?",
            "Are there any hard deadlines (events, launches)?"
        ]
    },
    "hosting": {
        "name": "Hosting & Infrastructure",
        "questions": [
            "Where should this be hosted (cloud, your servers, local)?",
            "Do you have existing infrastructure to use?",
            "What's your expected traffic/usage volume?"
        ]
    }
}


class Interviewer:
    """
    Generates and manages clarifying questions for projects.
    
    Usage:
        interviewer = Interviewer()
        questions = interviewer.analyze_and_ask(description)
        
        # Client answers...
        
        if interviewer.is_ready_to_proceed(answers):
            # Move to specification phase
    """
    
    def __init__(self, max_questions: int = 5):
        self.max_questions = max_questions
        self.use_ai = bool(openai.api_key)
    
    def analyze_requirements(self, description: str) -> Dict[str, float]:
        """
        Analyze description to determine what information is missing.
        
        Returns:
            Dict of category -> confidence score (0-1)
        """
        desc_lower = description.lower()
        scores = {}
        
        for category, data in REQUIREMENT_CATEGORIES.items():
            score = 0.0
            
            # Check for keywords indicating this category is covered
            if category == "scope":
                if any(kw in desc_lower for kw in ["feature", "function", "must", "should", "need"]):
                    score += 0.4
                if len(description) > 200:  # Longer descriptions usually have more scope info
                    score += 0.3
                if any(kw in desc_lower for kw in ["not", "don't", "exclude", "without"]):
                    score += 0.2  # Mentions exclusions
            
            elif category == "technical":
                if any(kw in desc_lower for kw in ["python", "javascript", "api", "framework", "stack"]):
                    score += 0.5
                if any(kw in desc_lower for kw in ["integrate", "connect", "use", "existing"]):
                    score += 0.3
            
            elif category == "data":
                if any(kw in desc_lower for kw in ["database", "data", "store", "save", "records"]):
                    score += 0.5
                if any(kw in desc_lower for kw in ["users", "entries", "items", "volume"]):
                    score += 0.3
            
            elif category == "users":
                if any(kw in desc_lower for kw in ["user", "login", "auth", "access", "team", "public"]):
                    score += 0.5
                if any(kw in desc_lower for kw in ["admin", "role", "permission"]):
                    score += 0.3
            
            elif category == "timeline":
                if any(kw in desc_lower for kw in ["deadline", "urgent", "asap", "week", "month", "date"]):
                    score += 0.6
                if any(kw in desc_lower for kw in ["phase", "milestone", "priority"]):
                    score += 0.3
            
            elif category == "hosting":
                if any(kw in desc_lower for kw in ["host", "deploy", "server", "cloud", "aws", "docker"]):
                    score += 0.6
                if any(kw in desc_lower for kw in ["traffic", "scale", "performance"]):
                    score += 0.3
            
            scores[category] = min(1.0, score)
        
        return scores
    
    def generate_questions_rule_based(self, 
                                       description: str,
                                       category_scores: Dict[str, float]) -> List[str]:
        """
        Generate questions based on rule-based analysis.
        
        Selects questions from categories with lowest confidence.
        """
        questions = []
        
        # Sort categories by score (lowest first)
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])
        
        for category, score in sorted_categories:
            if score < 0.5 and len(questions) < self.max_questions:
                # Get first unanswered question from this category
                cat_questions = REQUIREMENT_CATEGORIES[category]["questions"]
                questions.append(cat_questions[0])
        
        # If we still have room, add more questions from low-score categories
        for category, score in sorted_categories:
            if score < 0.7 and len(questions) < self.max_questions:
                cat_questions = REQUIREMENT_CATEGORIES[category]["questions"]
                for q in cat_questions[1:]:
                    if q not in questions and len(questions) < self.max_questions:
                        questions.append(q)
        
        return questions[:self.max_questions]
    
    def generate_questions_ai(self, description: str) -> List[str]:
        """
        Use AI to generate targeted clarifying questions.
        """
        if not self.use_ai:
            return []
        
        prompt = f"""You are a senior project manager interviewing a client about their software project.

PROJECT DESCRIPTION:
{description}

Your task: Generate exactly 3-5 clarifying questions to understand:
1. What is UNCLEAR or AMBIGUOUS in the description
2. What CRITICAL information is MISSING
3. What could cause SCOPE CREEP if not clarified now

Rules:
- Questions must be specific, not generic
- Each question should help estimate project time/cost
- Focus on technical and scope questions
- Don't ask about budget (we already know that)

Output format: Return ONLY a JSON array of strings, no other text.
Example: ["Question 1?", "Question 2?", "Question 3?"]
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON array
            if content.startswith("["):
                questions = json.loads(content)
                return questions[:self.max_questions]
            
            return []
            
        except Exception as e:
            print(f"[INTERVIEWER] AI error: {e}")
            return []
    
    def analyze_and_ask(self, description: str, 
                        use_ai: bool = True) -> ClarificationSet:
        """
        Main method: Analyze description and generate questions.
        
        Args:
            description: Client's project description
            use_ai: Whether to use AI for question generation
            
        Returns:
            ClarificationSet with questions
        """
        # Analyze what we know
        category_scores = self.analyze_requirements(description)
        
        # Calculate overall confidence
        avg_confidence = sum(category_scores.values()) / len(category_scores)
        
        # Identify missing areas
        missing = [
            REQUIREMENT_CATEGORIES[cat]["name"] 
            for cat, score in category_scores.items() 
            if score < 0.5
        ]
        
        # Generate questions
        if use_ai and self.use_ai and avg_confidence < 0.7:
            questions = self.generate_questions_ai(description)
        else:
            questions = []
        
        # Fall back to rule-based if AI didn't work
        if not questions:
            questions = self.generate_questions_rule_based(description, category_scores)
        
        # If confidence is high, we might not need questions
        if avg_confidence >= 0.8 and len(description) > 300:
            questions = questions[:2]  # Just a few confirmatory questions
        
        return ClarificationSet(
            project_id=None,
            questions=questions,
            answers={},
            is_complete=len(questions) == 0,
            confidence_score=avg_confidence,
            missing_areas=missing
        )
    
    def process_answers(self, 
                        original_description: str,
                        clarification_set: ClarificationSet,
                        answers: Dict[str, str]) -> Tuple[bool, str]:
        """
        Process client's answers and determine if we can proceed.
        
        Args:
            original_description: Original project description
            clarification_set: The questions we asked
            answers: Client's answers (question -> answer)
            
        Returns:
            (can_proceed: bool, enhanced_description: str)
        """
        clarification_set.answers = answers
        
        # Check if all questions answered
        unanswered = [q for q in clarification_set.questions if q not in answers]
        
        if unanswered:
            clarification_set.is_complete = False
            return False, original_description
        
        clarification_set.is_complete = True
        
        # Create enhanced description
        enhanced = original_description + "\n\n--- CLARIFICATIONS ---\n"
        for question, answer in answers.items():
            enhanced += f"\nQ: {question}\nA: {answer}\n"
        
        # Re-analyze confidence
        new_scores = self.analyze_requirements(enhanced)
        clarification_set.confidence_score = sum(new_scores.values()) / len(new_scores)
        
        return True, enhanced
    
    def format_questions_for_client(self, 
                                     clarification_set: ClarificationSet,
                                     project_title: str = "your project") -> str:
        """Format questions for sending to client"""
        if not clarification_set.questions:
            return "No clarifying questions needed. Requirements are clear."
        
        lines = [
            f"To provide an accurate quote for {project_title}, I need a few clarifications:",
            ""
        ]
        
        for i, question in enumerate(clarification_set.questions, 1):
            lines.append(f"{i}. {question}")
        
        lines.extend([
            "",
            "Please respond to each question so I can prepare a detailed proposal.",
            "",
            "Thank you!"
        ])
        
        return "\n".join(lines)
    
    def save_to_database(self, project_id: int, clarification_set: ClarificationSet):
        """Save clarifications to database"""
        try:
            from database import NexusDB
            db = NexusDB()
            
            for question in clarification_set.questions:
                answer = clarification_set.answers.get(question)
                q_id = db.add_clarifying_question(project_id, question)
                
                if answer:
                    db.answer_clarification(q_id, answer)
            
            return True
        except Exception as e:
            print(f"[INTERVIEWER] DB save error: {e}")
            return False


# === SINGLETON ===
_interviewer = None

def get_interviewer() -> Interviewer:
    """Get or create Interviewer singleton"""
    global _interviewer
    if _interviewer is None:
        _interviewer = Interviewer()
    return _interviewer


# === QUICK FUNCTIONS ===

def generate_questions(description: str, max_questions: int = 5) -> List[str]:
    """Quick function to generate questions"""
    interviewer = Interviewer(max_questions=max_questions)
    result = interviewer.analyze_and_ask(description)
    return result.questions


def analyze_clarity(description: str) -> Dict:
    """Analyze how clear a description is"""
    interviewer = Interviewer()
    result = interviewer.analyze_and_ask(description, use_ai=False)
    
    return {
        "confidence": result.confidence_score,
        "missing_areas": result.missing_areas,
        "questions_needed": len(result.questions),
        "ready_to_proceed": result.confidence_score >= 0.7
    }


# === TEST ===
if __name__ == "__main__":
    print("=" * 60)
    print("  INTERVIEWER v1.0 - Requirements Clarification Test")
    print("=" * 60)
    
    # Test 1: Vague description
    print("\n[TEST 1] Vague description")
    desc1 = "I need a bot"
    
    interviewer = Interviewer()
    result = interviewer.analyze_and_ask(desc1, use_ai=False)
    
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Missing areas: {result.missing_areas}")
    print("\nQuestions:")
    for q in result.questions:
        print(f"  - {q}")
    
    # Test 2: Better description
    print("\n[TEST 2] Clearer description")
    desc2 = """
    I need a Telegram bot for my e-commerce store that:
    - Notifies me when new orders come in
    - Allows me to reply to customers through Telegram
    - Shows daily sales summary
    
    Should integrate with my Shopify store via their API.
    I'm the only user. Need it within 2 weeks.
    """
    
    result = interviewer.analyze_and_ask(desc2, use_ai=False)
    
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Missing areas: {result.missing_areas}")
    print(f"Questions needed: {len(result.questions)}")
    
    # Test 3: Format for client
    print("\n[TEST 3] Format for client")
    formatted = interviewer.format_questions_for_client(result, "Telegram Bot")
    print(formatted)




