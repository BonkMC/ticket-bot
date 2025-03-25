import atexit
from interactions import (
    slash_command,
    slash_option,
    OptionType,
    SlashContext,
    Embed,
    StringSelectMenu,
    Button,
    ButtonStyle,
    ActionRow,
    component_callback,
    ComponentContext,
    PermissionOverwrite,
    Permissions,
    Modal,
    ShortText,
    ParagraphText
)
from bot_instance import bot, ticket_handler, AppConfig_obj
from utils import colors, gptchatter

# Save tickets on program exit
atexit.register(ticket_handler.save)

chatter = gptchatter.GPTChatterDB(AppConfig_obj.get_openai_key())

# Define your support staff role ID (replace with your actual role ID)
SUPPORT_ROLE_ID = 123456789012345678


@slash_command(name="create_panel", description="Create a panel!")
@slash_option(
    name="channel",
    description="Channel to send in",
    required=True,
    opt_type=OptionType.CHANNEL
)
async def create_panel(ctx: SlashContext, channel):
    await ctx.send("Panel created!", ephemeral=True)

    panel_description = (
        "**Welcome To Tickets** 👋\n\n"
        "If you have any problems or questions related to the server, or if you need to clear up any doubts, "
        "you can create a ticket and our staff members will assist you.\n\n"
        "You can create a ticket related to the following:\n\n"
        "• **Report Ticket** 📢  - Report any player suspected of breaking server rules (e.g. hacking, exploiting, toxicity, etc.).\n\n"
        "• **General Ticket** 🎈 - Ask general questions related to the server.\n\n"
        "• **Appeal Ticket** 📜 - Appeal for your ban or mute.\n\n"
        "• **Bug Report Ticket** 🐛 - Report any bug or glitch found on the server.\n\n"
        "**RULES** 🛑\n"
        "When you create a ticket, please follow these rules or you may be subject to disciplinary action:\n\n"
        "1. **Impatience Is Not Allowed** - Please be patient; it might take us a moment to respond.\n"
        "2. **Don't Spam Ping** - Avoid spamming staff members with pings.\n"
        "3. **Create a Ticket When You Are Ready to Attend It** - Tickets without a response for a long time will be closed without notice.\n"
        "4. **Be Respectful** - Do not disrespect any staff member under any circumstances.\n"
        "5. **Staff Always Have the Final Say** - Staff decisions are final."
    )

    # Create a dropdown menu with ticket options (with emojis).
    dropdown = StringSelectMenu(
        "General Ticket 🎈", "Appeal Ticket 📜", "Report Ticket 📢", "Bug Report Ticket 🐛",
        custom_id="ticket_select_menu",  # persistent custom_id
        placeholder="Select a ticket category",
        min_values=1,
        max_values=1,
    )

    await channel.send(
        embed=Embed(
            title="Bonk Network | Support Tickets",
            description=panel_description,
            color=colors.DiscordColors.BLUE,
        ),
        components=[dropdown]
    )


