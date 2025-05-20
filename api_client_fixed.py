def generate_text(ai_headers, user_prompt):
    """Generate text using the configured AI API with a base system persona and a user-specific prompt."""
    from config import AI_BASE_PERSONA, OPENAI_MODEL_NAME, AI_PROVIDER # Re-import for clarity

    if AI_PROVIDER == "openai":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            model_name = OPENAI_MODEL_NAME

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": AI_BASE_PERSONA},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 250, # Max tokens for the generated text itself
                "top_p": 1
            }
            
            response = requests.post(url, headers=ai_headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_json = response.json()
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    model_response = response_json['choices'][0]['message']['content'].strip()
                    logger.info(f"Successfully generated text ({len(model_response)} chars) using {model_name} via OpenAI")
                    return model_response
                else:
                    logger.error(f"Unexpected OpenAI API response format: {response_json}")
                    return None
            else:
                error_msg = f"OpenAI API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return None
        except Exception as e:
            logger.error(f"Error in generate_text with OpenAI: {e}")
            return None
    else:
        logger.error(f"generate_text called with unsupported AI_PROVIDER: {AI_PROVIDER}")
        return None # Fallback handled by caller 