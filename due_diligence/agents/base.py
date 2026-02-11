"""Base agent class for Claude API calls with tool use."""

import anthropic
from rich.console import Console
from rich.panel import Panel

from due_diligence.config import ANTHROPIC_API_KEY

console = Console()


class BaseAgent:
    """Base class for all due diligence agents.

    Each agent has a name, system prompt, model, and optional tools.
    It calls the Claude API and extracts text + tool results from the response.
    """

    def __init__(self, name: str, system_prompt: str, model: str, max_tokens: int, tools: list | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self, user_prompt: str, state: dict) -> str:
        """Execute the agent with the given prompt and shared state.

        Args:
            user_prompt: The formatted prompt for this agent stage.
            state: Shared state dict containing outputs from prior agents.

        Returns:
            The agent's text response.
        """
        console.print(Panel(f"[bold cyan]{self.name}[/bold cyan]", subtitle="Starting...", style="cyan"))

        messages = [{"role": "user", "content": user_prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools

        # Run the agent, handling tool use loops (web search may require multiple turns)
        full_response_text = ""
        max_turns = 15

        for turn in range(max_turns):
            response = self.client.messages.create(**kwargs)

            # Extract text and tool results from response
            text_parts = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "web_search_tool_result":
                    # Web search results are automatically handled by Claude
                    pass

            turn_text = "\n".join(text_parts)
            full_response_text += turn_text

            # If stop reason is "end_turn", we're done
            if response.stop_reason == "end_turn":
                break

            # If stop reason is "tool_use", continue the conversation
            if response.stop_reason == "tool_use":
                # Add assistant response and empty user turn to continue
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{"type": "text", "text": "Continue with the analysis."}]})
                kwargs["messages"] = messages
                continue

            # Any other stop reason, break
            break

        console.print(f"  [green]✓[/green] {self.name} complete ({len(full_response_text)} chars)")
        return full_response_text
