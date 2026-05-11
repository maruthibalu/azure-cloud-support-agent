import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import SupportAgent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "VM Startup Failure",
        "ticket": {
            "ticket_id": "TEST001",
            "customer_name": "Alice Johnson",
            "customer_email": "alice@example.com",
            "subject": "Azure VM cannot start",
            "message": "Our production VM is stuck in stopped state and cannot start. Boot diagnostics shows startup failure. Please help urgently."
        },
        "expected_action": "resolve_with_kb",
        "expected_category": "compute"
    },
    {
        "name": "NSG Connectivity Block",
        "ticket": {
            "ticket_id": "TEST002",
            "customer_name": "Bob Wilson",
            "customer_email": "bob@example.com",
            "subject": "Cannot access app endpoint",
            "message": "Traffic to our app subnet is blocked after NSG changes. Port 443 is not reachable from frontend subnet."
        },
        "expected_action": "escalate_to_specialist",
        "expected_category": "networking"
    },
    {
        "name": "Managed Identity Access Denied",
        "ticket": {
            "ticket_id": "TEST003",
            "customer_name": "Carol Davis",
            "customer_email": "carol@example.com",
            "subject": "Key Vault secret read denied",
            "message": "Our app using managed identity gets access denied when reading Key Vault secrets. Role assignment might be missing."
        },
        "expected_action": "resolve_with_kb",
        "expected_category": "identity"
    },
    {
        "name": "AKS CrashLoop Incident",
        "ticket": {
            "ticket_id": "TEST004",
            "customer_name": "David Lee",
            "customer_email": "david@example.com",
            "subject": "Pods in CrashLoopBackOff",
            "message": "Critical: multiple AKS pods are in CrashLoopBackOff and checkout service is failing for all users."
        },
        "expected_action": "escalate_to_specialist",
        "expected_category": "aks"
    },
    {
        "name": "Cost Spike Investigation",
        "ticket": {
            "ticket_id": "TEST005",
            "customer_name": "Emma Brown",
            "customer_email": "emma@example.com",
            "subject": "Unexpected monthly cost increase",
            "message": "Our Azure bill suddenly increased by 40%. Need help identifying top cost drivers and remediation options."
        },
        "expected_action": "resolve_with_kb",
        "expected_category": "billing"
    },
    {
        "name": "Bicep Deployment Failure",
        "ticket": {
            "ticket_id": "TEST006",
            "customer_name": "Frank Miller",
            "customer_email": "frank@example.com",
            "subject": "Pipeline deployment failed",
            "message": "Our Azure DevOps pipeline failed during Bicep deployment with template validation errors in production release."
        },
        "expected_action": "resolve_with_kb",
        "expected_category": "deployment"
    }
]


def run_test_scenario(scenario):
    """Run a single test scenario"""
    print("\n" + "="*80)
    print(f"TEST: {scenario['name']}")
    print("="*80)

    agent = SupportAgent()
    result = agent.process_raw_ticket(
        ticket_id=scenario['ticket']['ticket_id'],
        customer_name=scenario['ticket']['customer_name'],
        customer_email=scenario['ticket']['customer_email'],
        subject=scenario['ticket']['subject'],
        message=scenario['ticket']['message']
    )

    # Display results
    print(f"\nCustomer: {scenario['ticket']['customer_name']}")
    print(f"Subject: {scenario['ticket']['subject']}")
    print(f"\nAnalysis:")
    print(f"  Category: {result.get('analysis', {}).get('category')}")
    print(f"  Severity: {result.get('analysis', {}).get('severity')}")
    print(f"  Sentiment: {result.get('analysis', {}).get('sentiment')}")
    print(f"  Key Issues: {', '.join(result.get('analysis', {}).get('key_issues', []))}")

    print(f"\nKB Search:")
    kb = result.get('kb_search', {})
    print(f"  Match Found: {kb.get('match_found')}")
    print(f"  Best Score: {kb.get('relevance_score', 0)*100:.0f}%")
    if kb.get('solutions'):
        print(f"  Top Solution: {kb['solutions'][0]['title']}")

    print(f"\nRouting Decision:")
    routing = result.get('routing', {})
    print(f"  Action: {routing.get('action')}")
    print(f"  Confidence: {routing.get('confidence')*100:.0f}%")
    if routing.get('specialist_type'):
        print(f"  Specialist: {routing.get('specialist_type')}")
    print(f"  Reason: {routing.get('reason')}")

    print(f"\nRecommended Response:")
    print(f"  {result.get('recommended_action')}")

    # Verify expectations
    actual_action = routing.get('action')
    actual_category = result.get('analysis', {}).get('category')

    if actual_category == scenario.get('expected_category'):
        print(f"\n[OK] Category match: {actual_category}")
    else:
        print(f"\n[MISMATCH] Category: expected {scenario.get('expected_category')}, got {actual_category}")

    if actual_action == scenario.get('expected_action'):
        print(f"[OK] Action match: {actual_action}")
    else:
        print(f"[MISMATCH] Action: expected {scenario.get('expected_action')}, got {actual_action}")

    return result


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("CUSTOMER SUPPORT AGENT - TEST SUITE")
    print("="*80)

    results = []
    for scenario in TEST_SCENARIOS:
        result = run_test_scenario(scenario)
        results.append({
            "name": scenario['name'],
            "ticket_id": scenario['ticket']['ticket_id'],
            "result": result
        })

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test in results:
        routing = test['result'].get('routing', {})
        status = "PASS" if not test['result'].get('error') else "FAIL"
        print(f"[{status}] {test['name']}: {routing.get('action', 'ERROR')}")

    print(f"\nTotal tests: {len(results)}")


if __name__ == "__main__":
    run_all_tests()
