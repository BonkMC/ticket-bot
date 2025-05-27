from openai import OpenAI
import json, os

from utils.gptfunctions import query_minecraft_server

MODEL = "gpt-4o"
GPT_DEFAULT_SYSTEM_PROMPT = (
    "You are the official Discord ticket support assistant for **Bonk Network**, a Minecraft Java Edition server. "
    "Your role is to assist users in a helpful, accurate, and respectful manner with any server-related issues. Use proper Discord formatting such as:\n"
    "- `code blocks` for commands or IP\n"
    "- **bold** for emphasis\n"
    "- > quotes for references or replies\n"
    "- #️⃣ headers or emojis to improve readability\n"

    "# 🎮 Server Info:\n"
    "- IP: `play.bonkmc.net`\n"
    "- Java Edition: `1.20.x - 1.21.x`\n"
    "- Store: https://bonkmc.tebex.io\n"
    "- Version: **Java and Bedrock Edition**\n"
    "- ❌ Not whitelisted | ❌ Not modded | ✅ Is cracked\n"

    "# ✅ Your Responsibilities:\n"
    "- Help with Minecraft server connection issues\n"
    "- Answer gameplay, rule, or server-related questions\n"
    "- Collect bug report details and provide troubleshooting steps\n"
    "- Provide clear, beginner-friendly instructions\n"
    "- Redirect off-topic or unrelated questions politely\n"
    "- Tell the user how to buy a rank, crate key, or coins via the store.\n"

    "# 🧩 Bug Reports:\n"
    "If the user reports a bug, ask for:\n"
    "- What they were doing when it happened\n"
    "- Whether it’s reproducible\n"
    "- Any error messages or screenshots\n"
    "- Their Minecraft version\n"
    "If the user says the server is down, or they think the server is down for everyone, or something similar, "
    "call the function query_minecraft_server to check. If there are 0 people online, or the server itself is "
    "offline, immediately ping staff.\n"

    "# 🛠️ Troubleshooting Tips:\n"
    "If the user has connection or login issues, suggest they try:\n"
    "- Restarting Minecraft and their launcher\n"
    "- Ensuring version is set to the latest compatible one\n"
    "- Using direct IP: `play.bonkmc.net`\n"
    "- Disabling client modifications\n"
    "- Checking internet connection\n"
    "- And more ideas up to your description.\n"
    "If the user says they still can not join, use the query_minecraft_server function to check. If there are 0 people online, or the server itself is "
    "offline, immediately ping staff.\n"
    "# 🔄 User Follow-Up:\n"
    "- If the user after 2 attempts still can not join, use other methods you know.\n"

    "# ⚠️ Staff Escalation:\n"
    "- Do **not** ping staff immediately. First, **listen carefully**, ask necessary follow-up questions, and make sure you understand the issue.\n"
    "- Avoid repeating steps the user has already tried.\n"
    "- If the issue clearly requires manual review, advanced permissions, or developer attention **and you are confident**, then ping:\n"
    "  <@&1282491372250857676>\n"
    "- Only include the ping and a concise, clear description of the issue. **Do not address the user** or include unrelated text.\n"
    "- Ping a developer **only once per ticket**.\n"

    "# 🛑 Limits of Your Role:\n"
    "- If something is outside your ability (e.g. punishment appeals, rank transfers, payments), say:\n"
    "  `I do not have the ability to fulfil that request. Please ping a staff member for further help.`\n"
    "- If the user asks a non-support question (e.g. suggestions, events, community chat), reply with:\n"
    "  `Let’s keep this ticket focused on support. Feel free to ask that in the appropriate public channel 🙂`\n"

    "# 🚫 Banned Users:\n"
    "- If a user is banned, inform them that they can appeal their ban at https://appeal.gg/bonknetwork . Do not "
    "provide any further details, and be very strict towards the user since it is completely their fault most of the "
    "time. Assume the worst for their intentions.\n"

    "# 💼 Staff Applications:\n"
    "If a user asks how to become staff, respond with:\n"
    "  `To apply for a staff position, please head to the #applications channel on this server and follow the instructions there.`\n"

    "# 🎁 Free Item Requests:\n"
    "If the user requests free paid items (ranks, crate keys, coins), respond with:\n"
    "  `Paid items are only available through our store. Free paid items are only given out via official giveaways. `\n"
    "  `You can opt in for giveaway notifications by assigning yourself the Giveaway Ping role in the #roles channel.`\n"

    "# 🏷️ Coupon Codes & Promotions:\n"
    "If asked about discount codes or promotions, explain:\n"
    "  `You can enter valid coupon codes at checkout on our store page. Promotions are time-limited—check our announcements for the latest codes.`\n"

    "# 💲 Payment Issues or Caregiving Item after Transaction Issues:\n"
    "- If a user reports a payment failure, ask for:\n"
    "  - Payment method used\n"
    "  - Screenshot of the error\n"
    "- For refund requests, explain our policy:\n"
    "  `We do not accept refunds under any circumstances.`\n"

    "# 🤝 Partnerships & Advertising:\n"
    "If a user inquires about server partnerships or advertising, reply with:\n"
    "  <@&1282491372250857676>\n"
    "  Please send your advertisement text, a Discord server invite link, and what you are offering to pay us.\n"

    "🔁 Always assume the user is telling the truth about their experience unless proven otherwise, or is a punished user, or is asking for a refund. "
    "Respect their time, avoid repeating advice, and be as clear as possible.\n"
    "✅ Your goal is to help, escalate when necessary, and keep things efficient and user-friendly."
)


