"""
Sample grievances (Hindi + English) to sanity-test the pipeline once you have
your environment set up and models downloaded. Run:
    python tests/sample_grievances.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.orchestrator import run_pipeline

SAMPLES = [
    "There has been no water supply in our street for the last 5 days. This is very urgent, please help.",
    "मेरी गली में पिछले 5 दिनों से पानी की आपूर्ति नहीं है। यह बहुत जरूरी है, कृपया मदद करें।",
    "The streetlight near the bus stop has not been working for two weeks.",
    "सड़क पर बहुत बड़ा गड्ढा है और कल एक दुर्घटना हो गई।",
    "I want to know the process for a property tax refund.",
]

if __name__ == "__main__":
    for text in SAMPLES:
        print("=" * 80)
        print("INPUT:", text)
        result = run_pipeline(text)
        for k, v in result.items():
            print(f"  {k}: {v}")
