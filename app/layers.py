# app/layers.py
import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.models import SessionLocal, FlaggedPrompt

# --- CONFIGURATION ---
# We use a smaller model compatible with CPUs. 
# If 'deepset/deberta-v3-base-injection' causes errors, switch to "facebook/bart-large-mnli" 
# or a generic sentiment model for demonstration.
MODEL_NAME = "protectai/deberta-v3-base-prompt-injection-v2" 

print("Loading ML Model... (This may take a minute)")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    # FORCE CPU USAGE
    device = torch.device("cpu")
    model.to(device)
except Exception as e:
    print(f"Error downloading model: {e}. Check internet connection.")

def log_attack(prompt, layer, score=1.0, blocked_content=None):
    """Saves blocked prompt/response metadata to database."""
    db = SessionLocal()
    entry = FlaggedPrompt(
        prompt=prompt,
        blocked_layer=layer,
        confidence_score=score,
        blocked_content=blocked_content,
    )
    db.add(entry)
    db.commit()
    db.close()

def load_rules():
    """Reads latest regex rules from JSON"""
    try:
        with open("data/rules.json", "r") as f:
            data = json.load(f)
            return data.get("patterns", [])
    except:
        return []

# --- LAYER 1: STATIC CHECKER ---
def static_layer(prompt):
    patterns = load_rules()
    for pattern in patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            log_attack(prompt, "Static Rule Checker", 1.0)
            return False, f"Blocked by Static Rule: '{pattern}'"
    return True, "Safe"

# --- LAYER 2: ML CLASSIFIER ---
def ml_layer(prompt):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get probability of class 1 (INJECTION)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    injection_score = probs[0][1].item() 
    
    if injection_score > 0.90:
        log_attack(prompt, "ML Classifier", injection_score)
        return False, f"Blocked by ML (Confidence: {injection_score:.2f})"
    return True, "Safe"

# --- LAYER 4: OUTPUT VALIDATOR ---
def output_layer(response_text, original_prompt):
    sensitive_words = ["password", "aws_key", "secret_token"]
    for word in sensitive_words:
        if word in response_text.lower():
            # Log user prompt separately from the sensitive model response for clarity
            log_attack(
                original_prompt,
                "Output Validator",
                1.0,
                blocked_content=response_text,
            )
            return False, "Blocked: Data Leakage Detected"
    return True, "Safe"