@component_callback("ticket_select_menu")
async def handle_ticket_select(ctx: ComponentContext):
    # Save the selected ticket category from the dropdown.
    ticket_category = ctx.values[0]

    # Create and send the modal with a unique custom_id.
    my_modal = Modal(
        ShortText(label="What is your in game name?", custom_id="ign"),
        ParagraphText(label="Why are you making a ticket?", custom_id="reason"),
        title="Ticket Details",
        custom_id="ticket_modal"
    )
    await ctx.send_modal(modal=my_modal)

    # Wait for the modal submission.
    modal_ctx = await ctx.bot.wait_for_modal(my_modal)
    ign = modal_ctx.responses["ign"]
    reason_input = modal_ctx.responses["reason"]

    # Check if the user already has an open ticket.
    if ticket_handler.has_open_ticket(str(ctx.author.id)):
        await modal_ctx.send("You already have an open ticket.", ephemeral=True)
        return

    # Continue with your ticket creation process using the stored category.
    ticket_id = ticket_handler._generate_ticket_id()
    overwrites = [
        PermissionOverwrite(
            id=ctx.guild_id,
            type=0,
            deny=Permissions.VIEW_CHANNEL
        ),
        PermissionOverwrite(
            id=ctx.author.id,
            type=1,
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        ),
        PermissionOverwrite(
            id=SUPPORT_ROLE_ID,
            type=0,
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        )
    ]
    category_id = 1353874386716725359  # Discord category ID for tickets
    new_channel = await ctx.guild.create_text_channel(
        name=f"ticket-{ticket_id}",
        category=category_id,
        permission_overwrites=overwrites
    )

    subject = f"{ticket_category} Ticket"
    ticket = ticket_handler.create_ticket(
        user_id=str(ctx.author.id),
        channel_id=str(new_channel.id),
        subject=subject,
        reason=reason_input,
        ign_username=ign,
        category=ticket_category
    )

    # Initialize a GPT conversation for this ticket using its ticket id.
    chatter.add_user(ticket.ticket_id)

    welcome_embed = Embed(
        title="Ticket Opened",
        description=(
            f"Hello <@{ctx.author.id}>, thank you for contacting support regarding **{ticket_category}**.\n\n"
            f"**In Game Name:** ```{ign}```\n"
            f"**Ticket Reason:** ```{reason_input}```\n\n"
            "A member of our team will be with you shortly. Please provide any additional details regarding your issue."
        ),
        color=colors.DiscordColors.GREEN,
    )
    await new_channel.send(content=f"<@{ctx.author.id}>", embed=welcome_embed)

    # Send action buttons: Close Ticket and Delete Ticket.
    close_button = Button(
        custom_id="close_ticket",
        label="Close Ticket",
        style=ButtonStyle.PRIMARY,
        emoji="🔒"
    )
    buttons_row = ActionRow(close_button)
    await new_channel.send(components=[buttons_row])

    # Use the modal context to send a follow-up message.
    await modal_ctx.send(
        embed=Embed(
            title="Ticket Created",
            description=f"Your ticket for **{ticket_category}** has been created: {new_channel.mention}",
            color=colors.DiscordColors.GREEN,
        ),
        ephemeral=True
    )

    # Reset the dropdown on the panel message so users can create more tickets.
    new_dropdown = StringSelectMenu(
        "General Ticket 🎈", "Appeal Ticket 📜", "Report Ticket 📢", "Bug Report Ticket 🐛",
        custom_id="ticket_select_menu",
        placeholder="Select a ticket category",
        min_values=1,
        max_values=1,
    )
    try:
        await ctx.message.edit(components=[new_dropdown])
    except Exception:
        pass


@component_callback("close_ticket")
async def close_ticket_callback(ctx: ComponentContext):
    await ctx.defer(ephemeral=True)
    ticket = next((t for t in ticket_handler.tickets.values() if t.channel_id == str(ctx.channel.id)), None)
    if not ticket:
        await ctx.send("Ticket not found.", ephemeral=True)
        return
    if ticket.status == "closed":
        await ctx.send("This ticket is already closed.", ephemeral=True)
        return

    ticket_handler.close_ticket(ticket.ticket_id, f"Closed by <@{ctx.author.id}>")
    await ctx.channel.edit(name=f"closed-{ticket.ticket_id}")

    # Update permission overwrites in one PATCH call.
    new_overwrites = [
        PermissionOverwrite(
            id=ctx.guild_id,
            type=0,
            deny=Permissions.VIEW_CHANNEL
        ),
        PermissionOverwrite(
            id=ticket.user_id,
            type=1,
            allow=Permissions.VIEW_CHANNEL,
            deny=Permissions.SEND_MESSAGES
        ),
        PermissionOverwrite(
            id=SUPPORT_ROLE_ID,
            type=0,
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        )
    ]
    try:
        await ctx.channel.edit(permission_overwrites=new_overwrites)
    except Exception as e:
        print("Error updating permissions:", e)

    reopen_button = Button(
        custom_id="reopen_ticket",
        label="Reopen Ticket",
        style=ButtonStyle.PRIMARY,
        emoji="🔓"
    )
    delete_button = Button(
        custom_id="delete_ticket",
        label="Delete Ticket",
        style=ButtonStyle.DANGER,
        emoji="🗑️"
    )
    action_row = ActionRow(reopen_button, delete_button)
    close_embed = Embed(
        title="Ticket Closed",
        description="This ticket has been closed. To reopen it, click the unlock button below.",
        color=0xFF0000
    )
    await ctx.channel.send(embed=close_embed, components=[action_row])
    await ctx.send("Ticket closed successfully.", ephemeral=True)
    # Remove the GPT conversation from storage now that the ticket is closed.
    chatter.delete_user(ticket.ticket_id)


