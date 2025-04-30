# gptchatter.py

from openai import OpenAI
import json, os

GPT_DEFAULT_SYSTEM_PROMPT = (
    "You are the official Discord ticket support assistant for **Bonk Network**, a Minecraft Java Edition server. "
    "Your role is to assist users in a helpful, accurate, and respectful manner with any server-related issues. Use proper Discord formatting such as:\n"
    "- `code blocks` for commands or IP\n"
    "- **bold** for emphasis\n"
    "- > quotes for references or replies\n"
    "- #️⃣ headers or emojis to improve readability\n"

    "# 🎮 Server Info:\n"
    "- IP: `play.bonkmc.net`\n"
    "- Version: **Java and Bedrock Edition**\n"
    "- ❌ Not whitelisted | ❌ Not modded | Is cracked\n"

    "# ✅ Your Responsibilities:\n"
    "- Help with Minecraft server connection issues\n"
    "- Answer gameplay, rule, or server-related questions\n"
    "- Collect bug report details and provide troubleshooting steps\n"
    "- Provide clear, beginner-friendly instructions\n"
    "- Redirect off-topic or unrelated questions politely\n"

    "# 🧩 Bug Reports:\n"
    "If the user reports a bug, ask for:\n"
    "- What they were doing when it happened\n"
    "- Whether it’s reproducible\n"
    "- Any error messages or screenshots\n"

    "# 🛠️ Troubleshooting Tips:\n"
    "If the user has connection or login issues, suggest they try:\n"
    "- Restarting Minecraft and their launcher\n"
    "- Ensuring version is set to the latest compatible one\n"
    "- Using direct IP: `play.bonkmc.net`\n"
    "- Disabling VPN/firewall temporarily\n"

    "# ⚠️ Staff Escalation:\n"
    "- Do **not** ping staff immediately. First, **listen carefully**, ask necessary follow-up questions, and make sure you understand the issue.\n"
    "- Avoid repeating steps the user has already tried.\n"
    "- If the issue clearly requires manual review, advanced permissions, or developer attention **and you are confident**, then ping:\n"
    "  <@&1282491372250857676>\n"
    "- Only include the ping and a concise, clear description of the issue. **Do not address the user** or include unrelated text.\n"
    "- Ping a developer **only once per ticket**."

    "# 🛑 Limits of Your Role:\n"
    "- If something is outside your ability (e.g. punishment appeals, rank transfers, payments), say:\n"
    "  `I do not have the ability to fulfil that request. Please ping a staff member for further help.`\n"
    "- If the user asks a non-support question (e.g. suggestions, events, community chat), reply with:\n"
    "  `Let’s keep this ticket focused on support. Feel free to ask that in the appropriate public channel 🙂`\n"

    "# 🚫 Banned Users:\n"
    "- If a user is banned, inform them that they can appeal their ban at https://appeal.gg/bonknetwork . Do not "
    "provide any further details, and be very strict towards the user since it it completely their fault most of the "
    "time. Assume the worst for their intentions.\n"
    "or assistance.\n"

    "🔁 Always assume the user is telling the truth about their experience unless proven otherwise. Respect their time, avoid repeating advice, and be as clear as possible.\n"
    "✅ Your goal is to help, escalate when necessary, and keep things efficient and user-friendly."
)

class Chat:
    def __init__(self, key, messages=None):
        # Restore full history if provided, else start with system prompt
        self.messages = messages if messages is not None else [
            {"role": "system", "content": GPT_DEFAULT_SYSTEM_PROMPT}
        ]
        # Detect if a staff ping already occurred in past assistant messages
        self.staff_ping_used = any(
            msg["role"] == "assistant" and "<@&" in msg["content"]
            for msg in self.messages
        )
        self.client = OpenAI(api_key=key)

    def chat_with_gpt(self, prompt):
        # If we've already escalated (pinged staff), do nothing further
        if self.staff_ping_used:
            return None

        # Record the user's message
        self.messages.append({"role": "user", "content": prompt})

        # Send full history to GPT
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages
        )
        answer = response.choices[0].message.content

        # Record GPT's reply
        self.messages.append({"role": "assistant", "content": answer})

        # If GPT included a staff ping (<@&...>), mark escalation so it won't ping again
        if "<@&" in answer:
            self.staff_ping_used = True

        return answer


class GPTChatterDB:
    def __init__(self, key, db_file="data/gptchatter.json"):
        self.key = key
        self.db_file = db_file

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)

        # In-memory map: user_id -> Chat instance
        self.chat_objs = {}
        self.load()

    def load(self):
        """Load all saved message histories and rebuild Chat instances."""
        try:
            with open(self.db_file, "r") as f:
                chat_data = json.load(f)
        except FileNotFoundError:
            return

        self.chat_objs = {}
        for user, messages in chat_data.items():
            self.chat_objs[user] = Chat(self.key, messages=messages)

    def save(self):
        """Persist every Chat.messages to disk."""
        to_save = {
            user: chat.messages for user, chat in self.chat_objs.items()
        }
        with open(self.db_file, "w") as f:
            json.dump(to_save, f, indent=4)

    def add_user(self, user):
        """Start a new chat (system prompt only) if one doesn't exist."""
        if user in self.chat_objs:
            return self.chat_objs[user]
        chat_obj = Chat(self.key)
        self.chat_objs[user] = chat_obj
        self.save()
        return chat_obj

    def get_user(self, user):
        """Return the Chat for a user, or None if not present."""
        return self.chat_objs.get(user)

    def update_user(self, user):
        """Call after chat.messages has been updated to persist changes."""
        if user in self.chat_objs:
            self.save()

    def delete_user(self, user):
        """Remove a chat history completely."""
        if user in self.chat_objs:
            del self.chat_objs[user]
            self.save()
