import os
import random
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands

# Timezone fix (Asia/Manila = UTC+8)
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Manila")
except Exception:
    TZ = timezone(timedelta(hours=8))

def now_dt():
    return datetime.now(TZ)

def now_time() -> str:
    return now_dt().strftime("%I:%M %p")

def today_key() -> str:
    return now_dt().strftime("%Y-%m-%d")

def today_label() -> str:
    return now_dt().strftime("%b %d, %Y (%A)")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

records: dict[int, dict] = {}

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

def ensure_today(user_id: int) -> None:
    t = today_key()
    r = records.get(user_id)
    if not r or r.get("date") != t:
        records[user_id] = {"date": t}

def reset_user(user_id: int) -> None:
    records[user_id] = {"date": today_key()}

def get_user_record(user_id: int) -> dict:
    ensure_today(user_id)
    return records[user_id]

def make_embed(user: discord.abc.User, last_action: str, quote: str, done: bool = False) -> discord.Embed:
    r = get_user_record(user.id)
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
        color=discord.Color.from_rgb(255, 182, 193),
    )
    embed.set_footer(text="Done for today 💗" if done else "Tap a button when ready")
    return embed

class Buttons(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This panel isn’t yours 🙂 Type `!in` to make your own.",
                ephemeral=True
            )
            return False
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong. Try `!in` again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong. Try `!in` again.", ephemeral=True)
        except Exception:
            pass
        print("VIEW ERROR:", repr(error))

    @discord.ui.button(label="🟢 In", style=discord.ButtonStyle.success)
    async def btn_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["in1"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(interaction.user, f"🟢 IN — {r['in1']}", random.choice(IN_QUOTES)),
            view=self
        )

    @discord.ui.button(label="🟡 Lunch", style=discord.ButtonStyle.secondary)
    async def btn_lunch(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["lunch"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(interaction.user, f"🟡 LUNCH — {r['lunch']}", random.choice(LUNCH_QUOTES)),
            view=self
        )

    @discord.ui.button(label="🟠 Resume", style=discord.ButtonStyle.primary)
    async def btn_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["resume"] = now_time()
        await interaction.edit_original_response(
            embed=make_embed(interaction.user, f"🟠 RESUME — {r['resume']}", random.choice(RESUME_QUOTES)),
            view=self
        )

    @discord.ui.button(label="🔴 Out", style=discord.ButtonStyle.danger)
    async def btn_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["out"] = now_time()

        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label != "🔄 Reset":
                item.disabled = True

        await interaction.edit_original_response(
            embed=make_embed(interaction.user, f"🔴 OUT — {r['out']}", random.choice(OUT_QUOTES), done=True),
            view=self
        )

    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.secondary)
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        reset_user(interaction.user.id)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = False
        await interaction.edit_original_response(
            embed=make_embed(interaction.user, "Reset ✨", random.choice(RESET_QUOTES)),
            view=self
        )

@bot.command(name="in")
async def in_cmd(ctx: commands.Context):
    reset_user(ctx.author.id)
    await ctx.send(
        embed=make_embed(ctx.author, "Ready ✨", "Tap a button to start."),
        view=Buttons(owner_id=ctx.author.id)
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | timezone={TZ}")

bot.run(os.environ["DISCORD_TOKEN"])
