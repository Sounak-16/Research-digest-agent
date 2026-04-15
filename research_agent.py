"""
Research Digest Agent - Final Fixed Version
No warnings, no errors, ready for assignment
"""

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
            resp = requests.get(source, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            title = soup.title.string if soup.title else "No title"
            return text, title
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
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claims = []
    patterns = ['demonstrate', 'show', 'find', 'conclude', 'indicate', 'suggest', 'report', 'according to', 'research']
    
    for sent in sentences[:50]:
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 500:
            continue
        if any(p in sent.lower() for p in patterns):
            confidence = 0.7
            if 'demonstrate' in sent.lower() or 'conclude' in sent.lower():
                confidence = 0.85
            claims.append({
                'text': sent,
                'evidence': sent[:200],
                'confidence': confidence
            })
    return claims[:10]

def group_claims(claims):
    """Group similar claims"""
    if len(claims) < 2:
        return [{'theme': 'Main findings', 'claims': claims, 'count': len(claims)}]
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    texts = [c['text'] for c in claims]
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(texts).toarray()
    sim_matrix = cosine_similarity(embeddings)
    
    clusters = []
    visited = [False] * len(claims)
    
    for i in range(len(claims)):
        if visited[i]:
            continue
        cluster = [i]
        for j in range(i+1, len(claims)):
            if not visited[j] and sim_matrix[i][j] > 0.3:
                cluster.append(j)
                visited[j] = True
        visited[i] = True
        clusters.append([claims[idx] for idx in cluster])
    
    themes = []
    for cluster in clusters:
        all_text = ' '.join([c['text'] for c in cluster])
        words = [w for w in all_text.lower().split() if len(w) > 5]
        common = Counter(words).most_common(2)
        theme = ' / '.join([w for w, _ in common]) if common else 'Research findings'
        themes.append({
            'theme': theme,
            'claims': cluster,
            'count': len(cluster)
        })
    return themes

def get_display_name(source_path):
    """Get display name safely"""
    if '\\' in source_path or '/' in source_path:
        return Path(source_path).name
    else:
        return source_path[:50]

def main():
    print("\n" + "="*60)
    print("RESEARCH DIGEST AGENT")
    print("="*60)
    
    print("\nHow to provide sources?")
    print("1. Enter URLs (one by one)")
    print("2. Process all files from a folder")
    print("3. Enter file paths (one by one)")
    
    choice = input("\nChoose (1, 2, or 3): ").strip()
    
    sources = []
    
    if choice == '1':
        print("\nEnter URLs (type 'done' when finished):")
        while True:
            url = input("URL: ").strip()
            if url.lower() == 'done':
                break
            if url:
                sources.append(url)
                print(f"  Added: {url[:50]}...")
    
    elif choice == '2':
        folder = input("\nEnter folder path: ").strip()
        if Path(folder).exists():
            sources = glob.glob(f"{folder}/**/*.txt", recursive=True) + \
                      glob.glob(f"{folder}/**/*.html", recursive=True)
            print(f"  Found {len(sources)} files")
        else:
            print(f"  Folder not found: {folder}")
            return
    
    elif choice == '3':
        print("\nEnter file paths (type 'done' when finished):")
        while True:
            filepath = input("File: ").strip()
            if filepath.lower() == 'done':
                break
            if filepath and Path(filepath).exists():
                sources.append(filepath)
                print(f"  Added: {filepath}")
            elif filepath:
                print(f"  File not found: {filepath}")
    
    else:
        print("Invalid choice")
        return
    
    if not sources:
        print("No sources provided")
        return
    
    print(f"\nProcessing {len(sources)} sources...")
    
    all_claims = []
    source_count = 0
    
    for src in sources:
        text, title = fetch_content(src)
        if text:
            claims = extract_claims(text)
            for c in claims:
                c['source'] = src
                c['title'] = title
            all_claims.extend(claims)
            source_count += 1
            display_name = get_display_name(src)
            print(f"  [{source_count}] Processed: {display_name} ({len(claims)} claims)")
    
    if not all_claims:
        print("No claims extracted from any source")
        return
    
    themes = group_claims(all_claims)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_file = Path(OUTPUT_FOLDER) / f"analysis_{timestamp}.txt"
    
    with open(save_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"RESEARCH DIGEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"SOURCES PROCESSED: {source_count}\n")
        f.write(f"TOTAL CLAIMS: {len(all_claims)}\n")
        f.write(f"THEMES FOUND: {len(themes)}\n\n")
        
        f.write("-"*60 + "\n")
        f.write("SOURCES:\n")
        f.write("-"*60 + "\n")
        for src in sources:
            f.write(f"  - {src}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("KEY THEMES:\n")
        f.write("-"*60 + "\n")
        
        for i, theme in enumerate(themes, 1):
            f.write(f"\n{i}. {theme['theme']}\n")
            best_claim = max(theme['claims'], key=lambda x: x['confidence'])
            f.write(f"   {best_claim['text'][:150]}...\n")
            f.write(f"   Supporting claims: {len(theme['claims'])}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("ALL CLAIMS:\n")
        f.write("-"*60 + "\n")
        
        for i, claim in enumerate(all_claims, 1):
            f.write(f"\n{i}. {claim['text']}\n")
            f.write(f"   Confidence: {claim['confidence']*100:.0f}%\n")
            source_short = claim['source'][:60].replace('\\', '/')
            f.write(f"   Source: {source_short}\n")
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Sources processed: {source_count}")
    print(f"Claims extracted: {len(all_claims)}")
    print(f"Themes identified: {len(themes)}")
    
    print("\n--- SAMPLE CLAIMS ---")
    for claim in all_claims[:3]:
        print(f"\n  {claim['text'][:100]}...")
        print(f"  Confidence: {claim['confidence']*100:.0f}%")
    
    print("\n" + "="*60)
    print(f"SAVED TO: {save_file}")
    print("="*60)

if __name__ == "__main__":
    main()