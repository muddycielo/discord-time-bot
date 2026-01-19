import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

# -------------------------
# PH TIME (UTC + 8) - reliable on Render
# -------------------------
PH_OFFSET = timedelta(hours=8)

def ph_now() -> datetime:
    return datetime.now(timezone.utc) + PH_OFFSET

def now_time() -> str:
    return ph_now().strftime("%I:%M %p")

def today_key() -> str:
    return ph_now().strftime("%Y-%m-%d")

def today_label() -> str:
    return ph_now().strftime("%b %d, %Y (%A)")

def tomorrow_key() -> str:
    return (ph_now() + timedelta(days=1)).strftime("%Y-%m-%d")

def tomorrow_label() -> str:
    return (ph_now() + timedelta(days=1)).strftime("%b %d, %Y (%A)")


# -------------------------
# Bot setup
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# records[user_id] = {"date": "YYYY-MM-DD", "in1": "...", "lunch": "...", "resume": "...", "out": "..."}
records: dict[int, dict] = {}

# Not-cringe Taglish lines
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
    "Fresh start tomorrow. Rest well, okay?",
    "Reset done. New day, new pace.",
    "Okay—tomorrow ulit. Pahinga na.",
]

def ensure_today(user_id: int) -> None:
    t = today_key()
    r = records.get(user_id)
    if not r or r.get("date") != t:
        records[user_id] = {"date": t}

def get_user_record(user_id: int) -> dict:
    ensure_today(user_id)
    return records[user_id]

def make_report_embed(user: discord.abc.User, date_text: str, r: dict, quote: str, done: bool) -> discord.Embed:
    embed = discord.Embed(
        title="✨ 𝐸𝓃𝒹 𝑜𝒻 𝒟𝒶𝓎 𝑅𝑒𝓅𝑜𝓇𝓉 ✨",
        description=(
            f"👤 **{user.display_name}**\n"
            f"📆 **{date_text}**\n\n"
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

def make_panel_embed(user: discord.abc.User, date_text: str) -> discord.Embed:
    embed = discord.Embed(
        title="✨ Time Panel",
        description=(
            f"👤 **{user.display_name}**\n"
            f"📆 **{date_text}**\n\n"
            f"Tap a button to log your time."
        ),
        color=discord.Color.from_rgb(255, 182, 193),
    )
    embed.set_footer(text="Tap a button when ready")
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

    @discord.ui.button(label="🟢 In", style=discord.ButtonStyle.success)
    async def btn_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["in1"] = now_time()
        embed = make_report_embed(interaction.user, today_label(), r, random.choice(IN_QUOTES), done=False)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="🟡 Lunch", style=discord.ButtonStyle.secondary)
    async def btn_lunch(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["lunch"] = now_time()
        embed = make_report_embed(interaction.user, today_label(), r, random.choice(LUNCH_QUOTES), done=False)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="🟠 Resume", style=discord.ButtonStyle.primary)
    async def btn_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["resume"] = now_time()
        embed = make_report_embed(interaction.user, today_label(), r, random.choice(RESUME_QUOTES), done=False)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="🔴 Out", style=discord.ButtonStyle.danger)
    async def btn_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        r = get_user_record(interaction.user.id)
        r["out"] = now_time()

        # After Out, keep panel but disable the log buttons (Reset stays available)
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label != "🔄 Reset":
                item.disabled = True

        embed = make_report_embed(interaction.user, today_label(), r, random.choice(OUT_QUOTES), done=True)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.secondary)
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        # 1) Send FINAL attendance as a NEW message (this stays forever)
        r = get_user_record(interaction.user.id).copy()
        final_embed = make_report_embed(
            interaction.user,
            today_label(),
            r,
            "Good job today! Don’t forget to rest 💕",
            done=True
        )
        await interaction.followup.send(embed=final_embed)

        # 2) Lock the OLD panel so it won't be changed again (keep it visible)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.edit_original_response(view=self)

        # 3) Create a NEW panel for next day (fresh buttons)
        records[interaction.user.id] = {"date": tomorrow_key()}
        await interaction.channel.send(
            embed=make_panel_embed(interaction.user, tomorrow_label()),
            view=Buttons(owner_id=interaction.user.id)
        )


@bot.command(name="in")
async def in_cmd(ctx: commands.Context):
    # Start/refresh today's panel for this user
    records[ctx.author.id] = {"date": today_key()}
    await ctx.send(
        embed=make_panel_embed(ctx.author, today_label()),
        view=Buttons(owner_id=ctx.author.id)
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | PH now: {now_time()} | {today_label()}")

bot.run(os.environ["DISCORD_TOKEN"])
