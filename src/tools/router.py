from enum import Enum
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RoutingAction(str, Enum):
    RESOLVE_WITH_KB = "resolve_with_kb"
    ESCALATE_TO_SPECIALIST = "escalate_to_specialist"
    SEND_FOLLOWUP = "send_followup"


class SpecialistType(str, Enum):
    CLOUD_COMPUTE = "cloud_compute_engineer"
    CLOUD_NETWORK = "cloud_network_engineer"
    CLOUD_STORAGE = "cloud_storage_engineer"
    CLOUD_IDENTITY = "cloud_identity_engineer"
    CLOUD_AKS = "aks_platform_engineer"
    CLOUD_BILLING = "cloud_finops_analyst"
    CLOUD_MONITORING = "cloud_observability_engineer"
    CLOUD_DEPLOYMENT = "cloud_devops_engineer"
    GENERAL = "cloud_support_agent"


def route_ticket(
    ticket_id: str,
    category: str,
    severity: str,
    kb_match_found: bool,
    kb_relevance_score: float = 0.0
) -> dict:
    """
    Determine the routing action for a support ticket.

    Args:
        ticket_id: Unique ticket identifier
        category: Ticket category
        severity: Ticket severity
        kb_match_found: Whether KB search found matches
        kb_relevance_score: Highest relevance score (0-1)

    Returns:
        Dictionary with routing decision
    """
    logger.info(f"Routing ticket {ticket_id}: category={category}, severity={severity}")

    # Decision logic
    if severity == "critical":
        # Always escalate critical issues
        action = RoutingAction.ESCALATE_TO_SPECIALIST
        specialist = _get_specialist_for_category(category)
        reason = "Critical severity requires immediate specialist attention"
        confidence = 0.95
    elif kb_match_found and kb_relevance_score >= 0.7:
        # High confidence KB match - resolve with KB
        action = RoutingAction.RESOLVE_WITH_KB
        specialist = None
        reason = f"High relevance KB solution found (score: {kb_relevance_score})"
        confidence = 0.85
    elif kb_match_found and kb_relevance_score >= 0.5:
        # Moderate match - offer solution but prepare for escalation
        action = RoutingAction.SEND_FOLLOWUP
        specialist = _get_specialist_for_category(category)
        reason = f"Moderate KB match found but may need specialist follow-up (score: {kb_relevance_score})"
        confidence = 0.6
    elif severity == "high":
        # High severity without good KB match
        action = RoutingAction.ESCALATE_TO_SPECIALIST
        specialist = _get_specialist_for_category(category)
        reason = "High severity and no satisfactory KB solution found"
        confidence = 0.8
    else:
        # Medium/Low severity - try to resolve with KB if available
        if kb_match_found:
            action = RoutingAction.RESOLVE_WITH_KB
            specialist = None
            reason = f"KB solution available (score: {kb_relevance_score})"
            confidence = 0.75
        else:
            action = RoutingAction.ESCALATE_TO_SPECIALIST
            specialist = _get_specialist_for_category(category)
            reason = "No satisfactory KB solution, routing to specialist"
            confidence = 0.7

    result = {
        "ticket_id": ticket_id,
        "action": action.value,
        "reason": reason,
        "confidence": round(confidence, 2),
        "specialist_type": specialist.value if specialist else None
    }

    logger.info(f"Routing decision: {action.value} (confidence: {confidence})")
    return result


def _get_specialist_for_category(category: str) -> SpecialistType:
    """Get the appropriate specialist type for a category"""
    category_mapping = {
        "compute": SpecialistType.CLOUD_COMPUTE,
        "networking": SpecialistType.CLOUD_NETWORK,
        "storage": SpecialistType.CLOUD_STORAGE,
        "identity": SpecialistType.CLOUD_IDENTITY,
        "aks": SpecialistType.CLOUD_AKS,
        "billing": SpecialistType.CLOUD_BILLING,
        "monitoring": SpecialistType.CLOUD_MONITORING,
        "deployment": SpecialistType.CLOUD_DEPLOYMENT,
        "other": SpecialistType.GENERAL,
    }
    return category_mapping.get(category.lower(), SpecialistType.GENERAL)
