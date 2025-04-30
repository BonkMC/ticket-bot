from utils.config import AppConfig
import json
from openai import OpenAI

config = AppConfig()
api_key = config.get_openai_key()

client = OpenAI(api_key=api_key)  # Replace with your actual key

# Fake function to simulate real logic
def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny with 24°C."

# Function schema
functions = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g., 'Paris, France'",
                },
            },
            "required": ["location"],
        },
    }
]

# Initial chat message
messages = [
    {"role": "user", "content": "What's the weather like in Tokyo?"}
]

# First request
response = client.chat.completions.create(
    model="gpt-4-0613",
    messages=messages,
    functions=functions,
    function_call="auto",
)

response_message = response.choices[0].message

# Check if GPT wants to call a function
if response_message.function_call:
    function_name = response_message.function_call.name
    arguments = json.loads(response_message.function_call.arguments)

    if function_name == "get_weather":
        function_response = get_weather(**arguments)

        # Append function call and result to message history
        messages.append(response_message)
        messages.append({
            "role": "function",
            "name": function_name,
            "content": function_response
        })

        # Final GPT response with function result
        final_response = client.chat.completions.create(
            model="gpt-4-0613",
            messages=messages
        )

        print("🤖 GPT says:")
        print(final_response.choices[0].message.content)

else:
    print("GPT didn't call any function.")
    print(response_message.content)
