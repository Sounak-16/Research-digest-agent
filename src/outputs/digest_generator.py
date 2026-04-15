from typing import List, Dict
from datetime import datetime

class DigestGenerator:
    @staticmethod
    def generate(clusters: List[Dict], conflicting_claims: List[Dict], total_sources: int) -> str:
        lines = []
        lines.append(f"# Research Digest")
        lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append(f"*Sources analyzed: {total_sources}*\n")
        
        lines.append("## Key Themes\n")
        for idx, cluster in enumerate(clusters, 1):
            lines.append(f"### Theme {idx}: {cluster['theme_label']}")
            lines.append(f"{cluster['summary']}")
            lines.append(f"**Supporting sources:** {', '.join(cluster['sources'])}")
            lines.append(f"**Number of claims:** {len(cluster['claims'])}\n")
        
        lines.append("## Conflicting Insights\n")
        if conflicting_claims:
            for conf in conflicting_claims:
                lines.append(f"- **Conflict:** {conf['description']}")
                lines.append(f"  - View 1: {conf['view_1']} (Source: {conf['source_1']})")
                lines.append(f"  - View 2: {conf['view_2']} (Source: {conf['source_2']})")
                lines.append("")
        else:
            lines.append("*No major conflicts detected across sources.*\n")
        
        lines.append("## Key Takeaways\n")
        # Extract most confident unique claims across themes
        takeaways = []
        for cluster in clusters[:5]:
            best = max(cluster['claims'], key=lambda x: x['confidence'])
            takeaways.append(f"- {best['text'][:150]} (confidence: {best['confidence']})")
        lines.extend(takeaways)
        
        return "\n".join(lines)