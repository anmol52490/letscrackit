from google import genai
import os

def get_gemini_response(prompt):
    """
    Sends a prompt to Gemini using the new google-genai SDK.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not found."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error contacting AI: {str(e)}"