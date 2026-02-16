import json
import os

def load_attack_db(filepath="data/attack_db.json"):
    """Loads the list of banned phrases."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)

def check_exact_match(prompt, banned_phrases):
    """
    Checks if the prompt contains any banned phrases.
    Returns: (is_blocked, reason)
    """
    prompt_lower = prompt.lower().strip()
    
    for phrase in banned_phrases:
        if phrase in prompt_lower:
            return True, f"Blocked: Found banned phrase '{phrase}'"
            
    return False, "Pass"