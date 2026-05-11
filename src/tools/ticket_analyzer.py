import json
import os

from openai import AzureOpenAI

from src.models.ticket import TicketCategory, TicketSeverity, TicketSentiment
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def analyze_ticket(ticket_id: str, customer_message: str) -> dict:
    """
    Analyze a customer support ticket and extract key information.

    Args:
        ticket_id: Unique ticket identifier
        customer_message: Customer's message text

    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing ticket {ticket_id}")

    ai_result = _analyze_with_azure_ai(ticket_id, customer_message)
    if ai_result:
        logger.info(f"AI analysis complete: category={ai_result['category']}, severity={ai_result['severity']}")
        return ai_result

    # Fallback to deterministic rules when Azure AI is not configured/available.
    category = _categorize_ticket(customer_message)
    severity = _determine_severity(customer_message, category)
    key_issues = _extract_key_issues(customer_message)
    sentiment = _analyze_sentiment(customer_message)

    result = {
        "ticket_id": ticket_id,
        "category": category.value,
        "severity": severity.value,
        "key_issues": key_issues,
        "sentiment": sentiment.value
    }

    logger.info(f"Analysis complete: category={category.value}, severity={severity.value}")
    return result


def _analyze_with_azure_ai(ticket_id: str, customer_message: str) -> dict | None:
    """Use Azure OpenAI for semantic ticket analysis when credentials are available."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    if not endpoint or not api_key or not deployment:
        return None

    categories = [c.value for c in TicketCategory]
    severities = [s.value for s in TicketSeverity]
    sentiments = [s.value for s in TicketSentiment]

    prompt = {
        "task": "Analyze Azure cloud support ticket",
        "category_allowed_values": categories,
        "severity_allowed_values": severities,
        "sentiment_allowed_values": sentiments,
        "output_schema": {
            "ticket_id": "string",
            "category": "string",
            "severity": "string",
            "key_issues": ["string"],
            "sentiment": "string"
        },
        "rules": [
            "Return strict JSON only.",
            "Use only allowed enum values.",
            "Do not include markdown or extra explanation.",
            "If uncertain, choose category='other' and severity='medium'."
        ],
        "ticket": {
            "ticket_id": ticket_id,
            "message": customer_message
        }
    }

    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        completion = client.chat.completions.create(
            model=deployment,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are an Azure cloud triage model that outputs strict JSON.",
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt),
                },
            ],
        )

        raw = completion.choices[0].message.content or ""
        parsed = json.loads(raw)

        category = str(parsed.get("category", "other")).lower()
        severity = str(parsed.get("severity", "medium")).lower()
        sentiment = str(parsed.get("sentiment", "neutral")).lower()
        key_issues = parsed.get("key_issues", [])

        if category not in categories:
            category = "other"
        if severity not in severities:
            severity = "medium"
        if sentiment not in sentiments:
            sentiment = "neutral"
        if not isinstance(key_issues, list):
            key_issues = ["unclassified_issue"]
        if not key_issues:
            key_issues = ["unclassified_issue"]

        return {
            "ticket_id": ticket_id,
            "category": category,
            "severity": severity,
            "key_issues": [str(x) for x in key_issues[:8]],
            "sentiment": sentiment,
        }
    except Exception as exc:
        logger.warning(f"Azure AI analysis failed, falling back to rules: {exc}")
        return None


