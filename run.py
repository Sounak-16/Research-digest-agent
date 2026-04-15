from src.pipeline import ResearchDigestPipeline
import glob

if __name__ == "__main__":
    # Example: mix of URLs and local files
    sources = [
        "https://en.wikipedia.org/wiki/Climate_change",
        "https://www.who.int/news-room/fact-sheets/detail/climate-change-and-health",
        "./data/samples/paper1.txt",
        "./data/samples/report.html",
        "https://example.com/broken"  # Will be gracefully skipped
    ]
    
    # Or scan a folder
    # sources = glob.glob("./data/sources/*.txt") + glob.glob("./data/sources/*.html")
    
    pipeline = ResearchDigestPipeline(similarity_threshold=0.75)
    pipeline.run(sources, output_dir="./outputs")