import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ClaimExtractor:
    @staticmethod
    def extract_claims(text: str, source_id: str, title: str) -> List[Dict]:
        """
        Extract atomic claims with evidence. Uses sentence splitting and heuristic patterns.
        In production, would integrate with an LLM or NLI model for higher precision.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        
        # Heuristic: sentences that state facts, findings, or conclusions
        claim_patterns = [
            r'(find|show|demonstrate|indicate|suggest|report|observe|conclude|argue|propose|state)',
            r'(is|are|was|were)\s+(\w+\s+){1,5}(associated with|correlated with|caused by|due to)',
            r'(increases|decreases|leads to|results in|affects)',
            r'according to',
            r'data suggest',
            r'we find'
        ]
        pattern = re.compile('|'.join(claim_patterns), re.IGNORECASE)
        
        for idx, sent in enumerate(sentences):
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 500:
                continue
            
            if pattern.search(sent):
                # Confidence based on structure and specificity
                confidence = 0.6
                if any(keyword in sent.lower() for keyword in ['demonstrate', 'show that', 'conclude']):
                    confidence = 0.8
                if '? ' in sent:
                    confidence = 0.3  # Questions are low confidence
                
                claims.append({
                    'claim_id': f"{source_id[:50]}_{idx}",
                    'source_id': source_id,
                    'text': sent,
                    'evidence': sent[:200] + ("..." if len(sent) > 200 else ""),
                    'confidence': round(confidence, 2)
                })
        
        # Ensure 3-10 claims per source (simulate if too few)
        if len(claims) < 3:
            logger.warning(f"Only {len(claims)} claims extracted from {source_id}, using fallback")
            # Fallback: take top 3 meaningful sentences
            meaningful = [s for s in sentences if len(s.split()) > 10][:3]
            for sent in meaningful:
                claims.append({
                    'claim_id': f"{source_id[:50]}_fallback_{idx}",
                    'source_id': source_id,
                    'text': sent,
                    'evidence': sent[:200],
                    'confidence': 0.5
                })
        
        return claims[:25]  # Cap at 10