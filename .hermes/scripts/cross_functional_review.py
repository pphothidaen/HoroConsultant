#!/usr/bin/env python3
"""
Structured Cross-Functional Review System - KAN-279

Core implementation for the 4-phase structured review protocol:
Phase 1: Orchestrator Framing
Phase 2: Parallel Perspective Dispatch (4 Roles)
Phase 3: Synthesis & Trade-off Matrix
Phase 4: Decision & Rationale

Author: HoroConsultant Integration Team
Version: 1.0.0
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path (.hermes/scripts -> .hermes -> repo root)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Note: hermes_tools is intentionally not imported; this CLI only uses the
# standard library. If memory persistence is needed later, guard the import.

class CrossFunctionalReviewSystem:
    """Main class for structured cross-functional review system."""
    
    def __init__(self, ticket_id: str, review_dir: str = None):
        self.ticket_id = ticket_id
        self.review_dir = review_dir or f"~/.hermes/reviews"
        self.review_dir = os.path.expanduser(self.review_dir)
        
        # Ensure review directory exists
        os.makedirs(self.review_dir, exist_ok=True)
        
        # Initialize review data structure (resume from sidecar when present)
        self.review_data = {
            "ticket_id": ticket_id,
            "created_at": datetime.now().isoformat(),
            "status": "IN_PROGRESS",
            "phases": {
                "phase_1": {"status": "PENDING", "findings": ""},
                "phase_2": {"status": "PENDING", "perspectives": {}},
                "phase_3": {"status": "PENDING", "synthesis": ""},
                "phase_4": {"status": "PENDING", "decision": ""}
            },
            "roles": ["red_team", "blue_team", "worker_specialist", "research"],
            "perspectives": {}
        }
        existing = self._sidecar_path()
        if os.path.exists(existing):
            try:
                with open(existing, encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict) and loaded.get("ticket_id") == ticket_id:
                    self.review_data = loaded
            except (OSError, json.JSONDecodeError):
                pass  # Corrupt sidecar: start fresh, never crash the CLI.

    def _sidecar_path(self) -> str:
        """JSON sidecar path that persists structured review state."""
        return os.path.join(
            self.review_dir,
            f"{self.ticket_id.replace('-', '_')}-cross-functional-review.json"
        )
    
    def init_review(self, title: str, problem: str, constraints: str, criteria: str):
        """Initialize a new structured review (Phase 1)."""
        self.review_data.update({
            "title": title,
            "problem_statement": problem,
            "hard_constraints": constraints,
            "decision_criteria": criteria,
        })
        self.review_data["phases"]["phase_1"] = {
            "status": "COMPLETED",
            "findings": f"Problem: {problem}\nConstraints: {constraints}\nCriteria: {criteria}",
            "completed_at": datetime.now().isoformat()
        }
        
        # Save review data
        self._save_review_data()
        
        print(f"✅ Review initialized: {title}")
        print(f"📋 Ticket: {self.ticket_id}")
        print(f"🎯 Problem: {problem}")
        print(f"⚡ Constraints: {constraints}")
        print(f"📊 Criteria: {criteria}")
        
        return True
    
    def dispatch_prompts(self, design: str):
        """Dispatch prompts to 4 parallel review roles (Phase 2)."""
        perspectives = {}
        
        # Red Team (Adversarial)
        perspectives["red_team"] = f"Probe: {design}"
        
        # Blue Team (Resilience)  
        perspectives["blue_team"] = f"Defend: {design}"
        
        # Worker Specialist (Implementation)
        perspectives["worker_specialist"] = f"Implementability: {design}"
        
        # Research (Precedent)
        perspectives["research"] = f"Precedent: {design}"
        
        self.review_data["phases"]["phase_2"]["perspectives"] = perspectives
        self.review_data["phases"]["phase_2"]["status"] = "IN_PROGRESS"
        
        # Save review data
        self._save_review_data()
        
        print("🚀 Prompts dispatched to 4 review roles:")
        for role, prompt in perspectives.items():
            print(f"  • {role.replace('_', ' ').title()}: {prompt}")
        
        return perspectives
    
    def record_perspective(self, role: str, findings: str):
        """Record findings from a review role (Phase 2)."""
        if role not in self.review_data["roles"]:
            raise ValueError(f"Invalid role: {role}")
        
        self.review_data["perspectives"][role] = {
            "findings": findings,
            "recorded_at": datetime.now().isoformat(),
            "role": role
        }
        
        # Check if all roles have completed
        completed_roles = len(self.review_data["perspectives"])
        if completed_roles == len(self.review_data["roles"]):
            self.review_data["phases"]["phase_2"]["status"] = "COMPLETED"
        
        self._save_review_data()
        
        print(f"✅ {role.replace('_', ' ').title()} perspective recorded")
        
        return True
    
    def synthesize(self, design_options: List[str], evaluation_matrix: Dict[str, Any]):
        """Synthesize findings into architectural options (Phase 3)."""
        self.review_data["phases"]["phase_3"]["synthesis"] = {
            "design_options": design_options,
            "evaluation_matrix": evaluation_matrix,
            "synthesized_at": datetime.now().isoformat()
        }
        self.review_data["phases"]["phase_3"]["status"] = "COMPLETED"
        
        self._save_review_data()
        
        print("🧠 Synthesis completed")
        print(f"📊 Evaluated {len(design_options)} design options")
        print(f"⚖️ Trade-offs matrix prepared")
        
        return True
    
    def make_decision(self, decision: str, rationale: str, owner: str):
        """Make final decision and document rationale (Phase 4)."""
        self.review_data["phases"]["phase_4"]["decision"] = {
            "choice": decision,
            "rationale": rationale,
            "owner": owner,
            "made_at": datetime.now().isoformat()
        }
        self.review_data["phases"]["phase_4"]["status"] = "COMPLETED"
        self.review_data["status"] = "COMPLETED"
        
        self._save_review_data()
        
        print("🎯 Decision made")
        print(f"✅ Choice: {decision}")
        print(f"📝 Rationale: {rationale}")
        print(f"👤 Owner: {owner}")
        
        return True
    
    def _save_review_data(self):
        """Save review data to file (JSON sidecar + markdown rendering)."""
        stem = f"{self.ticket_id.replace('-', '_')}-cross-functional-review"

        with open(self._sidecar_path(), 'w', encoding='utf-8') as f:
            json.dump(self.review_data, f, indent=2, ensure_ascii=False)

        review_file = os.path.join(self.review_dir, f"{stem}.md")
        with open(review_file, 'w', encoding='utf-8') as f:
            f.write(self._format_review_data())
    
    def _format_review_data(self) -> str:
        """Format review data as markdown."""
        return f"""# Structured Cross-Functional Review - {self.ticket_id}

