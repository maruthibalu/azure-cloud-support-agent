"""
Example usage of the Customer Support Agent

This script demonstrates how to use the support agent to process tickets.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import SupportAgent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def process_sample_tickets():
    """Load and process sample tickets from file"""
    print("\n" + "="*80)
    print("CUSTOMER SUPPORT AGENT - EXAMPLE USAGE")
    print("="*80)

    # Load sample tickets
    try:
        with open("examples/sample_tickets.json", "r") as f:
            tickets = json.load(f)
    except FileNotFoundError:
        print("Error: sample_tickets.json not found")
        return

    # Initialize agent
    agent = SupportAgent()

    # Process each ticket
    for ticket_data in tickets:
        print(f"\n{'='*80}")
        print(f"Processing: {ticket_data['ticket_id']} - {ticket_data['subject']}")
        print("="*80)

        result = agent.process_raw_ticket(
            ticket_id=ticket_data['ticket_id'],
            customer_name=ticket_data['customer_name'],
            customer_email=ticket_data['customer_email'],
            subject=ticket_data['subject'],
            message=ticket_data['message']
        )

        # Display concise result
        print(f"\nCustomer: {ticket_data['customer_name']}")
        print(f"Email: {ticket_data['customer_email']}")

        if "error" in result:
            print(f"Error: {result['error']}")
            continue

        analysis = result.get('analysis', {})
        print(f"\nAnalysis:")
        print(f"  Category: {analysis.get('category')}")
        print(f"  Severity: {analysis.get('severity')}")
        print(f"  Sentiment: {analysis.get('sentiment')}")

        routing = result.get('routing', {})
        print(f"\nRouting Decision:")
        print(f"  Action: {routing.get('action')}")
        print(f"  Confidence: {routing.get('confidence')}")
        if routing.get('specialist_type'):
            print(f"  Route To: {routing.get('specialist_type')}")

        kb = result.get('kb_search', {})
        if kb.get('match_found') and kb.get('solutions'):
            print(f"\nKnowledge Base Solutions Found:")
            for i, solution in enumerate(kb['solutions'][:2], 1):
                print(f"  {i}. {solution['title']} (relevance: {solution['relevance_score']*100:.0f}%)")

        print(f"\nRecommendation:")
        print(f"  {result.get('recommended_action')}")


def interactive_mode():
    """Run agent in interactive mode"""
    print("\n" + "="*80)
    print("CUSTOMER SUPPORT AGENT - INTERACTIVE MODE")
    print("="*80)
    print("Enter ticket details (or 'quit' to exit):\n")

    agent = SupportAgent()

    while True:
        print("\n" + "-"*80)
        ticket_id = input("Ticket ID (or 'quit'): ").strip()
        if ticket_id.lower() == 'quit':
            break

        customer_name = input("Customer Name: ").strip()
        customer_email = input("Customer Email: ").strip()
        subject = input("Subject: ").strip()
        message = input("Message:\n> ").strip()

        result = agent.process_raw_ticket(
            ticket_id=ticket_id,
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            message=message
        )

        # Display result
        print("\n" + "="*80)
        print("RESULT")
        print("="*80)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(json.dumps(result, indent=2))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Customer Support Agent")
    parser.add_argument(
        "--mode",
        choices=["sample", "interactive"],
        default="sample",
        help="Run mode: sample (process predefined tickets) or interactive (manual input)"
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        interactive_mode()
    else:
        process_sample_tickets()


if __name__ == "__main__":
    main()
