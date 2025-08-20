import discord
from discord.ext import commands
from discord import ButtonStyle, Interaction
from discord.ui import View, Button
import pytesseract
import cv2
import io
import os
import json
from datetime import datetime
from trade_ocr_analyzer import analyze_trade_image

TOKEN = os.getenv("TOKEN")
TRADE_CHANNEL_ID = int(os.getenv("TRADE_CHANNEL_ID"))
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID")) if os.getenv("AUTHORIZED_USER_ID") else None

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def handle_trade(message, attachment):
    try:
        if not (attachment.filename.endswith(".png") or attachment.filename.endswith(".jpg")):
            return

        image_bytes = await attachment.read()
        result = analyze_trade_image(image_bytes)

        embed = discord.Embed(title="Trade Analysis", color=discord.Color.blue())
        embed.add_field(name="Items Given", value="\n".join(result['items_given']), inline=True)
        embed.add_field(name="Items Received", value="\n".join(result['items_received']), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="RAP Gain/Loss", value=str(result['rap_received'] - result['rap_given']), inline=True)
        embed.add_field(name="Value Gain/Loss", value=str(result['value_received'] - result['value_given']), inline=True)
        embed.add_field(name="Bot Verdict", value=result['verdict'], inline=False)

        class VerdictView(View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(Button(label="Accept", style=ButtonStyle.success, custom_id="accept"))
                self.add_item(Button(label="Decline", style=ButtonStyle.danger, custom_id="decline"))
                self.add_item(Button(label="Consider", style=ButtonStyle.secondary, custom_id="consider"))

            async def interaction_check(self, interaction: Interaction):
                if AUTHORIZED_USER_ID and interaction.user.id != AUTHORIZED_USER_ID:
                    await interaction.response.send_message("You're not authorized to respond to this trade.", ephemeral=True)
                    return False
                return True

            @discord.ui.button(label="Accept", style=ButtonStyle.success, custom_id="accept")
            async def accept_button(self, interaction: Interaction, button: Button):
                await self.record_decision(interaction, "Accept")

            @discord.ui.button(label="Decline", style=ButtonStyle.danger, custom_id="decline")
            async def decline_button(self, interaction: Interaction, button: Button):
                await self.record_decision(interaction, "Decline")

            @discord.ui.button(label="Consider", style=ButtonStyle.secondary, custom_id="consider")
            async def consider_button(self, interaction: Interaction, button: Button):
                await self.record_decision(interaction, "Consider")

            async def record_decision(self, interaction, user_verdict):
                embed.set_field_at(5, name="Final Verdict", value=f"{result['verdict']} (Bot) / {user_verdict} (User)")
                await interaction.response.edit_message(embed=embed, view=None)

                trade_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": interaction.user.id,
                    "items_given": result['items_given'],
                    "items_received": result['items_received'],
                    "rap_given": result['rap_given'],
                    "rap_received": result['rap_received'],
                    "value_given": result['value_given'],
                    "value_received": result['value_received'],
                    "bot_verdict": result['verdict'],
                    "user_verdict": user_verdict
                }
                os.makedirs("logs", exist_ok=True)
                with open("logs/trades.json", "a") as f:
                    f.write(json.dumps(trade_data) + "\n")

        await message.reply(embed=embed, view=VerdictView())

    except Exception as e:
        await message.channel.send(f"Error analyzing trade: {str(e)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != TRADE_CHANNEL_ID:
        return
    for attachment in message.attachments:
        await handle_trade(message, attachment)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

bot.run(TOKEN)
