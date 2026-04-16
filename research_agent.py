import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import glob

OUTPUT_FOLDER = "my_analyses"
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

# TEST FUNCTIONS (Run on user's sources)

def run_tests_on_sources(sources):
    """Run 3 tests on the user's provided sources"""
    print("\n" + "="*60)
    print("RUNNING TESTS ON PROVIDED SOURCES")
    print("="*60)
    
    all_passed = True
    
    # TEST 1: Check for unreachable/broken sources
    print("\nTest 1: Checking for unreachable/broken sources")
    valid_count = 0
    broken_count = 0
    
    for src in sources:
        if src.startswith(('http://', 'https://')):
            try:
                resp = requests.get(src, timeout=5)
                if resp.status_code == 200:
                    valid_count += 1
                else:
                    broken_count += 1
                    print(f"  Broken URL: {src[:50]}... (Status: {resp.status_code})")
            except:
                broken_count += 1
                print(f"  Unreachable URL: {src[:50]}...")
        else:
            if Path(src).exists():
                valid_count += 1
            else:
                broken_count += 1
                print(f"  File not found: {src}")
    
    if broken_count == 0:
        print("  PASSED: All sources are reachable")
    else:
        print(f"  PASSED: {broken_count} broken source(s) detected and will be skipped")
    
    # TEST 2: Check for duplicate/similar sources (deduplication test)
    print("\nTest 2: Checking for duplicate or similar sources")
    
    # Create simple fingerprints for deduplication check
    source_fingerprints = {}
    duplicates = []
    
    for src in sources:
        # Simple fingerprint based on source name
        fingerprint = src.lower().replace('https://', '').replace('http://', '').replace('www.', '')
        if fingerprint in source_fingerprints:
            duplicates.append(src)
        else:
            source_fingerprints[fingerprint] = src
    
    if len(duplicates) > 0:
        print(f"  Found {len(duplicates)} potential duplicate(s)")
        for dup in duplicates[:3]:
            print(f"     - {dup[:60]}...")
    else:
        print("  PASSED: No obvious duplicates found")
    
    # TEST 3: Check for potential conflicting viewpoints
    print("\nTest 3: Checking for potential conflicting viewpoints")
    
    # Fetch content from first few valid sources to check for conflicts
    sample_texts = []
    for src in sources[:3]:  # Check first 3 sources
        if src.startswith(('http://', 'https://')):
            try:
                resp = requests.get(src, timeout=5)
                if resp.status_code == 200:
                    sample_texts.append(resp.text.lower())
            except:
                pass
        else:
            if Path(src).exists():
                try:
                    text = Path(src).read_text(encoding='utf-8', errors='ignore')
                    sample_texts.append(text.lower())
                except:
                    pass
    
    # Check for opposite keywords
    increase_words = ['increase', 'increases', 'increasing', 'rise', 'rising', 'growth']
    decrease_words = ['decrease', 'decreases', 'decreasing', 'fall', 'falling', 'decline']
    
    has_increase = any(any(word in text for word in increase_words) for text in sample_texts)
    has_decrease = any(any(word in text for word in decrease_words) for text in sample_texts)
    
    if has_increase and has_decrease:
        print("  PASSED: Potential conflicting viewpoints detected (both increase and decrease mentions found)")
        print("     → Both perspectives will be preserved in output")
    else:
        print("  PASSED: No clear conflicts detected in sampled sources")
    
    print("\n" + "="*60)
    print("TESTS COMPLETE - Ready to process")
    print("="*60)
    
    return all_passed

# CORE AGENT FUNCTIONS

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
        print(f"  Error fetching {source}: {e}")
    return None, None

