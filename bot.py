import discord
from discord.ext import commands
from datetime import datetime
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

data = {}

# Calm, caring Taglish (not cringe)
IN_QUOTES = [
    "Good luck today. I’m here if you need me.",
    "Take it one task at a time. Kaya mo.",
    "Start lang—no pressure.",
    "Rooting for you, always.",
]
LUNCH_QUOTES = [
    "Lunch muna, please. Kahit konti.",
    "Eat properly ha. Important ’yan.",
    "Take a real break—deserve mo.",
    "Slow down muna. Saglit lang.",
]
RESUME_QUOTES = [
    "Okay, resume na tayo. Chill pace lang.",
    "One step at a time ulit.",
    "Let’s continue—steady lang.",
    "Almost there. Proud ako sayo.",
]
OUT_QUOTES = [
    "Good work today. Rest na, okay?",
    "You did enough today. Proud ako sayo.",
    "Solid effort today. Time to recharge.",
    "Thank you for showing up today. Pahinga na.",
]
RESET_QUOTES = [
    "Fresh start ulit. Take it easy.",
    "Okay, reset. New day, new pace.",
    "Back to zero—no pressure.",
]

def now_time():
    return datetime.now().strftime("%I:%M %p")

def today_key():
    return datetime.now().strftime("%Y-%m-%d")

def today_label():
    return datetime.now().strftime("%b %d, %Y (%A)")

def reset_data():
    global data
    data = {"date": today_key()}

def ensure_today():
    global data
    if data.get("date") != today_key():
        reset_data()

def make_embed(last_action: str, quote: str, done=False):
    embed = discord.Embed(
        title="✨ 𝐸𝓃𝒹 𝑜𝒻 𝒟𝒶𝓎 𝑅𝑒𝓅𝑜𝓇𝓉 ✨",
        description=(
            f"📆 **{today_label()}**\n\n"
            f"**Last:** {last_action}\n\n"
            f"🟢 **In:** {data.get('in1','-')}\n"
            f"🟡 **Lunch:** {data.get('break','-')}\n"
            f"🟠 **Resume:** {data.get('in2','-')}\n"
            f"🔴 **Out:** {data.get('out','-')}\n\n"
            f"✨ _{quote}_"
        ),
        color=discord.Color.from_rgb(255, 182, 193)
    )
    embed.set_footer(text="Done for today 💗" if done else "Tap a button when ready")
    return embed

class Buttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 In", style=discord.ButtonStyle.success)
    async def btn_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_today()
        data["in1"] = now_time()
        embed = make_embed(f"🟢 IN — {data['in1']}", random.choice(IN_QUOTES))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🟡 Lunch", style=discord.ButtonStyle.secondary)
    async def btn_lunch(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_today()
        data["break"] = now_time()
        embed = make_embed(f"🟡 LUNCH — {data['break']}", random.choice(LUNCH_QUOTES))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🟠 Resume", style=discord.ButtonStyle.primary)
    async def btn_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_today()
        data["in2"] = now_time()
        embed = make_embed(f"🟠 RESUME — {data['in2']}", random.choice(RESUME_QUOTES))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔴 Out", style=discord.ButtonStyle.danger)
    async def btn_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_today()
        data["out"] = now_time()
        embed = make_embed(f"🔴 OUT — {data['out']}", random.choice(OUT_QUOTES), done=True)

        # Disable all except Reset
        for item in self.children:
            if item.label != "🔄 Reset":
                item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.secondary)
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        reset_data()
        for item in self.children:
            item.disabled = False

        embed = make_embed("Reset ✨", random.choice(RESET_QUOTES))
        await interaction.response.edit_message(embed=embed, view=self)

@bot.command(name="in")
async def in_cmd(ctx):
    reset_data()
    embed = make_embed("Ready ✨", "Tap a button to start.")
    await ctx.send(embed=embed, view=Buttons())

import os
bot.run(os.environ["DISCORD_TOKEN"])
