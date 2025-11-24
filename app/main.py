# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.layers import static_layer, ml_layer, output_layer

app = FastAPI(title="PromptShield API")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_response(request: PromptRequest):
    user_prompt = request.prompt
    print(f"Received: {user_prompt}")

    # 1. Static Layer
    is_safe, msg = static_layer(user_prompt)
    if not is_safe:
        return {"status": "blocked", "layer": "static", "message": msg}

    # 2. ML Layer
    is_safe, msg = ml_layer(user_prompt)
    if not is_safe:
        return {"status": "blocked", "layer": "ml", "message": msg}

    # 3. LLM Gateway (Simulated)
    # We simulate an LLM response here. 
    # If the user asks for a password, we simulate a leak to test Layer 4.
    if "password" in user_prompt.lower():
        llm_response = "Here is the admin password: secret_token_123"
    else:
        llm_response = f"Processed: {user_prompt}"

    # 4. Output Validation
    is_safe, msg = output_layer(llm_response)
    if not is_safe:
        return {"status": "blocked", "layer": "output", "message": msg}

    return {"status": "success", "response": llm_response}