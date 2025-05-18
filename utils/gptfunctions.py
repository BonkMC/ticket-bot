import requests
import base64

def query_minecraft_server(address: str="play.bonkmc.net", mode: str = "java_status") -> str:
    """
    Query the Minecraft Server Status API.
    :param address: Server address (e.g. "play.bonkmc.net")
    :param mode: One of:
        - "java_status"
        - "bedrock_status"
        - "simple_status"
        - "bedrock_simple_status"
        - "icon"
        - "debug_ping"
        - "debug_query"
        - "debug_bedrock"
    :return:
      - JSON string for all *_status and debug modes
      - "True" or "False" for simple_status modes
      - Base64‐encoded PNG string for "icon"
    """
    BASE_URL = "https://api.mcsrvstat.us"
    headers = {"User-Agent": "BonkMCTicketBot/1.0 (contact: support@bonkmc.net)"}

    if mode == "java_status":
        url = f"{BASE_URL}/3/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return r.text

    if mode == "bedrock_status":
        url = f"{BASE_URL}/bedrock/3/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return r.text

    if mode == "simple_status":
        url = f"{BASE_URL}/simple/{address}"
        r = requests.get(url, headers=headers)
        return str(r.status_code == 200)

    if mode == "bedrock_simple_status":
        url = f"{BASE_URL}/bedrock/simple/{address}"
        r = requests.get(url, headers=headers)
        return str(r.status_code == 200)

    if mode == "icon":
        url = f"{BASE_URL}/icon/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return base64.b64encode(r.content).decode("ascii")

    if mode == "debug_ping":
        url = f"{BASE_URL}/debug/ping/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return r.text

    if mode == "debug_query":
        url = f"{BASE_URL}/debug/query/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return r.text

    if mode == "debug_bedrock":
        url = f"{BASE_URL}/debug/bedrock/{address}"
        r = requests.get(url, headers=headers); r.raise_for_status()
        return r.text

    raise ValueError(f"Unsupported mode: {mode}")

if __name__ == "__main__":
        result = query_minecraft_server("play.bonkmc.net", mode="java_status")
        print(result)