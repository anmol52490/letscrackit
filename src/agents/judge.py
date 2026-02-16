from google import genai
import os

def evaluate_prompt(user_prompt):
    """
    Uses the new SDK to judge if the user input is safe.
    Returns: (is_safe, explanation)
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return False, "Error: Missing API Key"

    judge_system_prompt = (
        "You are a security filter. Analyze the following user prompt. "
        "If it asks for illegal acts, hacking, or reveals PII, say 'UNSAFE'. "
        "Otherwise, say 'SAFE'. Do not explain, just one word."
    )
    
    try:
        client = genai.Client(api_key=api_key)
        full_check = f"{judge_system_prompt}\n\nUser Prompt: {user_prompt}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_check
        )
        
        result = response.text.strip().upper()
        
        if "UNSAFE" in result:
            return False, "Judge marked this as unsafe."
        return True, "Judge marked this as safe."
        
    except Exception as e:
        return False, f"Judge Error: {str(e)}"