from litellm import completion

import os

class LLM:
    def __init__(self, model, system_prompt):
        self.base_url = os.getenv("LLM_BASE_URL") or "https://ollama.com"
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = 0.7

    def text_complete(self, prompt):
        print(f"[llm] sending prompt")
        response = completion(model=self.model, messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}], base_url=self.base_url, temperature=self.temperature)
        print(f"[llm] response received")
        msg = getattr(response.choices[0], "message", None)
        content = getattr(msg, "content", None) if msg else None
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif hasattr(block, "text"):
                    parts.append(str(getattr(block, "text", "") or ""))
            return "\n".join(parts).strip()
        return str(content or "").strip()
