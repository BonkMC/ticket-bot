from utils import config
from interactions import Client, check, SlashContext
import os


AppConfig_obj = config.AppConfig()
token = AppConfig_obj.get_bonk_staff_key()
bot = Client(token=token, sync_interactions=True)



# Example role check function, make sure to change the role IDs.
CHECK_ROLES = [1111111111111111111, 2222222222222222222]
def role_check():
    async def predicate(ctx: SlashContext):
        user_roles = [int(i.id) for i in ctx.author.roles]
        return any(role_id in user_roles for role_id in CHECK_ROLES)
    return check(predicate)
