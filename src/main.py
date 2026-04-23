from dotenv import load_dotenv
from gemini import Gemini
from llm import LLM
from telegram import Telegram
from pathlib import Path

import os
import asyncio

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


async def main():
    load_dotenv()
    async with Telegram(
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        group=os.getenv("GROUP"),
    ) as telegram:
        topic, message_id = await telegram.get_latest_message()
        print(f"[pipeline]Topic: {topic}")
        #await telegram.reply("Hello, world!", message_id)

    gemini = Gemini(api_key=os.getenv("GEMINI_API_KEY"))
    research = gemini.run_deep_research(
        prompt_txt_path=PROMPTS_DIR / "deep_research.txt",
        topic=topic,
        agent=os.getenv("GEMINI_DEEP_RESEARCH_AGENT") or "deep-research-pro-preview-12-2025",
    )

    judge_response = ""

    for attempt in range(0, 5):
        print(f"[pipeline] Attempt {attempt + 1}:")
        print(f"[pipeline] Generating blog post...")
        if attempt == 0:
            blog_writer_prompt_path = PROMPTS_DIR/"blog_writer.txt"
            blog_writer = LLM(model="gemma3:4b-cloud", system_prompt=blog_writer_prompt_path.read_text(encoding="utf-8"))
            blog_writer_response = blog_writer.text_complete(prompt=f"Write a blog post about {topic} based on the following research: {research}")
        else:
            blog_writer = LLM(model="gemma3:4b-cloud", system_prompt="Rewrite the blog post based on the recommendations from the judge.")
            blog_writer_response = blog_writer.text_complete(prompt=f"Blog post: {blog_writer_response}. Recommendations from the judge: {judge_response}")
        
        print(f"[pipeline] Judging blog post...")
        judge_prompt_path = PROMPTS_DIR/"judge.txt"
        judge = LLM(model="gemma3:4b-cloud", system_prompt=judge_prompt_path.read_text(encoding="utf-8"))
        judge_response = judge.text_complete(prompt=f"The blog post is: {blog_writer_response}")
        
        print(f"[pipeline] Judge response: {judge_response}")
        
        if judge_response.lower() == "approved":
            print("[pipeline] Blog post approved")
            print(f"[pipeline] Blog post: {blog_writer_response}")
            break
        else:
            print("[pipeline] Blog post not approved")
    

if __name__ == "__main__":
    asyncio.run(main())