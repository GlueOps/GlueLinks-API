"""
Quick Links category generator.
Shared utility for generating the Quick Links category with platform links.
Used by both the main links_generator and fixtures to keep things DRY.
"""
from typing import Dict, Any, List

from app.models import CategoryModel, LinkModel


def generate_quick_links_category(captain_domain: str) -> CategoryModel:
    """
    Generate the Quick Links category with platform links.
    
    Args:
        captain_domain: The captain domain for cluster-info URL
        
    Returns:
        CategoryModel with Quick Links
    """
    return CategoryModel(
        id="quick-links",
        label="Quick Links",
        icon="🌟",
        status="ok",
        links=[
            LinkModel(
                label="ℹ️ Cluster Info",
                url=f"https://cluster-info.{captain_domain}",
            ),
            LinkModel(
                label="📚 GlueOps Docs",
                url="https://docs.glueops.dev",
            ),
            LinkModel(
                label="📞 +1-877-GLUEOPS",
                url="tel:+18774583677",
            ),
            LinkModel(
                label="📧 support@glueops.dev",
                url="mailto:support@glueops.dev",
            ),
        ],
    )


def get_quick_links_dict(captain_domain: str) -> Dict[str, Any]:
    """
    Get Quick Links category as a dictionary.
    Used by fixtures which return raw dictionaries.
    
    Args:
        captain_domain: The captain domain for cluster-info URL
        
    Returns:
        Dictionary representation of the Quick Links category
    """
    return {
        "id": "quick-links",
        "label": "Quick Links",
        "icon": "🌟",
        "status": "ok",
        "message": None,
        "links": [
            {
                "label": "Cluster Info",
                "url": f"https://cluster-info.{captain_domain}",
            },
            {
                "label": "GlueOps Documentation",
                "url": "https://docs.glueops.dev",
            },
            {
                "label": "Call GlueOps Support",
                "url": "tel:18774583677",
            },
            {
                "label": "Email GlueOps Support",
                "url": "mailto:support@glueops.dev",
            },
        ],
    }