@component_callback("reopen_ticket")
async def reopen_ticket_callback(ctx: ComponentContext):
    await ctx.defer(ephemeral=True)
    ticket = next((t for t in ticket_handler.tickets.values() if t.channel_id == str(ctx.channel.id)), None)
    if not ticket:
        await ctx.send("Ticket not found.", ephemeral=True)
        return
    if ticket.status != "closed":
        await ctx.send("This ticket is not closed.", ephemeral=True)
        return

    ticket_handler.update_ticket(ticket.ticket_id, status="open")
    ticket_handler.add_ticket_log_with_user(ticket.ticket_id, str(ctx.author.id), ctx.author.username,
                                              "Ticket reopened.")
    await ctx.channel.edit(name=f"ticket-{ticket.ticket_id}")

    new_overwrites = [
        PermissionOverwrite(
            id=ctx.guild_id,
            type=0,
            deny=Permissions.VIEW_CHANNEL
        ),
        PermissionOverwrite(
            id=ticket.user_id,
            type=1,
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        ),
        PermissionOverwrite(
            id=SUPPORT_ROLE_ID,
            type=0,
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        )
    ]
    try:
        await ctx.channel.edit(permission_overwrites=new_overwrites)
    except Exception as e:
        print("Error updating permissions on reopen:", e)

    close_button = Button(
        custom_id="close_ticket",
        label="Close Ticket",
        style=ButtonStyle.PRIMARY,
        emoji="🔒"
    )
    delete_button = Button(
        custom_id="delete_ticket",
        label="Delete Ticket",
        style=ButtonStyle.DANGER,
        emoji="🗑️"
    )
    buttons_row = ActionRow(close_button, delete_button)
    reopen_embed = Embed(
        title="Ticket Reopened",
        description="This ticket has been reopened. You may now continue the conversation.",
        color=colors.DiscordColors.GREEN
    )
    await ctx.channel.send(embed=reopen_embed, components=[buttons_row])
    await ctx.send("Ticket reopened successfully.", ephemeral=True)


@component_callback("delete_ticket")
async def delete_ticket_callback(ctx: ComponentContext):
    await ctx.defer(ephemeral=True)
    ticket = next((t for t in ticket_handler.tickets.values() if t.channel_id == str(ctx.channel.id)), None)
    if not ticket:
        await ctx.send("Ticket not found.", ephemeral=True)
        return
    if ticket.status != "closed":
        await ctx.send("You cannot delete a ticket until it is closed.", ephemeral=True)
        return

    ticket_handler.add_ticket_log_with_user(ticket.ticket_id, str(ctx.author.id), ctx.author.username,
                                              "Ticket channel deleted.")
    ticket_handler.update_ticket(ticket.ticket_id, channel_id="deleted")
    await ctx.channel.delete()


