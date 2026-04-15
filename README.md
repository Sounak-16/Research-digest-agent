# Research Digest Agent

## Assignment Submission for AI Engineer Role

A lightweight research analysis tool that extracts key claims from research sources (URLs or local files), identifies themes, and generates structured analysis with evidence-backed claims.

---

## Overview

This agent takes a single research source (URL or file) and produces:
- Key themes identified in the content
- Extracted claims with confidence scores
- Evidence snippets for each claim
- Saved analysis file for future reference

---

## How It Works (Step by Step)

### Step 1: Content Ingestion
- User provides a URL or local file path
- Agent fetches URL content or reads local file
- Cleans HTML/boilerplate content (removes scripts, styles, navigation)
- Extracts plain text and metadata (title, content length)

### Step 2: Claim Extraction
- Scans text for research-oriented sentences using pattern matching
- Looks for keywords like: demonstrates, shows, concludes, finds, indicates
- Extracts 3-10 atomic claims per source
- Each claim includes:
  - Claim text
  - Evidence snippet (direct quote from source)
  - Confidence score (0-1 based on language certainty)

### Step 3: Semantic Grouping
- Converts claims to embeddings using sentence-transformers
- Groups similar claims using cosine similarity (threshold 0.75)
- Identifies themes across the content
- Merges overlapping clusters

### Step 4: Analysis Generation
- Creates structured output with themes and claims
- Saves analysis to timestamped file in `my_analyses/` folder
- Displays summary on screen

### How Claims Are Grounded
Every claim is strictly grounded in source text:
- Claims are extracted from existing sentences
- Evidence is directly quoted from source
- No inference or hallucination
- Confidence score reflects linguistic certainty

---

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Internet connection (for URL fetching and model download)

### Installation

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

How to Run
Basic Usage:
python research_agent.py

Then enter your source when prompted:
Enter URL or file path: https://en.wikipedia.org/wiki/Artificial_intelligence  
Or with a local file:
Enter URL or file path: my_research.txt  


Example Run:
============================================================
RESEARCH DIGEST AGENT
============================================================

Enter URL or file path: https://en.wikipedia.org/wiki/Climate_change

Processing: https://en.wikipedia.org/wiki/Climate_change
Generating analysis...

============================================================
RESULTS
============================================================

Source: https://en.wikipedia.org/wiki/Climate_change
Claims extracted: 14
Themes found: 5

--- KEY THEMES ---

1. climate / change / temperature
   Climate change describes global warming and its effects...

2. emissions / carbon / greenhouse
   Human activities have increased CO2 levels by 50%...

--- SAMPLE CLAIMS ---

1. Global temperatures have risen 1.2°C since pre-industrial times...
   Confidence: 85%

============================================================
SAVED TO: my_analyses\analysis_20241215_153045.txt
============================================================  

Output Files
All analyses are saved to the my_analyses/ folder:
my_analyses/
├── analysis_20241215_153045.txt
├── analysis_20241215_160230.txt
└── analysis_20241216_091512.txt

Sample Output File Content
text
============================================================
ANALYSIS - 2024-12-15 15:30:45
============================================================

SOURCE: https://en.wikipedia.org/wiki/Artificial_intelligence

CLAIMS FOUND: 12
THEMES FOUND: 4

============================================================
DETAILED ANALYSIS
============================================================

--- THEME 1: artificial / intelligence / learning ---
Artificial intelligence (AI) is intelligence demonstrated by machines...

Sources: 1

--- ALL CLAIMS ---

1. Artificial intelligence was founded as an academic discipline in 1956
   Evidence: Artificial intelligence was founded as an academic discipline in 1956...
   Confidence: 85%

2. Deep learning has led to significant advances in computer vision
   Evidence: Deep learning has led to significant advances in computer vision...
   Confidence: 80%

   
Deduplication & Grouping Logic
How Similar Claims Are Grouped
Embedding Generation: Each claim is converted to a 384-dimensional vector using SentenceTransformers (all-MiniLM-L6-v2)

Similarity Calculation: Cosine similarity is calculated between all claim pairs

Clustering: Claims with similarity >= 0.75 are grouped together

Lower threshold (0.65) = broader grouping

Higher threshold (0.85) = stricter grouping

Theme Labeling: Each cluster gets a label from the most frequent keywords

Example of Deduplication
Without grouping, these would appear as separate claims:

"Climate change causes sea levels to rise"

"Sea levels are rising due to climate change"

With semantic grouping, they are identified as similar and grouped under one theme.

Preserving Conflicting Viewpoints
When conflicting claims are detected (e.g., one says "increases" and another says "decreases"), both are preserved with their source attribution.

Example from analysis:

text
--- CONFLICT DETECTED ---
Viewpoint 1 (Source: NOAA): "Climate change increases hurricane intensity"
Viewpoint 2 (Source: Alternative Study): "Climate change decreases hurricane frequency"
Both viewpoints preserved with source attribution
No information is deleted. All conflicting perspectives are explicitly shown.

Tests
Test 1: Empty/Unreachable Source Handling
# Skips 404 URLs and missing files without crashing
sources = ['https://nonexistent-site.com', 'missing.txt']


# Result: Graceful error handling, no crash
Test 2: Deduplication of Similar Claims
# Similar claims are grouped together
claim1 = "Sea levels rise 3.6mm per year"
claim2 = "Annual sea level increase is 3.6mm"


# Both placed in same theme cluster
Test 3: Preservation of Conflicting Claims
# Opposing claims are preserved
claim1 = "X increases Y"
claim2 = "X decreases Y"
# Both appear in output with source attribution
Run Tests
python -c "import pytest; pytest.main(['tests/'])" 

