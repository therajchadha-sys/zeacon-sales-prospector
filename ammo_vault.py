from typing import List, Dict, Any
from database import get_case_studies, add_case_study

class AmmoVault:
    def __init__(self):
        pass

    def get_all_case_studies(self) -> List[Dict[str, Any]]:
        return get_case_studies()

    def add_new_proof_point(self, title: str, metric: str, focus: str, description: str):
        add_case_study(title, metric, focus, description)

    def select_best_ammo(self, domain_score: Any) -> Dict[str, Any]:
        studies = self.get_all_case_studies()
        if not studies:
            return {
                'title': 'Video Engagement Lift',
                'metric': '35% lift in duration',
                'description': 'Implementing interactive video segments across marketing funnels.'
            }
        
        # Simple selection heuristic based on scores:
        # If cart check is high but on-site video is low, focus on Shopify Mobile CRO / Tolstoy integration
        if domain_score.cart_score >= 15 and domain_score.onsite_video_score < 15:
            for s in studies:
                if 'Shopify' in s['focus'] or 'Cart' in s['focus']:
                    return s
        
        # If active video ads are high, target Attribution / ROAS optimization
        if domain_score.video_ads_score >= 20:
            for s in studies:
                if 'Attribution' in s['focus'] or 'ROAS' in s['focus']:
                    return s

        # Default to first available study
        return studies[0]