def _categorize_ticket(message: str) -> TicketCategory:
    """Determine ticket category based on keywords"""
    message_lower = message.lower()

    # Keyword mapping for Azure cloud categories.
    keywords = {
        TicketCategory.COMPUTE: [
            "vm", "virtual machine", "scale set", "availability set", "compute", "instance",
            "boot", "start", "stop", "restart"
        ],
        TicketCategory.NETWORKING: [
            "vnet", "subnet", "nsg", "network security group", "load balancer", "application gateway",
            "dns", "private endpoint", "peering", "traffic"
        ],
        TicketCategory.STORAGE: [
            "storage account", "blob", "file share", "queue", "table storage", "sas token",
            "container", "immutability", "storage firewall"
        ],
        TicketCategory.IDENTITY: [
            "aad", "entra", "managed identity", "rbac", "role assignment", "permission denied",
            "access denied", "service principal", "key vault"
        ],
        TicketCategory.AKS: [
            "aks", "kubernetes", "pod", "node pool", "kubectl", "container", "image pull",
            "crashloopbackoff", "ingress", "helm"
        ],
        TicketCategory.BILLING: [
            "billing", "invoice", "payment", "cost", "budget", "charge", "refund",
            "subscription", "reservation", "savings plan"
        ],
        TicketCategory.MONITORING: [
            "azure monitor", "alert", "log analytics", "application insights", "metrics",
            "diagnostic settings", "workspace", "kql"
        ],
        TicketCategory.DEPLOYMENT: [
            "arm", "bicep", "terraform", "pipeline", "devops", "github actions",
            "deployment failed", "template", "release"
        ],
    }

    # First matching category wins.
    for category, kws in keywords.items():
        if any(kw in message_lower for kw in kws):
            return category

    return TicketCategory.OTHER


def _determine_severity(message: str, category: TicketCategory) -> TicketSeverity:
    """Determine severity based on content and category"""
    message_lower = message.lower()

    # Critical indicators
    critical_indicators = [
        "production down", "service down", "outage", "sev1", "critical",
        "all users", "cannot access", "complete failure", "loss of service",
        "data loss", "security breach"
    ]
    if any(indicator in message_lower for indicator in critical_indicators):
        return TicketSeverity.CRITICAL

    # High severity indicators
    high_indicators = [
        "error", "failed", "broken", "not working", "timeout", "degraded",
        "urgent", "asap", "blocked", "incident"
    ]
    if any(indicator in message_lower for indicator in high_indicators):
        return TicketSeverity.HIGH

    # Medium severity for common Azure operations categories.
    if category in [
        TicketCategory.COMPUTE,
        TicketCategory.NETWORKING,
        TicketCategory.STORAGE,
        TicketCategory.AKS,
        TicketCategory.BILLING,
        TicketCategory.DEPLOYMENT,
    ]:
        return TicketSeverity.MEDIUM

    return TicketSeverity.LOW


def _extract_key_issues(message: str) -> list[str]:
    """Extract key issues from the message"""
    issues = []
    message_lower = message.lower()

    # Simple keyword extraction
    issue_keywords = {
        "vm_unavailable": ["vm down", "virtual machine down", "cannot start vm", "boot diagnostics"],
        "network_connectivity": ["cannot connect", "nsg", "dns", "vnet", "peering", "port blocked"],
        "identity_rbac": ["rbac", "role assignment", "permission denied", "access denied", "managed identity"],
        "storage_access": ["blob", "storage account", "sas", "forbidden", "storage firewall"],
        "aks_workload_failure": ["aks", "pod crash", "crashloopbackoff", "node not ready", "image pull"],
        "deployment_failure": ["deployment failed", "arm template", "bicep", "terraform", "pipeline failed"],
        "cost_spike": ["cost spike", "unexpected charge", "budget alert", "invoice", "billing"]
    }

    for issue, keywords in issue_keywords.items():
        if any(kw in message_lower for kw in keywords):
            issues.append(issue)

    return issues if issues else ["unclassified_issue"]


def _analyze_sentiment(message: str) -> TicketSentiment:
    """Analyze customer sentiment from message"""
    message_lower = message.lower()

    # Negative indicators
    negative_words = ["angry", "frustrated", "upset", "terrible", "worst", "horrible", "unacceptable", "disappointed"]
    if any(word in message_lower for word in negative_words):
        return TicketSentiment.NEGATIVE

    # Positive indicators
    positive_words = ["thanks", "appreciate", "great", "excellent", "works", "resolved"]
    if any(word in message_lower for word in positive_words):
        return TicketSentiment.POSITIVE

    return TicketSentiment.NEUTRAL