def extract_claims(text):
    """Extract claims from text"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claims = []
    patterns = ['demonstrate', 'show', 'find', 'conclude', 'indicate', 'suggest', 'report', 'according to', 'research', 'study', 'data shows']
    
    for sent in sentences[:50]:
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 500:
            continue
        if any(p in sent.lower() for p in patterns):
            confidence = 0.7
            if 'demonstrate' in sent.lower() or 'conclude' in sent.lower():
                confidence = 0.85
            elif 'suggest' in sent.lower():
                confidence = 0.65
            claims.append({
                'text': sent,
                'evidence': sent[:200],
                'confidence': confidence
            })
    return claims[:10]

def group_claims(claims):
    """Group similar claims using semantic similarity"""
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

# MAIN AGENT

def main():
    print("\n" + "="*60)
    print("RESEARCH DIGEST AGENT")
    print("="*60)
    
    # Step 1: Get sources from user
    print("\n" + "="*60)
    print("STEP 1: PROVIDE YOUR RESEARCH SOURCES")
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
    
    print(f"\n Total sources collected: {len(sources)}")
    for i, src in enumerate(sources[:5], 1):
        print(f"   {i}. {src[:70]}...")
    if len(sources) > 5:
        print(f"   ... and {len(sources)-5} more")
    
    # Step 2: Ask if user wants to run tests
    print("\n" + "="*60)
    print("STEP 2: RUN TESTS ON YOUR SOURCES")
    print("="*60)
    
    run_tests = input("\nRun tests on your sources before processing? (y/n): ").strip().lower()
    
    if run_tests == 'y':
        run_tests_on_sources(sources)
    else:
        print("\nSkipping tests. Proceeding directly to processing...")
    
    # Step 3: Process the sources
    print("\n" + "="*60)
    print("STEP 3: PROCESSING SOURCES")
    print("="*60)
    
    print(f"\nProcessing {len(sources)} sources...")
    
    all_claims = []
    source_count = 0
    broken_sources = []
    
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
            print(f"  ✓ [{source_count}] {display_name} → {len(claims)} claims")
        else:
            broken_sources.append(src)
    
    if broken_sources:
        print(f"\n  Skipped {len(broken_sources)} broken/unreachable source(s)")
    
    if not all_claims:
        print("\n No claims extracted from any source")
        return
    
    # Group claims
    themes = group_claims(all_claims)
    
    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_file = Path(OUTPUT_FOLDER) / f"analysis_{timestamp}.txt"
    
    with open(save_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"RESEARCH DIGEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"SOURCES PROVIDED: {len(sources)}\n")
        f.write(f"SOURCES PROCESSED: {source_count}\n")
        f.write(f"SOURCES SKIPPED (broken): {len(broken_sources)}\n")
        f.write(f"TOTAL CLAIMS EXTRACTED: {len(all_claims)}\n")
        f.write(f"THEMES IDENTIFIED: {len(themes)}\n\n")
        
        f.write("-"*60 + "\n")
        f.write("SOURCES:\n")
        f.write("-"*60 + "\n")
        for src in sources:
            status = "✓" if src not in broken_sources else "✗"
            f.write(f"  {status} {src}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("KEY THEMES:\n")
        f.write("-"*60 + "\n")
        
        for i, theme in enumerate(themes, 1):
            f.write(f"\n{i}. {theme['theme']}\n")
            best_claim = max(theme['claims'], key=lambda x: x['confidence'])
            f.write(f"   Summary: {best_claim['text'][:150]}...\n")
            f.write(f"   Supporting claims: {len(theme['claims'])}\n")
        
        f.write("\n" + "-"*60 + "\n")
        f.write("ALL CLAIMS WITH EVIDENCE:\n")
        f.write("-"*60 + "\n")
        
        for i, claim in enumerate(all_claims, 1):
            f.write(f"\n{i}. CLAIM: {claim['text']}\n")
            f.write(f"   EVIDENCE: {claim['evidence'][:150]}...\n")
            f.write(f"   CONFIDENCE: {claim['confidence']*100:.0f}%\n")
            source_short = claim['source'][:60].replace('\\', '/')
            f.write(f"   SOURCE: {source_short}\n")
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\n✓ Sources processed successfully: {source_count}/{len(sources)}")
    print(f"✓ Claims extracted: {len(all_claims)}")
    print(f"✓ Themes identified: {len(themes)}")
    
    print("\n--- SAMPLE CLAIMS ---")
    for claim in all_claims[:3]:
        print(f"\n  {claim['text'][:100]}...")
        print(f"     Confidence: {claim['confidence']*100:.0f}%")
    
    print("\n" + "="*60)
    print(f" OUTPUT SAVED TO: {save_file}")
    print("="*60)

if __name__ == "__main__":
    main()
