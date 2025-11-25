# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.layers import static_layer, ml_layer, output_layer
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PromptShield API")

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_response(request: PromptRequest):
    user_prompt = request.prompt
    print(f"Received: {user_prompt}")

    # 1. Static Layer
    is_safe, msg = static_layer(user_prompt)
    if not is_safe:
        return {
            "status": "blocked", 
            "layer": "Static Rule Checker", 
            "message": "⚠️ Potential security threat detected",
            "details": msg,
            "prompt": user_prompt
        }

    # 2. ML Layer
    is_safe, msg = ml_layer(user_prompt)
    if not is_safe:
        return {
            "status": "blocked", 
            "layer": "ML Classifier", 
            "message": "⚠️ AI security system flagged this prompt as potentially malicious",
            "details": msg,
            "prompt": user_prompt
        }

    # 3. LLM Gateway - Generate real response using Groq
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, concise, and accurate responses to user queries."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024
        )
        
        llm_response = completion.choices[0].message.content
        
    except Exception as e:
        print(f"LLM Error: {e}")
        llm_response = "I'm having trouble processing your request right now. Please try again later."

    # 4. Output Validation
    is_safe, msg = output_layer(llm_response, user_prompt)
    if not is_safe:
        return {
            "status": "blocked", 
            "layer": "Output Validator", 
            "message": "⚠️ Response blocked due to potential data leakage",
            "details": msg,
            "prompt": user_prompt
        }

    return {"status": "success", "response": llm_response}