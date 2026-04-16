import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import glob

OUTPUT_FOLDER = "my_analyses"
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

def fetch_content(source):
    """Fetch content from URL or file"""
    try:
        if source.startswith(('http://', 'https://')):
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(source, timeout=15, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:20000], soup.title.string if soup.title else "No title"
        else:
            p = Path(source)
            if p.exists():
                text = p.read_text(encoding='utf-8', errors='ignore')
                return text, p.stem
    except Exception as e:
        print(f"  Error: {e}")
    return None, None

def extract_claims(text):
    """Extract claims from text"""
    if not text:
        return []
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claims = []
    
    for sent in sentences[:80]:
        sent = sent.strip()
        if len(sent) < 40 or len(sent) > 600:
            continue
        
        # Look for research language
        research_words = ['research', 'study', 'show', 'demonstrate', 'find', 'conclude', 
                         'according to', 'report', 'indicate', 'suggest', 'result', 'data']
        
        if any(word in sent.lower() for word in research_words):
            confidence = 0.7
            if 'demonstrate' in sent.lower() or 'conclude' in sent.lower():
                confidence = 0.85
            elif 'suggest' in sent.lower():
                confidence = 0.65
            
            claims.append({
                'text': sent[:500],
                'evidence': sent[:250],
                'confidence': confidence
            })
    
    # If no research claims found, take longest sentences
    if len(claims) < 3:
        for sent in sentences[:15]:
            if 50 < len(sent) < 500:
                claims.append({
                    'text': sent[:500],
                    'evidence': sent[:250],
                    'confidence': 0.5
                })
    
    return claims[:10]

def group_claims(claims):
    """Group similar claims"""
    if len(claims) < 2:
        return [{'theme': 'Main Findings', 'claims': claims, 'count': len(claims)}]
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        texts = [c['text'] for c in claims]
        vectorizer = TfidfVectorizer(max_features=50)
        embeddings = vectorizer.fit_transform(texts).toarray()
        sim_matrix = cosine_similarity(embeddings)
        
        clusters = []
        visited = [False] * len(claims)
        
        for i in range(len(claims)):
            if visited[i]:
                continue
            cluster = [i]
            for j in range(i+1, len(claims)):
                if not visited[j] and sim_matrix[i][j] > 0.25:
                    cluster.append(j)
                    visited[j] = True
            visited[i] = True
            clusters.append([claims[idx] for idx in cluster])
        
        themes = []
        for cluster in clusters:
            all_text = ' '.join([c['text'] for c in cluster])
            words = [w for w in all_text.lower().split() if len(w) > 6]
            common = Counter(words).most_common(3)
            theme = ' / '.join([w for w, _ in common]) if common else 'Research Findings'
            themes.append({
                'theme': theme,
                'claims': cluster,
                'count': len(cluster)
            })
        return themes
    except:
        return [{'theme': 'Research Findings', 'claims': claims, 'count': len(claims)}]

def main():
    print("\n" + "="*60)
    print("RESEARCH DIGEST AGENT")
    print("="*60)
    
    # Get sources
    print("\nEnter URLs or file paths (type 'done' to finish):")
    sources = []
    while True:
        inp = input("> ").strip()
        if inp.lower() == 'done':
            break
        if inp:
            sources.append(inp)
            print(f"  Added: {inp[:60]}")
    
    if not sources:
        print("No sources provided")
        return
    
    print(f"\nProcessing {len(sources)} source(s)...")
    print("="*60)
    
    # Process each source
    all_claims = []
    success_count = 0
    
    for i, src in enumerate(sources, 1):
        print(f"\n[{i}] {src[:70]}...")
        text, title = fetch_content(src)
        
        if text:
            claims = extract_claims(text)
            for c in claims:
                c['source'] = src
                c['title'] = title
            all_claims.extend(claims)
            success_count += 1
            print(f"    Claims extracted: {len(claims)}")
        else:
            print(f"    Failed to fetch")
    
    if not all_claims:
        print("\nNo claims extracted from any source")
        return
    
    # Group claims
    print("\nGrouping similar claims...")
    themes = group_claims(all_claims)
    
    # Save analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_file = Path(OUTPUT_FOLDER) / f"analysis_{timestamp}.txt"
    
    with open(save_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"RESEARCH DIGEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"SOURCES: {len(sources)} (Successfully processed: {success_count})\n")
        f.write(f"CLAIMS EXTRACTED: {len(all_claims)}\n")
        f.write(f"THEMES IDENTIFIED: {len(themes)}\n\n")
        
        f.write("-"*60 + "\n")
        f.write("SOURCES USED:\n")
        f.write("-"*60 + "\n")
        for src in sources:
            f.write(f"  - {src}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("KEY THEMES:\n")
        f.write("-"*60 + "\n")
        
        for idx, theme in enumerate(themes, 1):
            f.write(f"\nTHEME {idx}: {theme['theme']}\n")
            best = max(theme['claims'], key=lambda x: x['confidence'])
            f.write(f"Summary: {best['text'][:200]}\n")
            f.write(f"Number of claims: {len(theme['claims'])}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("ALL CLAIMS WITH EVIDENCE:\n")
        f.write("-"*60 + "\n")
        
        for idx, claim in enumerate(all_claims, 1):
            f.write(f"\nCLAIM {idx}: {claim['text']}\n")
            f.write(f"Evidence: {claim['evidence']}\n")
            f.write(f"Confidence: {claim['confidence']*100:.0f}%\n")
            f.write(f"Source: {claim['source'][:80]}\n")
    
    # Show results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Sources processed: {success_count}/{len(sources)}")
    print(f"Claims extracted: {len(all_claims)}")
    print(f"Themes found: {len(themes)}")
    
    print("\nSample claims:")
    for claim in all_claims[:3]:
        print(f"\n  - {claim['text'][:100]}...")
        print(f"    Confidence: {claim['confidence']*100:.0f}%")
    
    print("\n" + "="*60)
    print(f"Analysis saved to: {save_file}")
    print("="*60)

if __name__ == "__main__":
    main()