**Generated:** {self.review_data['created_at']}
**Status:** {self.review_data['status']}
**Title:** {self.review_data.get('title', 'N/A')}

## Phase 1: Orchestrator Framing
**Status:** {self.review_data['phases']['phase_1']['status']}

**Problem Statement:**
{self.review_data.get('problem_statement', 'N/A')}

**Hard Constraints:**
{self.review_data.get('hard_constraints', 'N/A')}

**Decision Criteria:**
{self.review_data.get('decision_criteria', 'N/A')}

**Phase 1 Findings:**
{self.review_data['phases']['phase_1'].get('findings', 'N/A')}

## Phase 2: Parallel Perspective Dispatch
**Status:** {self.review_data['phases']['phase_2']['status']}

**Dispatched Perspectives:**
{self._format_perspectives()}

**Recorded Findings:**
{self._format_recorded_perspectives()}

## Phase 3: Synthesis & Trade-off Matrix
**Status:** {self.review_data['phases']['phase_3']['status']}

**Synthesis:**
{self._format_synthesis()}

## Phase 4: Decision & Rationale
**Status:** {self.review_data['phases']['phase_4']['status']}

**Decision:**
{self._format_decision()}
"""
    
    def _format_perspectives(self) -> str:
        """Format dispatched perspectives."""
        if not self.review_data["phases"]["phase_2"]["perspectives"]:
            return "No perspectives dispatched"
        
        result = ""
        for role, prompt in self.review_data["phases"]["phase_2"]["perspectives"].items():
            result += f"- **{role.replace('_', ' ').title()}**: {prompt}\n"
        return result
    
    def _format_recorded_perspectives(self) -> str:
        """Format recorded perspectives."""
        if not self.review_data["perspectives"]:
            return "No perspectives recorded yet"
        
        result = ""
        for role, data in self.review_data["perspectives"].items():
            result += f"### {role.replace('_', ' ').title()}\n"
            result += f"- **Findings**: {data['findings']}\n"
            result += f"- **Recorded**: {data['recorded_at']}\n\n"
        return result
    
    def _format_synthesis(self) -> str:
        """Format synthesis results."""
        if not self.review_data["phases"]["phase_3"]["synthesis"]:
            return "Synthesis not yet completed"
        
        synthesis = self.review_data["phases"]["phase_3"]["synthesis"]
        result = ""
        
        result += f"**Design Options:**\n"
        for i, option in enumerate(synthesis.get("design_options", []), 1):
            result += f"{i}. {option}\n"
        
        result += f"\n**Evaluation Matrix:**\n"
        result += f"```json\n{json.dumps(synthesis.get('evaluation_matrix', {}), indent=2)}\n```"
        
        result += f"\n\n**Synthesized at:** {synthesis.get('synthesized_at', 'N/A')}"
        
        return result
    
    def _format_decision(self) -> str:
        """Format decision results."""
        if not self.review_data["phases"]["phase_4"]["decision"]:
            return "Decision not yet made"
        
        decision = self.review_data["phases"]["phase_4"]["decision"]
        result = ""
        
        result += f"**Chosen Option:** {decision['choice']}\n"
        result += f"**Rationale:** {decision['rationale']}\n"
        result += f"**Owner:** {decision['owner']}\n"
        result += f"**Decision Made:** {decision['made_at']}\n"
        
        return result

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Structured Cross-Functional Review System - KAN-279"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new review")
    init_parser.add_argument("--ticket", required=True, help="Ticket ID")
    init_parser.add_argument("--title", required=True, help="Review title")
    init_parser.add_argument("--problem", required=True, help="Problem statement")
    init_parser.add_argument("--constraints", required=True, help="Hard constraints")
    init_parser.add_argument("--criteria", required=True, help="Decision criteria")
    
    # Dispatch command
    dispatch_parser = subparsers.add_parser(
        "dispatch-prompts", help="Dispatch prompts to review roles"
    )
    dispatch_parser.add_argument("--ticket", required=True, help="Ticket ID")
    dispatch_parser.add_argument("--design", required=True, help="Design description")
    
    # Record perspective command
    record_parser = subparsers.add_parser(
        "record-perspective", help="Record perspective findings"
    )
    record_parser.add_argument("--file", required=True, help="Review file path")
    record_parser.add_argument("--role", required=True, 
                              choices=["red_team", "blue_team", "worker_specialist", "research"],
                              help="Review role")
    record_parser.add_argument("--findings", required=True, help="Findings from review role")
    
    # Synthesize command
    synthesize_parser = subparsers.add_parser(
        "synthesize", help="Synthesize findings into architectural options"
    )
    synthesize_parser.add_argument("--file", required=True, help="Review file path")
    synthesize_parser.add_argument("--design-options", nargs="+", 
                                 required=True, help="Design options to evaluate")
    synthesize_parser.add_argument("--evaluation-matrix", 
                                 required=True, help="Evaluation matrix JSON")
    
    # Decide command
    decide_parser = subparsers.add_parser(
        "decide", help="Make final decision and document rationale"
    )
    decide_parser.add_argument("--file", required=True, help="Review file path")
    decide_parser.add_argument("--status", required=True, 
                              choices=["APPROVED", "REJECTED", "NEEDS_REVISION"],
                              help="Decision status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    def _resolve_review(namespace) -> "CrossFunctionalReviewSystem":
        """Build (or resume) a review from --ticket/--file arguments."""
        file_path = getattr(namespace, "file", None)
        review_dir = None
        ticket = getattr(namespace, "ticket", None)
        if file_path:
            expanded = os.path.expanduser(file_path)
            review_dir = os.path.dirname(expanded) or None
            if not ticket:
                stem = os.path.basename(expanded)
                suffix = "-cross-functional-review.md"
                if stem.endswith(suffix):
                    ticket = stem[: -len(suffix)].replace("_", "-")
                else:
                    ticket = stem
        if not ticket:
            parser.error("cannot determine ticket; pass --ticket or --file")
        return CrossFunctionalReviewSystem(ticket, review_dir=review_dir)
    
    # Execute commands
    if args.command == "init":
        review = _resolve_review(args)
        review.init_review(args.title, args.problem, args.constraints, args.criteria)
        
    elif args.command == "dispatch-prompts":
        review = _resolve_review(args)
        review.dispatch_prompts(args.design)
        
    elif args.command == "record-perspective":
        review = _resolve_review(args)
        review.record_perspective(args.role, args.findings)
        
    elif args.command == "synthesize":
        review = _resolve_review(args)
        evaluation_matrix = json.loads(args.evaluation_matrix)
        review.synthesize(args.design_options, evaluation_matrix)
        
    elif args.command == "decide":
        review = _resolve_review(args)
        review.make_decision(args.status, f"Decision: {args.status}", "Orchestrator")

if __name__ == "__main__":
    main()