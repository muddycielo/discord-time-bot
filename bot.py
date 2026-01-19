import os
import random
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands


# -------------------------
# FORCE PHILIPPINES TIME (UTC+8)
# -------------------------
TZ = timezone(timedelta(hours=8))

def now_dt():
    return datetime.now(TZ)

def now_time():
    return now_dt().strftime("%I:%M %p")

def today_key():
    return now_dt().strftime("%Y-%m-%d")

def today_label():
    return now_dt().strftime("%b %d, %Y (%A)")


# -------------------------
# Bot setup
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# records[user_id] = daily data
records = {}


# -------------------------
# Not-cringe Taglish messages
# -------------------------
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
    "Reset done. Take it easy.",
    "Fresh start ulit. No pressure.",
    "Okay—back to zero. Slow lang.",
]


# -------------------------
# Helpers
# -------------------------
def ensure_today(user_id):
    if user_id not in records or records[user_id].get("date") != today_key():
        records[user_id] = {"date": today_key()}

def reset_user(user_id):
    records[user_id] = {"date": today_key()}

def make_embed(user, last_action, quote, done=False):
    r = records[user.id]

    embed = discord.Embed(
        title="✨ 𝐸𝓃𝒹 𝑜𝒻 𝒟𝒶𝓎 𝑅𝑒𝓅𝑜𝓇𝓉 ✨",
        description=(
            f"👤 **{user.display_name}**\n"
            f"📆 **{today_label()}**\n\n"
            f"**Last:** {last_action}\n\n"
            f"🟢 **In:** {r.get('in1','-')}\n"
            f"🟡 **Lunch:** {r.get('lunch','-')}\n"
            f"🟠 **Resume:** {r.get('resume','-')}\n"
            f"🔴 **Out:** {r.get('out','-')}\n\n"
            f"✨ _{quote}_"
        ),
        color=discord.Color.from_rgb(255, 182, 193)
    )

    embed.set_footer(text="Done for today 💗" if done else "Tap a button when ready")
    return embed


# -------------------------
# Buttons
# -------------------------
class Buttons(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This panel isn’t yours 🙂 Type `!in` to make your own.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🟢 In", style=discord.ButtonStyle.success)
    async def in_btn(self, interaction, button):
        await interaction.response.defer()
        ensure_today(interaction.user.id)
        records[interaction.user.id]["in1"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(
                interaction.user,
                f"🟢 IN — {records[interaction.user.id]['in1']}",
                random.choice(IN_QUOTES)
            ),
            view=self
        )

    @discord.ui.button(label="🟡 Lunch", style=discord.ButtonStyle.secondary)
    async def lunch_btn(self, interaction, button):
        await interaction.response.defer()
        ensure_today(interaction.user.id)
        records[interaction.user.id]["lunch"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(
                interaction.user,
                f"🟡 LUNCH — {records[interaction.user.id]['lunch']}",
                random.choice(LUNCH_QUOTES)
            ),
            view=self
        )

    @discord.ui.button(label="🟠 Resume", style=discord.ButtonStyle.primary)
    async def resume_btn(self, interaction, button):
        await interaction.response.defer()
        ensure_today(interaction.user.id)
        records[interaction.user.id]["resume"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(
                interaction.user,
                f"🟠 RESUME — {records[interaction.user.id]['resume']}",
                random.choice(RESUME_QUOTES)
            ),
            view=self
        )

    @discord.ui.button(label="🔴 Out", style=discord.ButtonStyle.danger)
    async def out_btn(self, interaction, button):
        await interaction.response.defer()
        ensure_today(interaction.user.id)
        records[interaction.user.id]["out"] = now_time()

        for item in self.children:
            if item.label != "🔄 Reset":
                item.disabled = True

        await interaction.edit_original_response(
            embed=make_embed(
                interaction.user,
                f"🔴 OUT — {records[interaction.user.id]['out']}",
                random.choice(OUT_QUOTES),
                done=True
            ),
            view=self
        )

    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.secondary)
    async def reset_btn(self, interaction, button):
        await interaction.response.defer()
        reset_user(interaction.user.id)

        for item in self.children:
            item.disabled = False

        await interaction.edit_original_response(
            embed=make_embed(
                interaction.user,
                "Reset ✨",
                random.choice(RESET_QUOTES)
            ),
            view=self
        )


# -------------------------
# Command
# -------------------------
@bot.command(name="in")
async def in_cmd(ctx):
    reset_user(ctx.author.id)
    await ctx.send(
        embed=make_embed(ctx.author, "Ready ✨", "Tap a button to start."),
        view=Buttons(owner_id=ctx.author.id)
    )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Timezone UTC+8")


# -------------------------
# Run (Render)
# -------------------------
bot.run(os.environ["DISCORD_TOKEN"])
