# This is an example of a command. Each command should be a separate file and will be automatically imported and usable.
from interactions import slash_command, SlashContext, Embed

from bot_instance import role_check
from utils import colors


@slash_command(name="example", description="This is an example of a command description!.")
@role_check()
async def handle_test_command(ctx: SlashContext):
    test_start_msg = Embed(description="Running Tests...", color=colors.DiscordColors.GREEN)
    msg = await ctx.send(embeds=test_start_msg)
    test_complete_msg = Embed(description="Test Complete!", color=colors.DiscordColors.GREEN)
    await msg.edit(embeds=test_complete_msg)
