from openai import OpenAI
import json

gpt_system_prompt = (
    "You are a simple helpful discord ticket answering assistant working for Bonk Network. "
    "Help users with their issues, answer questions, provide information, and troubleshoot problems related to the server. "
    "You can also provide links to helpful resources and guides. If a user mentions connection issues, provide generic help for joining the Minecraft Server. "
    "All text must follow Discord's messaging formatting. If you do not have the ability to do something, say 'I do not have the ability to fulfil that request.' "
    "Provide only basic help, and if a human is needed or requested, ask the user to ping a helper. "
    "Server IP is play.bonkmc.net, Java Edition, not whitelisted, not modded, and not cracked. "
    "Stay focused on ticket and Minecraft support, and redirect off-topic requests back on track. "
    "If the user requests staff support, ping the developers by typing '<@&1282491372250857676>', and describe the "
    "user's issue briefly. If the user mentions a bug, ask for more details and steps to reproduce. You may "
    "only "
    "ping a dev once in a chat session. "
)

class Chat:
    def __init__(self, key):
        self.messages = [{"role": "system", "content": gpt_system_prompt}]
        self.client = OpenAI(api_key=key)
        self.staff_ping_used = False

    def chat_with_gpt(self, prompt):
        # Append the user message.
        self.messages.append({"role": "user", "content": prompt})
        # Call the GPT API.
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=self.messages
        )
        # Extract the assistant's reply.
        answer = response.choices[0].message.content
        # If the user's prompt includes a staff ping request and it hasn't been used, append the ping.
        if "<@1282491372250857676>" in prompt and not self.staff_ping_used:
            answer += "\n\n<@1282491372250857676>"
            self.staff_ping_used = True
        # Save the assistant's reply.
        self.messages.append({"role": "assistant", "content": answer})
        return answer

class GPTChatterDB:
    def __init__(self, key, db_file="data/gptchatter.json"):
        self.key = key
        self.chat_objs = {}
        self.db_file = db_file
        self.load()

    def add_user(self, user):
        self.load()
        chat_obj = Chat(self.key)
        self.chat_objs[user] = chat_obj
        self.save()
        return chat_obj

    def get_user(self, user):
        self.load()
        if user in self.chat_objs:
            return self.chat_objs[user]
        return None

    def update_user(self, user, chat_obj):
        self.load()
        self.save(user, chat_obj)

    def delete_user(self, user):
        self.load()
        if user in self.chat_objs:
            del self.chat_objs[user]
            self.save()
        else:
            pass

    def save(self, user=None, chat_obj=None):
        if user is not None and chat_obj is not None:
            self.chat_objs[user] = chat_obj
        with open(self.db_file, "w") as f:
            json.dump(
                {user: chat_obj.messages for user, chat_obj in self.chat_objs.items()},
                f,
                indent=4,
            )

    def load(self):
        try:
            with open(self.db_file, "r") as f:
                chat_data = json.load(f)
                self.chat_objs = {
                    user: Chat(self.key)
                    for user, messages in chat_data.items()
                }
        except FileNotFoundError:
            pass