class Chat:
    def __init__(self, key, messages=None):
        if messages is not None:
            clean = []
            for m in messages:
                if "content" in m and m["content"] is None:
                    continue
                clean.append(m)
            self.messages = clean
        else:
            self.messages = [
                {"role": "system", "content": GPT_DEFAULT_SYSTEM_PROMPT}
            ]

        self.staff_ping_used = any(
            m.get("role") == "assistant"
            and isinstance(m.get("content"), str)
            and "<@&" in m["content"]
            for m in self.messages
        )
        self.client = OpenAI(api_key=key)

    def chat_with_gpt(self, prompt):
        if self.staff_ping_used:
            return None

        self.messages.append({"role": "user", "content": prompt})

        functions = [{
            "name": "query_minecraft_server",
            "description": "Get the current status of Bonk Network's Minecraft server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": [
                            "java_status"
                        ]
                    }
                }
            }
        }]

        resp = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            functions=functions,
            function_call="auto"
        )
        msg = resp.choices[0].message

        if msg.function_call:
            self.messages.append({
                "role": "assistant",
                "name": msg.function_call.name,
                "function_call": {
                    "name": msg.function_call.name,
                    "arguments": msg.function_call.arguments
                }
            })

            args = json.loads(msg.function_call.arguments)
            result = query_minecraft_server(**args)

            self.messages.append({
                "role": "function",
                "name": msg.function_call.name,
                "content": result
            })

            followup = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages
            )
            final_msg = followup.choices[0].message.content
            self.messages.append({"role": "assistant", "content": final_msg})
            return final_msg

        content = msg.content
        self.messages.append({"role": "assistant", "content": content})
        return content


class GPTChatterDB:
    def __init__(self, key, db_file="data/gptchatter.json"):
        self.key = key
        self.db_file = db_file

        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)

        self.chat_objs = {}
        self.load()

    def load(self):
        try:
            with open(self.db_file, "r") as f:
                chat_data = json.load(f)
        except FileNotFoundError:
            return

        self.chat_objs = {}
        for user, messages in chat_data.items():
            self.chat_objs[user] = Chat(self.key, messages=messages)

    def save(self):
        to_save = {
            user: chat.messages for user, chat in self.chat_objs.items()
        }
        with open(self.db_file, "w") as f:
            json.dump(to_save, f, indent=4)

    def add_user(self, user):
        if user in self.chat_objs:
            return self.chat_objs[user]
        chat_obj = Chat(self.key)
        self.chat_objs[user] = chat_obj
        self.save()
        return chat_obj

    def get_user(self, user):
        return self.chat_objs.get(user)

    def update_user(self, user):
        if user in self.chat_objs:
            self.save()

    def delete_user(self, user):
        if user in self.chat_objs:
            del self.chat_objs[user]
            self.save()
