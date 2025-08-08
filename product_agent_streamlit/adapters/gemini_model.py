"""
Gemini model adapter for OpenAI Agents SDK
This allows using Gemini models with the OpenAI Agents framework
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncIterator
import google.generativeai as genai
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage
import time
import uuid

class GeminiChatModel:
    """
    Custom Gemini model that implements the interface expected by OpenAI Agents SDK.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", api_key: str = None, base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"):
        self.model_name = model_name
        if api_key:
            genai.configure(api_key=api_key)
        self.base_url = base_url
        self.gemini_model = genai.GenerativeModel(model_name)
        print(f"🤖 Initialized Gemini model: {model_name}")
        
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, Any]]) -> str:
        """Convert OpenAI-style messages to a single prompt for Gemini."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _create_chat_completion_response(self, content: str) -> ChatCompletion:
        """Create a ChatCompletion response that matches OpenAI's format."""
        return ChatCompletion(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(
                        content=content,
                        role="assistant"
                    )
                )
            ],
            created=int(time.time()),
            model=self.model_name,
            object="chat.completion",
            usage=CompletionUsage(
                completion_tokens=len(content.split()),
                prompt_tokens=0,  # Gemini doesn't provide exact token counts easily
                total_tokens=len(content.split())
            )
        )
    
    async def create(
    self,
    messages: List[Dict[str, Any]],
    model: str,
    **kwargs
) -> ChatCompletion:
        """Create a chat completion using Gemini with proper error handling."""
        try:
            print(f"🔄 Processing {len(messages)} messages with Gemini...")
            
            # Convert OpenAI messages to Gemini prompt
            prompt = self._convert_messages_to_gemini_format(messages)
            
            # FIXED: Further reduce prompt size and sanitize content
            if len(prompt) > 10000:
                prompt = prompt[:10000] + "\n[Content truncated]"
            
            # FIXED: Sanitize prompt to avoid blocks
            prompt = self._sanitize_prompt(prompt)
            
            print(f"📝 Sanitized prompt length: {len(prompt)} characters")
            
            # Generate response using Gemini with safety settings
            print("🤖 Calling Gemini API...")
            
            # FIXED: Add safety settings to reduce blocking
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                safety_settings=safety_settings
            )
            
            # FIXED: Handle all possible response states
            content = self._extract_response_content(response)
            print(f"✅ Gemini response length: {len(content)} characters")
            
            return self._create_chat_completion_response(content)
            
        except Exception as e:
            error_msg = f"Error calling Gemini API: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_chat_completion_response("I'm having trouble processing that request. Please try a more specific product question.")

    def _sanitize_prompt(self, prompt: str) -> str:
        """Remove potentially problematic content that might cause blocking."""
        # Remove special characters that might cause issues
        import re
        
        # Remove excessive punctuation
        prompt = re.sub(r'[!@#$%^&*()]{3,}', '', prompt)
        
        # Remove repeated characters
        prompt = re.sub(r'(.)\1{5,}', r'\1\1\1', prompt)
        
        # Remove potentially problematic words
        problematic_patterns = [
            r'\b(hack|crack|break)\b',
            r'\b(illegal|banned|forbidden)\b',
        ]
        
        for pattern in problematic_patterns:
            prompt = re.sub(pattern, '[redacted]', prompt, flags=re.IGNORECASE)
        
        return prompt

    def _extract_response_content(self, response) -> str:
        """Extract content from Gemini response with comprehensive error handling."""
        try:
            # Check if response has text attribute and it's accessible
            if hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            print(f"Could not access response.text: {e}")
        
        # Try to access candidates directly
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check finish reason
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    print(f"Finish reason: {finish_reason}")
                    
                    if finish_reason == 1:  # STOP
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            return candidate.content.parts[0].text
                    elif finish_reason == 3:  # SAFETY
                        return "Response blocked by safety filters. Please rephrase your question."
                    elif finish_reason == 4:  # RECITATION
                        return "Response blocked due to recitation concerns. Please try a different approach."
                    elif finish_reason == 12:  # BLOCKED_REASON_OTHER
                        return "Response blocked by content policy. Please try asking about specific product features or specifications."
                    else:
                        return f"Response generation incomplete (reason: {finish_reason}). Please try a simpler question."
                
                # Try to get content anyway
                if hasattr(candidate, 'content') and candidate.content.parts:
                    return candidate.content.parts[0].text
        except Exception as e:
            print(f"Error accessing candidates: {e}")
        
        return "Unable to generate response. Please try asking about specific products or features."