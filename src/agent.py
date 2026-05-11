import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.models.ticket import Ticket
from src.tools.ticket_analyzer import analyze_ticket
from src.tools.kb_searcher import search_knowledge_base
from src.tools.router import route_ticket
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


class SupportAgent:
    """Azure Foundry Customer Support Agent"""

    def __init__(self):
        """Initialize the support agent"""
        self.config = self._load_config()
        logger.info("Support Agent initialized")

    def _load_config(self) -> dict:
        """Load agent configuration"""
        try:
            with open("config/agent_config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Agent config not found")
            return {}

    def process_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Process a support ticket through the complete workflow.

        Args:
            ticket: Ticket object with customer information and message

        Returns:
            Dictionary with agent's analysis and routing decision
        """
        logger.info(f"Processing ticket: {ticket.ticket_id}")

        try:
            # Step 1: Analyze the ticket
            analysis = analyze_ticket(ticket.ticket_id, ticket.message)
            ticket.category = analysis["category"]
            ticket.severity = analysis["severity"]
            ticket.key_issues = analysis["key_issues"]
            ticket.sentiment = analysis["sentiment"]

            logger.info(f"Ticket analysis complete: {analysis}")

            # Step 2: Search knowledge base
            search_query = f"{ticket.subject} {ticket.message}"
            kb_results = search_knowledge_base(
                query=search_query,
                category=analysis["category"]
            )

            # Determine if good match found
            kb_match_found = len(kb_results["matches"]) > 0
            kb_relevance_score = (
                kb_results["matches"][0]["relevance_score"]
                if kb_match_found else 0.0
            )

            logger.info(f"KB search results: {len(kb_results['matches'])} matches, best score: {kb_relevance_score}")

            # Step 3: Route the ticket
            routing_decision = route_ticket(
                ticket_id=ticket.ticket_id,
                category=analysis["category"],
                severity=analysis["severity"],
                kb_match_found=kb_match_found,
                kb_relevance_score=kb_relevance_score
            )

            logger.info(f"Routing decision: {routing_decision}")

            # Prepare response
            response = {
                "ticket_id": ticket.ticket_id,
                "customer": {
                    "name": ticket.customer_name,
                    "email": ticket.customer_email
                },
                "analysis": {
                    "category": analysis["category"],
                    "severity": analysis["severity"],
                    "key_issues": analysis["key_issues"],
                    "sentiment": analysis["sentiment"]
                },
                "kb_search": {
                    "query": search_query[:100],  # Truncate for readability
                    "match_found": kb_match_found,
                    "relevance_score": kb_relevance_score,
                    "solutions": kb_results["matches"][:3]  # Top 3 solutions
                },
                "routing": routing_decision,
                "recommended_action": _generate_response(
                    routing_decision,
                    kb_results.get("matches", []),
                    ticket
                )
            }

            logger.info(f"Ticket processing complete: {routing_decision['action']}")
            return response

        except Exception as e:
            logger.error(f"Error processing ticket: {str(e)}", exc_info=True)
            return {
                "ticket_id": ticket.ticket_id,
                "error": str(e),
                "action": "escalate_to_specialist"
            }

    def process_raw_ticket(
        self,
        ticket_id: str,
        customer_name: str,
        customer_email: str,
        subject: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process a ticket from raw data.

        Args:
            ticket_id: Unique ticket ID
            customer_name: Customer's name
            customer_email: Customer's email
            subject: Ticket subject
            message: Ticket message

        Returns:
            Dictionary with agent's analysis and routing decision
        """
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            message=message
        )
        return self.process_ticket(ticket)


def _generate_response(routing_decision: dict, solutions: list, ticket: Ticket) -> str:
    """Generate a human-readable response based on routing decision"""
    action = routing_decision["action"]

    if action == "resolve_with_kb":
        response = f"Solution found for ticket {ticket.ticket_id}:\n"
        if solutions:
            solution = solutions[0]
            response += f"- {solution['title']}\n"
            response += f"- Steps: {len(solution.get('steps', []))} step(s)\n"
            response += f"- Relevance: {solution.get('relevance_score', 0)*100:.0f}%"
        return response

    elif action == "send_followup":
        return f"Send follow-up message to customer after KB solution for ticket {ticket.ticket_id}"

    else:  # escalate_to_specialist
        specialist = routing_decision.get("specialist_type", "support_agent")
        return f"Escalate ticket {ticket.ticket_id} to {specialist}: {routing_decision.get('reason', 'Complex issue requires specialist attention')}"


def main():
    """Demo the agent"""
    agent = SupportAgent()

    # Sample ticket
    result = agent.process_raw_ticket(
        ticket_id="TK001",
        customer_name="John Smith",
        customer_email="john@example.com",
        subject="Password reset not working",
        message="I tried to reset my password but I'm not receiving any emails. This is urgent as I need to access my account today!"
    )

    print("\n" + "="*80)
    print("TICKET PROCESSING RESULT")
    print("="*80)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
