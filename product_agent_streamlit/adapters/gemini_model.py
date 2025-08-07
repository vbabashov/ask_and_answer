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
        """
        Create a chat completion using Gemini.
        This method signature matches what OpenAI Agents SDK expects.
        """
        try:
            print(f"🔄 Processing {len(messages)} messages with Gemini...")
            
            # Convert OpenAI messages to Gemini prompt
            prompt = self._convert_messages_to_gemini_format(messages)
            print(f"📝 Converted prompt length: {len(prompt)} characters")
            
            # Generate response using Gemini
            print("🤖 Calling Gemini API...")
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            content = response.text if response.text else "I apologize, but I couldn't generate a response."
            print(f"✅ Gemini response length: {len(content)} characters")
            
            # Return in OpenAI ChatCompletion format
            return self._create_chat_completion_response(content)
            
        except Exception as e:
            error_msg = f"Error calling Gemini API: {str(e)}"
            print(f"❌ {error_msg}")
            # Return error as a valid ChatCompletion
            return self._create_chat_completion_response(f"I encountered an error: {error_msg}")