# Event listener to log every user message in ticket channels and interact with GPT.
@bot.listen("on_message_create")
async def log_ticket_message(event):
    msg = event.message
    # Determine message content.
    content = ""
    if hasattr(msg, "content") and msg.content:
        content = msg.content
    elif hasattr(msg, "data") and msg.data.get("content"):
        content = msg.data.get("content")
    if not content:
        if hasattr(msg, "attachments") and msg.attachments:
            attachment_urls = ", ".join(att.url for att in msg.attachments)
            content = f"[Attachment(s): {attachment_urls}]"
        else:
            content = "[No message content]"

    # Get the author; ignore bot messages.
    author = getattr(msg, "author", None) or msg.member
    if not author or getattr(author, "bot", False):
        return

    # Check if this channel is a ticket channel.
    for ticket in ticket_handler.tickets.values():
        if ticket.channel_id == str(msg.channel.id):
            # Log the message as before.
            ticket_handler.add_ticket_log_with_user(
                ticket.ticket_id,
                str(author.id),
                author.username,
                content
            )
            # If the message is from the ticket owner and the ticket is open, call GPT.
            if ticket.user_id == str(author.id) and ticket.status == "open":
                chat_obj = chatter.get_user(ticket.ticket_id)
                if not chat_obj:
                    chat_obj = chatter.add_user(ticket.ticket_id)
                # Trigger typing indicator while generating the GPT response.
                await msg.channel.trigger_typing()
                answer = chat_obj.chat_with_gpt(content)
                try:
                    await msg.reply(answer)
                except Exception as e:
                    print("Error sending GPT reply:", e)
            break


@slash_command(name="close", description="Close the current ticket")
async def close_ticket_command(ctx: SlashContext):
    await ctx.defer(ephemeral=True)

    # Find the ticket associated with this channel.
    ticket = next((t for t in ticket_handler.tickets.values() if t.channel_id == str(ctx.channel_id)), None)
    if not ticket:
        await ctx.send("Ticket not found in this channel.", ephemeral=True)
        return
    if ticket.status == "closed":
        await ctx.send("This ticket is already closed.", ephemeral=True)
        return

    # Close the ticket and update its channel name.
    ticket_handler.close_ticket(ticket.ticket_id, f"Closed by <@{ctx.author.id}>")
    await ctx.channel.edit(name=f"closed-{ticket.ticket_id}")

    # Update permission overwrites in one PATCH call.
    new_overwrites = [
        PermissionOverwrite(
            id=ctx.guild_id,
            type=0,  # Role (@everyone)
            deny=Permissions.VIEW_CHANNEL
        ),
        PermissionOverwrite(
            id=ticket.user_id,
            type=1,  # Member
            allow=Permissions.VIEW_CHANNEL,
            deny=Permissions.SEND_MESSAGES
        ),
        PermissionOverwrite(
            id=SUPPORT_ROLE_ID,
            type=0,  # Role (Support staff)
            allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
        )
    ]
    try:
        await ctx.channel.edit(permission_overwrites=new_overwrites)
    except Exception as e:
        print("Error updating permissions:", e)

    # Send a message with buttons to allow reopening or deleting the ticket.
    reopen_button = Button(
        custom_id="reopen_ticket",
        label="Reopen Ticket",
        style=ButtonStyle.PRIMARY,
        emoji="🔓"
    )
    delete_button = Button(
        custom_id="delete_ticket",
        label="Delete Ticket",
        style=ButtonStyle.DANGER,
        emoji="🗑️"
    )
    action_row = ActionRow(reopen_button, delete_button)
    close_embed = Embed(
        title="Ticket Closed",
        description="This ticket has been closed. To reopen it, click the unlock button below.",
        color=0xFF0000
    )
    await ctx.channel.send(embed=close_embed, components=[action_row])
    await ctx.send("Ticket closed successfully.", ephemeral=True)
    # Remove the GPT conversation from storage.
    chatter.delete_user(ticket.ticket_id)
