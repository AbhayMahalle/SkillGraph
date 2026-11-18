"""
Prompts package for SkillGraph LLM service.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent

def load_prompt(filename: str) -> str:
    """Loads a prompt template text file from disk."""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template '{filename}' not found in {PROMPTS_DIR}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()
