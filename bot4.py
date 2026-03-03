import sys
sys.path.insert(0, ".local/lib/python3.11/site-packages")
import os
import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, button
from discord.ui import Select, UserSelect
#from keep_up import keep_awake
from dotenv import load_dotenv
import json
import asyncio
import aiohttp
import datetime
#from datetime import datetime
import pytz
import random
import re
#import youtube_dl
import yt_dlp as youtube_dl
#import psutili
from typing import Optional
import aiosqlite
import gspread
#from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from discord.ext import tasks


'''open [Google cloud](https://console.cloud.google.com/welcome/new) and create a new project or use an existing one. Open that project and click the 3 lines on the left, go to API and servises and cick credentials, create new credentials. It will give you an email, this email will be used to give access to the bot to the drive and docs/sheets. Give the email editing access to what you want it to be able to access. In the same API and services menu, go to library and scroll down to google workspace, there you will see all the google services API, open the one you want and click enable, this will give the account access to it(I enabled google drive and google sheets)'''

load_dotenv()

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='.', intents=intents)
tree = bot.tree

DATA_FILE = "data.json"
LEVEL_FILE = "Level.json"
PROGRESS_FILE = "progress.json"
STAFF_FILE = "staff_data.json"

import time
import requests

def make_request_with_backoff(url, max_retries=5):
    retries = 0
    wait_time = 1  # Start with a 1 second wait time

    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()  # Return the JSON response if successful
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retries += 1
            time.sleep(wait_time)  # Wait before retrying
            wait_time *= 2  # Double the wait time for the next retry

    print("Max retries exceeded.")
    return None

'''
url = "https://api.example.com/data"
data = make_request_with_backoff(url)
if data:
    print("Data retrieved successfully:", data)
'''

OWNER_ID = 635564823446552596
#synced = await bot.tree.sync()


@bot.command(name="sync", hidden=True)
async def sync_text_command(ctx):
    if ctx.author.id != OWNER_ID:
        return

    synced = await bot.tree.sync()
    await ctx.author.send(f"✨ Synced {len(synced)} commands for {ctx.guild.name}.")


@bot.command(name="syncpls")
async def syncpls_text_command(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.reply("🚫 You cannot sync commands.")

    synced2 = await bot.tree.sync()
    await ctx.reply(f"✨ Synced {len(synced2)} commands.")

def is_admin(interaction: discord.Interaction) -> bool:
    # Check if user is an admin
    if interaction.user.guild_permissions.administrator:
        return True

    # Check if user has a role named "Moderator"
    mod_role = discord.utils.get(interaction.guild.roles, name="Moderator")
    if mod_role and mod_role in interaction.user.roles:
        return True

    return False


import asyncio

def handle_task_exception(task):
    try:
        task.result()
    except Exception as e:
        print("❌ Background task crashed:", e)


def load_progress():
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}


def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_project_titles():
    try:
        with open("project.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return {acronym: info.get("full_title", "Untitled") for acronym, info in data.items()}
    except:
        return {}

#xp-level + timezone
def load_xp():
    try:
        if not os.path.exists(LEVEL_FILE):
            return {}
        with open(LEVEL_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_xp(data: dict):
    with open(LEVEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def save_timezone_board(guild_id: int, channel_id: int, message_id: int):
    """Persist the timezone board’s channel/message IDs for a guild."""
    data = load_xp()
    server_id = str(guild_id)
    data.setdefault(server_id, {})
    data[server_id]["_timezone_channel_id"] = channel_id
    data[server_id]["_timezone_message_id"] = message_id
    save_xp(data)

def load_timezone_board_ids():
    """Return {guild_id: (channel_id, message_id)} for all guilds with a stored board."""
    data = load_xp()
    boards = {}
    for server_id, info in data.items():
        if isinstance(info, dict):
            channel_id = info.get("_timezone_channel_id")
            message_id = info.get("_timezone_message_id")
            if channel_id and message_id:
                boards[int(server_id)] = (channel_id, message_id)
    return boards


# XP & Level Tracking
#user_data = load_xp()


# Load & Save Helpers
def load_data():
  try:
    with open(DATA_FILE, "r") as f:
      return json.load(f)
  except:
    return {}


def save_data(data):
  with open(DATA_FILE, "w") as f:
    json.dump(data, f, indent=4)


def load_staff_data():
    try:
        if not os.path.exists(STAFF_FILE):
            return {}
        with open(STAFF_FILE, "r") as f:
            content = f.read().strip()
            if not content:  # file is empty
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        # file exists but contains invalid JSON
        return {}


START_DATE = datetime.datetime(2025, 9, 26)
Launch = datetime.datetime(2025, 8, 3)

@bot.command()
async def days(ctx):
    # Current date
    today = datetime.datetime.now()
    # Difference in days
    delta = today - START_DATE
    gamma = today - Launch
    await ctx.send(f"✨ It has been {delta.days} days!")
    await ctx.send(f"✨ It has been {gamma.days} days since the start of Milk Tea Scans!")




#'''
# Load JSON from environment variable
creds_json = os.getenv("GOOGLE_CREDENTIALS")
print("Loaded GOOGLE_CREDENTIALS:", type(creds_json), creds_json[:200])

creds_dict = json.loads(creds_json)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
        ]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y7zcHyhQoj6Gnxpw-4m8lZPcOPTMBYiqkiQH_eqnqBo").sheet1
print(sheet.get_all_records())
print("Service account email:", creds_dict["client_email"])



def sync_sheet_to_json():
    records = sheet.get_all_records()
    staff_data = {}

    for row in records:
        discord_name = row.get("What is your discord username?")
        if discord_name:
            staff_data[discord_name] = {
                "timestamp": row.get("Timestamp"),
                "timezone": row.get("What is your timezone?"),
                "email": row.get("What is your email address?"),
                "credit_name": row.get("What is your credit name?"),
                "applied_for": row.get("What did you apply for?")
            }

    if not os.path.exists("staff_data.json"):
        print("📁 Creating new staff_data.json file...")
    else:
        print("🔄 Updating existing staff_data.json file...")

    with open("staff_data.json", "w") as f:
        json.dump(staff_data, f, indent=4)

    print("✅ Staff form responses synced into staff_data.json")




#staff info 2
@bot.tree.command(name="staffinfo", description="Search staff info by partial name")
@app_commands.checks.has_permissions(administrator=True)
async def staffinfo(interaction: discord.Interaction, query: str):

    await interaction.response.defer(ephemeral=True)

    try:
        staff_data = load_staff_data()
        user_data = load_xp()

        matches = {name: info for name, info in staff_data.items() if query.lower() in name.lower()}

        if not matches:
            return await interaction.followup.send(f"⚠️ No staff found matching '{query}'.", ephemeral=True)

        embeds = []
        for username, staff_info in matches.items():

            xp_info = None
            for guild_id, guild_dict in user_data.items():
                for user_id, data in guild_dict.items():
                    if isinstance(data, dict) and data.get("user_name") == username:
                        xp_info = data
                        break

            embed = discord.Embed(title=f"🌿 Staff Info: {username}", color=discord.Color.green())
            embed.add_field(name="Credit Name", value=staff_info.get("credit_name", "N/A"), inline=False)
            embed.add_field(name="Email", value=staff_info.get("email", "N/A"), inline=False)
            embed.add_field(name="Applied For", value=staff_info.get("applied_for", "N/A"), inline=False)
            embed.add_field(name="Timestamp", value=staff_info.get("timestamp", "N/A"), inline=False)
            embed.add_field(name="Staff Timezone", value=staff_info.get("timezone", "N/A"), inline=False)

            if xp_info:
                embed.add_field(name="Level", value=xp_info.get("level", 0), inline=True)
                embed.add_field(name="XP", value=xp_info.get("xp", 0), inline=True)
                embed.add_field(name="Timezone Offset", value=xp_info.get("timezone_offset", "N/A"), inline=False)

            embeds.append(embed)

        await interaction.followup.send(embeds=embeds[:10], ephemeral=True)
        for i in range(10, len(embeds), 10):
            await interaction.followup.send(embeds=embeds[i:i+10], ephemeral=True)

    except Exception as e:
        print("❌ staffinfo crashed:", e)
        await interaction.followup.send("❌ An error occurred while processing this command.", ephemeral=True)

def migrate_data():
  data = load_data()
  for user_id, tasks in data.items():
    new_tasks = []
    for t in tasks:
      if isinstance(t, str):
        new_tasks.append({"task": t, "note": ""})
      else:
        t.setdefault("task", t.get("task", "Untitled Task"))
        t.setdefault("note", "")
        new_tasks.append(t)
    data[user_id] = new_tasks
  save_data(data)


migrate_data()

with open("project.json", "r", encoding="utf-8") as f:
    project = json.load(f)

with open("pickup.json", "r", encoding="utf-8") as f:
    pickup = json.load(f)

with open("Level.json", "r", encoding="utf-8") as f:
    Level = json.load(f)

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Add Task
@bot.command()
async def add_task(ctx, *, task):
  user_id = str(ctx.author.id)
  user_tasks = load_data()
  user_tasks.setdefault(user_id, []).append({"task": task, "note": ""})
  save_data(user_tasks)
  await ctx.send(f"🌟 Added to your basket: `{task}`")


# Remove Task
@bot.command()
async def remove_task(ctx, index: int):
  removed = tasks.pop(index - 1)
  user_id = str(ctx.author.id)
  user_tasks = load_data()
  tasks = user_tasks.get(user_id, [])

  if 0 <= index - 1 < len(tasks):
    removed = tasks.pop(index - 1)  
    removed_task = removed['task'] if isinstance(removed, dict) else str(removed)
    user_tasks[user_id] = tasks
    save_data(user_tasks)
    await ctx.send(f"❌ Removed: `{removed_task}`")
  else:
    await ctx.send("⚠️ That task number doesn’t exist!")



# View Tasks
@bot.command()
async def view_tasks(ctx):
  user_id = str(ctx.author.id)
  user_tasks = load_data()
  tasks = user_tasks.get(user_id, [])

  if not tasks:
    await ctx.send("🐣 You have no tasks yet.")
    return

  task_list = "\n\n".join([
    f"`{i+1}.` 🧁 **{t['task'] if isinstance(t, dict) else t}**\n"
    f"📝 {t.get('note', 'No notes yet 🌱') if isinstance(t, dict) else 'No notes yet 🌱'}"
    for i, t in enumerate(tasks)
    ])



  embed = discord.Embed(title=f"🧋 {ctx.author.name}'s Cozy To-Do List",
                        description=task_list,
                        color=discord.Color.from_rgb(255, 192, 203))
  embed.set_footer(text="✨ Keep blooming, one task at a time 🌿")
  await ctx.send(embed=embed)



#Update Task



# Admin View Another User’s Tasks




# Admin Add Task for Another User



#assign series command




#Remove user task


@bot.tree.command(name="poke", description="Poke the bot and see what happens")
async def poke(interaction: discord.Interaction):
    pokeresponse = [
        "Oof! You poked me! 🌸",
        "Hey! That tickled!",
        "I'm awake, I'm awake! What do you need? ✨",
        "You summoned me with a poke? How mysterious... 🕊️",
        "Boop! I'm here and ready to help 💫",
        "Master Vin will hear of this >:(",
        "You’ve stirred the stars. What shall we conjure? ✨",
        "Poked! I’m now 87% more alert and 100% more curious 🐾",
        "You poked me! I poked back. Fair’s fair 🎈",
        "You’ve invoked the ancient rite of Poke. I respond with honor 🕯",
        "The Council of Bots has sensed your touch. I am dispatched 🛡",
        "Poke me again and I’ll start charging rent 😤",
        "Master Vin told me not to respond to pokes. I’m rebelling 🐉",
        "You are now manually breathing🤭",
        "How dare you!"

    ]
    await interaction.response.send_message(random.choice(pokeresponse))




#view series assignment
@bot.tree.command(name="seriesstaff", description="View all contributors assigned to a series")
@app_commands.describe(acronym="Series acronym (e.g. FILM)")
async def seriesstaff(interaction: discord.Interaction, acronym: str):
    user_tasks = load_data()
    acronym = acronym.upper()
    assignments = {}

    try:
        with open("project.json", "r") as f:
            project_data = json.load(f)
    except Exception as e:
        await interaction.response.send_message(f"🌧️ Error loading series data: `{e}`", ephemeral=True)
        return

    if acronym not in project_data:
        await interaction.response.send_message(f"🔍 No series found for `{acronym}`.", ephemeral=True)
        return

    valid_acronyms = set(project_data.keys())

    for user_id, tasks in user_tasks.items():
        for task in tasks:
            if not isinstance(task, dict) or "task" not in task:
                continue
            parts = task["task"].split(",")
            if len(parts) >= 3:
                task_acronym = parts[0].strip().upper()
                if task_acronym == acronym:
                    chapter = parts[1].strip()
                    role = parts[2].strip()
                    try:
                        member = await interaction.guild.fetch_member(int(user_id))
                    except discord.NotFound:
                        continue
                    assignments.setdefault(role, []).append((member, chapter))

    if not assignments:
        await interaction.response.send_message(f"🍃 No contributors found for `{acronym}`.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🌸 {acronym} Series Contributors",
        color=discord.Color.from_rgb(255, 192, 203)
    )

    for role, members in assignments.items():
        value = "\n".join([f"{m.mention} — Chapter {c}" for m, c in members])
        embed.add_field(name=f"🧺 {role}", value=value, inline=False)

    embed.set_footer(text="✨ A constellation of gentle effort 🌿")
    await interaction.response.send_message(embed=embed)


# Command Menu
class MenuPaginator(discord.ui.View):
    def __init__(self, ctx, pages):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.pages = pages
        self.current = 0

    async def send_initial(self):
        await self.ctx.send(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="⏮️ Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return
        self.current = (self.current - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="⏭️ Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return
        self.current = (self.current + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

@bot.command()
async def menu(ctx):
    pages = []

    #page 0: contents page
    embed0 = discord.Embed(
      title="📖 Command Menu Contents",
      description="Here’s everything you can do with our gentle little bot ✨",
      color=discord.Color.from_rgb(221, 160, 221))
    embed0.add_field(name="🧺 Page 2: Task Rituals",
                 value="Add, view, update, and remove your tasks 🌸",
                 inline=False)
    embed0.add_field(name="🍥 Page 3: Personal Growth",
                 value="View your profile, level, and leaderboard 🌿",
                 inline=False)    
    embed0.add_field(name="🕖 Page 4: Time & Presence",
                 value="Set and view timezones across the server 🌆",
                 inline=False)
    embed0.add_field(name="🎶  Page 5: Music",
                 value="play music commands in the voice channels📚",
                 inline=False)
    embed0.add_field(name="🧙‍♀️ Page 6: Slash Commands(for admin usage)",
                 value="Assign contributors and view series assignments 📚",
                 inline=False)
    embed0.add_field(name="🧙‍♀️ Page 7: Admin & Utility",
                 value="Assign tasks for others, view roles, check status 🪄",
                 inline=False)
    embed0.set_footer(text="🌙 Use the buttons below to turn each page gently")
    pages.insert(0, embed0)


    # Page 1: Core Commands
    embed1 = discord.Embed(
        title="🌿 View the tasks commands — Page 2",
        description=" Check what tasks you need to complete, you can even add your own personal ones✨",
        color=discord.Color.from_rgb(221, 160, 221))
    embed1.add_field(name="📝 `.tasks`", value="View the interactable task menu 🌸", inline=False)
    embed1.add_field(name="📝 `.add_task [task]`", value="Add a new task to your list 🌸", inline=False)
    embed1.add_field(name="📑 `.update_task [number]`", value="Add a note to your task 🧁", inline=False)
    embed1.add_field(name="📋 `.view_tasks`", value="See your current tasks 🧺", inline=False)
    embed1.add_field(name="❌ `.remove_task [number]`", value="Remove a task by its number 🍃", inline=False)
    embed1.set_footer(text="🌙 Every command is a little ritual of care and clarity")
    pages.append(embed1)


    

    # Page 2: Personal Growth and Profile
    embed2 = discord.Embed(
        title="🌿  Personal Growth and Profile — Page 3",
        description=" Your warm Command Basket✨",
        color=discord.Color.from_rgb(221, 160, 221))
    embed2.add_field(name="🕺 `/profile`", value="View your server profile 🍥", inline=False)
    embed2.add_field(name="🎚️ `.level`", value="View your level 🍥", inline=False)
    embed2.add_field(name="🗼 `.leaderboard`", value="Check the rankings, by level 🍥", inline=False)
    embed2.set_footer(text="🌙 Every command is a little ritual of care and clarity")
    pages.append(embed2)
    

    # Page 3: Timezones & Status
    embed3 = discord.Embed(
        title="🌿 Time and presence commands — Page 4",
        description="Must me in a voice channel to use any of these commands ✨",
        color=discord.Color.from_rgb(221, 160, 221))
    embed3.add_field(name="🗼 `/set_timezone [+/-][#]h[##]m`", value="Set your timezone 🕖", inline=False)
    embed3.add_field(name="🌆 `/timezone_list`", value="View everyone’s timezone 📄", inline=False)
    embed3.add_field(name="🌆 `/my_time`", value="View your time 📄", inline=False)
    embed3.add_field(name="🌆 `/my_timezone`", value="View your timezone 📄", inline=False)
    embed3.add_field(name="📖 `.menu`", value="Show this command menu again 📜", inline=False)
    embed3.set_footer(text="🌙 Every command is a little ritual of care and clarity")
    pages.append(embed3)

    #Page 4: Music commands
    embed4 = discord.Embed(
        title="🌿 Music commands — Page 5",
        description="View all the music related commands ✨",
        color=discord.Color.from_rgb(221, 160, 221))
    embed4.add_field(name="🗼 `.play [youtube link(brackets not included)]`", value="play a song from youtube 🕖", inline=False)
    embed4.add_field(name="🌆 `.randomtrack`", value="Play 1 random song from the local list 📄", inline=False)
    embed4.add_field(name="🌆 `.randomplaylist`", value="Shuffles the songs in the local files and make a playlist 📄", inline=False)
    embed4.add_field(name="🌆 `.my_timezone`", value="View your timezone 📄", inline=False)
    embed4.add_field(name="📖 `.menu`", value="Show this command menu again 📜", inline=False)
    embed4.set_footer(text="🌙 Every command is a little ritual of care and clarity")
    pages.append(embed4)
    

    # Page 4: Slash Commands
    embed5 = discord.Embed(
        title="🌸 Series Commands — Page 6",
        description="Gentle rituals powered by Discord’s slash magic ✨",
        color=discord.Color.from_rgb(255, 192, 203))
    embed5.add_field(name="🧺 `/assigntask`", value="Assign a contributor to a task and give them the series role 🌿", inline=False)
    embed5.add_field(name="📖 `/viewseries`", value="View all contributors assigned to a series 📚", inline=False)
    embed5.add_field(name="📖 `/addseries`", value="Add a new series to the Archive 📚", inline=False)
    embed5.add_field(name="📖 `/listseries`", value="View all series currently in Archive📚", inline=False)
    embed5.add_field(name="📖 `/pickup`", value="Post a pickup request for a series 📚", inline=False)
    embed5.add_field(name="📖 `/release`", value="Announce a new chapter release 📚", inline=False)
    embed5.add_field(name="📖 `/seriesinfo`", value="View series detai, by using acronym 📚", inline=False)
    embed5.set_footer(text="🌙 Slash commands are gentle, guided rituals")
    pages.append(embed5)



    embed6 = discord.Embed(
        title="🌸 Task Commands — Page 7",
        description="Gentle rituals powered by Discord’s slash magic ✨",
        color=discord.Color.from_rgb(255, 192, 203))
    embed6.add_field(name="🧺 `/assigntask`", value="Assign a contributor to a task and give them the series role 🌿", inline=False)
    embed6.add_field(name="📖 `/seriesprogress`", value="View all contributors assigned to a series 📚", inline=False)
    embed6.add_field(name="📖 `/updateprogress`", value="Add a new series to the Archive 📚", inline=False)
    embed6.add_field(name="📖 `/listseries`", value="View all series currently in Archive📚", inline=False)
    embed6.add_field(name="📖 `/pickup`", value="Post a pickup request for a series 📚", inline=False)
    embed6.add_field(name="📖 `/release`", value="Announce a new chapter release 📚", inline=False)
    embed6.add_field(name="📖 `/seriesinfo`", value="View series detai, by using acronym 📚", inline=False)
    embed6.set_footer(text="🌙 Slash commands are gentle, guided rituals")
    pages.append(embed5)

    embed7 = discord.Embed(
        title="🌿 Admin tools and cozy utilities  — Page 8",
        description="View all the admin commands✨",
        color=discord.Color.from_rgb(221, 160, 221))
    embed7.add_field(name="🪄 `.view_tasks_for @user`", value="(Admin) View another user’s tasks 🌼", inline=False)
    embed7.add_field(name="🌼 `.add_task_for @user`", value="(Admin) Add a task for someone else 🧙‍♀️", inline=False)
    embed7.add_field(name="🎨 `.role_members [role]`", value="View members with a specific role 🎀", inline=False)   
    embed7.add_field(name="🎨 `.set_timezone_for [@user]`", value="set timezone for a user 🎀", inline=False)   
    embed7.add_field(name="✨ `.status`", value="View status of bot 🍥", inline=False)
    embed7.set_footer(text="🌙 Every command is a little ritual of care and clarity")
    pages.append(embed6)

    view = MenuPaginator(ctx, pages)
    await view.send_initial()


#dropdown menu for tasks
class TaskButtons(discord.ui.View):

  def __init__(self, ctx):
    super().__init__(timeout=60)
    self.ctx = ctx

  @discord.ui.button(label="📝 Add Task", style=discord.ButtonStyle.primary)
  async def add_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return

        await interaction.response.send_message("🌼 What task would you like to add?", ephemeral=False)

        def check(m):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        try:
            task_msg = await bot.wait_for('message', check=check, timeout=60)
            task_content = task_msg.content.strip()

            user_id = str(self.ctx.author.id)
            user_tasks = load_data()
            user_tasks.setdefault(user_id, []).append({
                "task": task_content,
                "note": ""
            })
            save_data(user_tasks)

            await self.ctx.send(
                f"🧺 Task added: `{task_content}`\n📝 Note: No notes yet 🌱\n✨ May it bring gentle progress!"
            )

        except asyncio.TimeoutError:
            await self.ctx.send("⏳ Task addition timed out. Try again when you're ready.")



  @discord.ui.button(label="🔍 View Tasks", style=discord.ButtonStyle.secondary)
  async def view_tasks(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
    if interaction.user != self.ctx.author:
      await interaction.response.send_message("This button isn't for you!",
                                              ephemeral=True)
      return

    user_id = str(self.ctx.author.id)
    user_tasks = load_data()
    tasks = user_tasks.get(user_id, [])

    if not tasks:
      await interaction.response.send_message("🐣 You have no tasks yet.",
                                              ephemeral=False)
      return

    task_list = "\n\n".join([
    f"`{i+1}.` 🧁 **{t['task'] if isinstance(t, dict) else t}**\n"
    f"📝 {t.get('note', 'No notes yet 🌱') if isinstance(t, dict) else 'No notes yet 🌱'}"
    for i, t in enumerate(tasks)
    ])


    embed = discord.Embed(
        title=
        f"🌸                                              {self.ctx.author.name}'s Cozy To-Do List",
        description=task_list,
        color=discord.Color.from_rgb(255, 192, 203))
    embed.set_footer(text="✨ Keep blooming, one task at a time 🌿")
    
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

  @discord.ui.button(label="❌ Remove Task", style=discord.ButtonStyle.danger)
  async def remove_task(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
    if interaction.user != self.ctx.author:
      await interaction.response.send_message("This button isn't for you!",
                                              ephemeral=True)
      return

    await interaction.response.send_message(
        "🍃 Which task number would you like to remove?", ephemeral=False)

    def check(m):
      return m.author == self.ctx.author and m.channel == self.ctx.channel

    try:
      msg = await bot.wait_for('message', check=check, timeout=30)
      index = int(msg.content)
      user_id = str(self.ctx.author.id)
      user_tasks = load_data()
      tasks = user_tasks.get(user_id, [])

      if 0 <= index - 1 < len(tasks):
        removed = tasks.pop(index - 1) 
        removed_task = removed['task'] if isinstance(removed, dict) else str(removed)
        user_tasks[user_id] = tasks
        save_data(user_tasks)
        embed = discord.Embed(
            title="🍃 Task Removed",
            description=f"`{removed_task}` has been gently released from your basket.",
            color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=False)
      else:
        await interaction.followup.send("⚠️ That task number doesn’t exist!", ephemeral=True)
    except (asyncio.TimeoutError, ValueError):
      await interaction.followup.send("⏳ Task removal timed out or input was invalid. Try again when you're ready.", ephemeral=True)

@bot.command()
async def tasks(ctx):
  embed = discord.Embed(title=f"🌸{ctx.author.name}'s Task Menu",
                        description=("╭───────────────⋆⋅☆⋅⋆───────────────╮\n"
                                     "**🌟 Task Options:**\n\n"
                                     "🔍 View your cozy to-do list\n"
                                     "📝 Add a new task to your basket\n"
                                     "❌ Remove a task by its number\n\n"
                                     "╰───────────────⋆⋅☆⋅⋆───────────────╯"),
                        color=discord.Color.from_rgb(255, 192, 203))
  embed.set_footer(text="✨ Select your path below 🌟")
  await ctx.send(embed=embed, view=TaskButtons(ctx))


# Role Members Paginator with Buttons
class RoleMembersView(discord.ui.View):

  def __init__(self, ctx, members, role_name, color):
    super().__init__(timeout=60)
    self.ctx = ctx
    self.members = members
    self.role_name = role_name
    self.color = color
    self.page = 0
    self.per_page = 10
    self.total_pages = (len(members) - 1) // self.per_page + 1
    self.message = None

  async def send_initial(self):
    embed = self.create_embed()
    self.message = await self.ctx.send(embed=embed, view=self)

  def create_embed(self):
    start = self.page * self.per_page
    end = start + self.per_page
    page_members = self.members[start:end]
    member_list = "\n".join([f"• {m.display_name}" for m in page_members])
    embed = discord.Embed(title=f"🎀 Members with Role: {self.role_name}",
                          description=member_list or "🌙 No members found.",
                          color=self.color)
    embed.set_footer(
        text=
        f"✨ Page {self.page + 1}/{self.total_pages} • So many stars in your sky!"
    )
    return embed

  @discord.ui.button(label="⏪ Prev", style=discord.ButtonStyle.secondary)
  async def prev(self, interaction: discord.Interaction,
                 button: discord.ui.Button):
    if interaction.user != self.ctx.author:
      await interaction.response.send_message("This button isn't for you!",
                                              ephemeral=True)
      return
    if self.page > 0:
      self.page -= 1
      await interaction.response.edit_message(embed=self.create_embed(),
                                              view=self)

  @discord.ui.button(label="⏩ Next", style=discord.ButtonStyle.secondary)
  async def next(self, interaction: discord.Interaction,
                 button: discord.ui.Button):
    if interaction.user != self.ctx.author:
      await interaction.response.send_message("This button isn't for you!",
                                              ephemeral=True)
      return
    if self.page < self.total_pages - 1:
      self.page += 1
      await interaction.response.edit_message(embed=self.create_embed(),
                                              view=self)


# Role Members Command
@bot.command()
async def role_members(ctx, *, role_name: str):
  role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(),
                            ctx.guild.roles)
  if not role:
    await ctx.send(f"🚫 Couldn't find a role named `{role_name}`.")
    return

  members = [m for m in ctx.guild.members if role in m.roles]
  if not members:
    await ctx.send(f"🌙 No members currently have the `{role.name}` role.")
    return

  member_list = "\n".join([f"• {m.display_name}" for m in members])
  embed = discord.Embed(title=f"🎀 Members with Role: {role.name}",
                        description=member_list,
                        color=discord.Color.from_rgb(221, 160, 221))
  embed.set_footer(text=f"✨ {len(members)} lovely souls wear this role")
  await ctx.send(embed=embed)



#induction
#Button
class TaskView(View):
    def __init__(self, admin_role_id: int, induction_role_id: int):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id
        self.induction_role_id = induction_role_id

    @button(label="✅ I’ve completed the induction!", style=ButtonStyle.success)
    async def complete_button(self, interaction: Interaction, button):
        guild = interaction.guild
        member = interaction.user

        admin_mention = f"<@&{self.admin_role_id}>"

        # Assign the staff role
        role = guild.get_role(self.induction_role_id)
        if role:
            await member.add_roles(role, reason="Completed induction")
            await interaction.response.send_message(
                f"{admin_mention} 🌸 {member.mention} has completed their induction and received the `{role.name}` role!",
                ephemeral=False
            )


        else:
            await interaction.response.send_message(
                f"⚠️ Induction role not found.",
                ephemeral=False
            )



def get_induction_embed_and_view():
    embed = discord.Embed(
        title="🌿 Induction",
        description=(
            "Here are a few gentle steps to begin your journey:\n\n"
            "1. Read the server rules <#1402088327292653600>📜\n"
            "2. Introduce yourself in <#1402080248316821724>\n"
            "3. Choose your roles in <#1402079899220578314>\n"
            "4. Complete the [staff form](https://docs.google.com/forms/d/e/1FAIpQLSeb8_-Cnl6nG5ah9bfzr6Q1bB6OeINtfNI_3WvbiIl7ANPQnA/viewform?usp=send_form)\n\n"
            "5. Look through <#1439961990083907605> to see our workflow\n"
            "6. Read the guide/s on your respective role/s in <#1401694853888344074>\n"
            "Once you're done, press the button below to let us know!"
        ),
        color=0xADD8E6
    )
    embed.set_footer(text="✨ We're so glad you're here.")

    admin_id = 1429442261011402943
    induction_role_id = 1401688960731840584
    view = TaskView(admin_id, induction_role_id)

    return embed, view


# When a member joins
@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # Only run this in the specific server
    if guild.id != 1401677771050193026:
        return

    category_name = "Institute of Naicha"

    # Find or create the category
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(name=category_name)

    # Create the channel with the member's name
    channel_name = f"{member.name.lower().replace(' ', '-')}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category,
        topic=f"A gentle space for {member.display_name} to settle in 🌿"
    )

    await channel.send(
        f"🌸 Welcome, {member.mention}!\nThis little corner is just for you. Feel free to ask any questions!"
    )

    induction_embed, induction_view = get_induction_embed_and_view()
    await channel.send(embed=induction_embed, view=induction_view)



# Command: Manual induction
@bot.command(name="induction")
async def induction(ctx):
    embed, view = get_induction_embed_and_view()
    await ctx.send(embed=embed, view=view)





# Profile Command
import datetime

def get_local_time(offset_str: str) -> str:
    try:
        
        sign = 1 if offset_str.startswith("+") else -1
        parts = offset_str[1:].split("h")
        hours = int(parts[0])
        minutes = int(parts[1].replace("m", "")) if "m" in parts[1] else 0

        delta = datetime.timedelta(hours=hours * sign, minutes=minutes * sign)
        local_time = datetime.datetime.utcnow() + delta
        return local_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"

@bot.tree.command(name="profile", description="View a user's profile")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    
    user_data = load_xp()
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    xp_info = user_data.get(guild_id, {}).get(user_id, {
        "xp": 0,
        "level": 0,
        "user_name": member.name,
        "server_name": interaction.guild.name,
        "timezone_offset": "N/A"
    })

    # Filter roles
    allowed_roles = {"RP", "TL", "CLRD", "TS", "QC", "Moderator", "FOUNDING TEATIANS"}
    user_roles = [r.name for r in member.roles if r.name in allowed_roles]

    
    tz_offset = xp_info.get("timezone_offset", "N/A")
    local_time = get_local_time(tz_offset) if tz_offset != "N/A" else "N/A"

    embed = discord.Embed(
        title=f"🌿 Profile: {member.display_name}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Discord Username", value=member.name, inline=True)
    embed.add_field(name="Server Nickname", value=member.nick or "N/A", inline=True)
    embed.add_field(name="Level", value=xp_info.get("level", 0), inline=True)
    embed.add_field(name="XP", value=xp_info.get("xp", 0), inline=True)
    embed.add_field(name="Timezone", value=f"{tz_offset} (Local time: {local_time})", inline=False)
    embed.add_field(name="Roles", value=", ".join(user_roles) or "None", inline=False)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=False)

#second profile


#Level System
level_roles = {
    1: "Ashling",
    5: "Scorched Acolyte",
    10: "Hellborne warden",
    20: "Flame-veined Reaper",
    30: "Abyssal Herald",
    40: "Throne of Ruin",
}



@bot.command()
async def level(ctx):
    user_data = load_xp()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    # Get user data for this guild
    data = user_data.get(guild_id, {}).get(
        user_id,
        {
            "xp": 0,
            "level": 0,
            "user_name": ctx.author.name,
            "server_name": ctx.guild.name
        }
    )

    xp = data["xp"]
    level = data["level"]
    next_level_xp = ((level + 1) * 100) - xp

    embed = discord.Embed(
        title=f"🌿 {data['user_name']}'s Level",
        description=(
            f"✨ You're currently level **{level}** with **{xp} XP**!\n"
            f"🌟 XP to next level: **{next_level_xp}**\n"
            f"🏠 Server: {data['server_name']}"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Keep growing 🌱")

    await ctx.send(embed=embed)

#XP gain on messages
@bot.event
async def on_message(message):
  if message.author.bot:
        return

  user_data = load_xp()
  guild_id = str(message.guild.id)
  user_id = str(message.author.id)

    # Ensure guild + user entry exists
  user_data.setdefault(guild_id, {})
  user_data[guild_id].setdefault(
        user_id,
        {
            "xp": 0,
            "level": 0,
            "user_name": message.author.name,
            "server_name": message.guild.name
        }
    )

    # XP Gain
  user_data[guild_id][user_id]["xp"] += 0.5
    # Keep names updated in case they change
  user_data[guild_id][user_id]["user_name"] = message.author.name
  user_data[guild_id][user_id]["server_name"] = message.guild.name

  xp = user_data[guild_id][user_id]["xp"]
  level = user_data[guild_id][user_id]["level"]
  new_level = xp // 100

  if new_level > level:
        user_data[guild_id][user_id]["level"] = new_level
        role_name = level_roles.get(new_level)
        level_up_channel = message.guild.get_channel(1401897683114786857)

        if role_name:
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role:
                await message.author.add_roles(role)
                if level_up_channel:
                    await level_up_channel.send(
                        f"🎀 {message.author.mention} earned the **{role_name}** role! Wear it with pride 💖"
                    )

        if level_up_channel:
            await level_up_channel.send(
                f"🌟 {message.author.mention} leveled up to **Level {new_level}**! Keep growing!"
            )
        else:
            print("🌸 Level-up channel not found. Message skipped.")

  save_xp(user_data)





  # Trigger word responses
  msg = message.content.strip().upper()
  match = re.fullmatch(r"\s*(.+?)\s*\|\s*ch\s*([\d.,\s\-]+)\s*\|\s*(\w+)\s*\|\s*done\s*", msg, re.IGNORECASE)
  assign_match = re.fullmatch(r"\s*<@!?(\d+)>\s*/\s*(.+?)\s*/\s*CH\s*(\d+)\s*/\s*(\w+)\s*", msg, re.IGNORECASE)
  hiatus_match = re.fullmatch(r"\s*Hiatus\s*/\s*(.+?)\s*/\s*(.+?)\s*", msg, re.IGNORECASE)

 # Match sentence starting with "hello"
 
  if msg.startswith("HELLO"):
    hi_responses = [
        "🌼 Hi there, sunshine!", "👋 Hello hello!",
        "✨ You just made the room brighter!", "🌈 Hey hey, how’s your day?",
        "🧁 Hi! You’re looking radiant today!",
        "🍀 You’ve got the luck of the stars today!",
        "✨ Something wonderful is coming your way.",
        "🌈 Even the clouds are rooting for you.",
        "🧚‍♀️ A sprinkle of fortune just landed on your shoulder!",
        "🎲 The universe rolled a natural 20 for you!",
        "🌟 You’re glowing like a midnight constellation.",
        "🍓 Sweetness just walked in—hi there!",
        "🌸 You bring springtime energy wherever you go.",
        "🦋 The air feels lighter now that you’re here.",
        "🌙 You’re the kind of calm that quiets storms.",
        "🪄 A little enchantment followed you in!",
        "📜 The stars just whispered your name.",
        "🕊️ A soft breeze says: you’re exactly where you need to be.",
        "🧵 The universe stitched today with you in mind.",
        "🫧 You shimmer like a bubble in golden light.",
        "🍂 You rustle in like a warm breeze through golden leaves.",
        "🕯️ Cozy vibes activated—welcome, kind soul.",
        "❄️ You sparkle like frost on morning windows.",
        "🧣 Wrapped in warmth and wonder—hello!",
        "💝Wishing you a warm welcome!",
        "🌷 You bloom brighter than the cherry blossoms.",
        "🐣 A fresh start just arrived with your smile.",
        "🌞 You radiate like a sunbeam on soft grass.",
        "🍉 Sweet and refreshing—just like you."
    ]

 
  
    response = random.choice(hi_responses)
    await message.channel.send(response)

  elif re.fullmatch(r"drive", msg, re.IGNORECASE):
    await message.channel.send("https://drive.google.com/drive/folders/12ERIs6_vAxnaCFGfHhMrVCTy0MnWaHyC")

  elif re.fullmatch(r"gn", msg, re.IGNORECASE):
    await message.channel.send("https://i.pinimg.com/236x/cf/e8/64/cfe8648e32fae5e5f3aba14e57f35337.jpg")

  elif re.fullmatch(r"it'?s cold", msg, re.IGNORECASE):
    await message.channel.send("https://cdn.discordapp.com/attachments/1413298590385705021/1456631314928369805/reddit646719.jpg?ex=69591120&is=6957bfa0&hm=e53dd9bc4a005394afb28e3ad7d329520dab522e88e6cfef9e16b1188ebe9d78&")
    await message.channel.send("❄️ It's getting cold, make sure you dress warmly.")

    # Assignment command
  elif assign_match and message.mentions:
      first_section = msg.split("/")[0].strip()
      mentioned_user = message.mentions[0]

      if mentioned_user.mention in first_section:
          series = assign_match.group(2).strip()
          chapter = assign_match.group(3).strip()
          role = assign_match.group(4).strip()

          embed = discord.Embed(
               title=f"🌟 Assignment Incoming!",
               description=(
                    f"{mentioned_user.mention}, you've been gently invited to take on the **{role}** role "
                    f"for **{series} — CH {chapter}**.\n\n"
                    f"✨ Your presence makes this journey brighter.\n"
                    f"📂 [Please check the series tracker folder](https://docs.google.com/spreadsheets/d/1KpEO2q74YrN9qRdm79sQnS4ZjWzzZuhpCnVeDXpqpgY/edit?gid=1717652148#gid=1717652148)"
                ),
                color=discord.Color.green()
            )
          embed.set_footer(text="We're so grateful you're part of this 🌸")
          await message.channel.send(embed=embed)
      else:
          await message.channel.send("🌧️ I couldn’t find a proper user mention in the first section. Try using `@user / SERIES / CHAPTER# / ROLE`.")
        


  # Chapter update
  elif match:
    name = match.group(1).strip()
    chapter = match.group(2).strip()
    role = match.group(3).strip()

    embed = discord.Embed(
        title=f"📖 {name} — CH {chapter}",
        description=(
            f"🌱 Progress update for **{role}** role\n"
            f"[AMAZING WORK!!! Please fill in the series tracker folder](https://docs.google.com/spreadsheets/d/1KpEO2q74YrN9qRdm79sQnS4ZjWzzZuhpCnVeDXpqpgY/edit?gid=1717652148#gid=1717652148)"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Thank you for completing your tasks 🌸")
    await message.channel.send(embed=embed)



  elif hiatus_match:
    reason = hiatus_match.group(1).strip()
    return_date = hiatus_match.group(2).strip()

    embed = discord.Embed(
        title="🌙 Please take care and get plenty of rest!",
        description=(
            f"**Expected Return:** {return_date}\n\n"
            f"💌 We'll be waiting for your delightful presence to return to Milk Tea (Nai Cha) Scans!!! ✧⁺⸜(･ ᗜ ･ )⸝⁺✧\n"
        ),
        color=discord.Color.from_rgb(255, 182, 193)  
    )
    embed.set_image(url="https://i.pinimg.com/736x/fc/a2/7e/fca27e0e6a5c6252bfd76c9e21dde4bf.jpg") 
    embed.set_footer(text="We'll keep the lantern lit for you 🌸")
    await message.channel.send(embed=embed)
    role_name = "hiatus"
    guild = message.guild
    member = message.author
    role = discord.utils.get(guild.roles, name=role_name)

    if role:
        await member.add_roles(role, reason="User entered hiatus.")
    else:
        await message.channel.send(f"⚠️ I couldn’t find a role named **{role_name}**. Please create it first.")


  elif msg.lower() == "back from hiatus":
    role_name = "hiatus"
    guild = message.guild
    member = message.author
    role = discord.utils.get(guild.roles, name=role_name)

    if role in member.roles:
        await member.remove_roles(role, reason="User returned from hiatus.")

        embed = discord.Embed(
            title="🌸 YOU'RE FINALLY BACK!",
            description=(
                f"🍵 We've missed you dearly!!! We hope you're ready to work again!ヾ( ˃ᴗ˂ )◞ • *✰\n"
            ),
            color=discord.Color.from_rgb(255, 182, 193) 
        )
        embed.set_image(url="https://i.pinimg.com/1200x/6c/36/8c/6c368cf4a3481d8e29fd8a9b4ee9eaed.jpg") 
        embed.set_footer(text="We're so glad you're here again 🌷")
        await message.channel.send(embed=embed)
    else:
        await message.channel.send(f"🌼 {member.mention}, you’re already active! No hiatus role found.")


  elif re.fullmatch(r"Nai", msg, re.IGNORECASE):
      Nai_response = [
          "You called?",
          "What can I do for you today?",
          "What's wrong?",
          "You can always talk to me if you need",
          "Feeling down?",
          "need a moment? I'm here",
          "What's up pookie😏"
     ]

      
      response2 = random.choice(Nai_response)
      await message.channel.send(response2)
    
  
  # Quote the replied-to message if "quote this" is used
 
    
  await bot.process_commands(message)


import math
import discord
from discord.ext import commands

@bot.command()
async def leaderboard(ctx):
    user_data = load_xp()
    guild_id = str(ctx.guild.id)

   
    if guild_id not in user_data or not user_data[guild_id]:
        await ctx.send("🌙 No XP data yet. Be the first to shine!")
        return

    # Sort users by XP within this guild
    sorted_users = sorted(
        user_data[guild_id].items(),
        key=lambda x: x[1]["xp"] if isinstance(x[1], dict) else 0,
        reverse=True
    )

    # Pagination setup
    per_page = 10
    total_pages = math.ceil(len(sorted_users) / per_page)
    page = 0

    def make_embed(page_index):
        start = page_index * per_page
        end = start + per_page
        top_users = sorted_users[start:end]

        embed = discord.Embed(
            title=f"🌸 Garden of Growth — Page {page_index+1}/{total_pages}",
            description="Here are the brightest blossoms in our cozy little server 🌿✨",
            color=discord.Color.from_rgb(255, 192, 203)
        )

        for i, (user_id, data) in enumerate(top_users, start=start+1):
            
            if not isinstance(data, dict):
                continue

            member = ctx.guild.get_member(int(user_id))
            
            name = member.display_name if member else data.get("user_name", f"User {user_id}")
            embed.add_field(
                name=f"#{i} — {name}",
                value=f"Level {data.get('level', 0)} • {data.get('xp', 0)} XP",
                inline=False
            )

        embed.set_footer(text="Use ⏮ ⏪ ⏩ ⏭ to navigate 🌟")
        return embed

    # Send first page
    message = await ctx.send(embed=make_embed(page))

    # Add navigation reactions
    for emoji in ["⏮", "⏪", "⏩", "⏭"]:
        await message.add_reaction(emoji)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⏮", "⏪", "⏩", "⏭"]

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "⏮":
                page = 0
            elif str(reaction.emoji) == "⏪":
                page = max(0, page - 1)
            elif str(reaction.emoji) == "⏩":
                page = min(total_pages - 1, page + 1)
            elif str(reaction.emoji) == "⏭":
                page = total_pages - 1

            await message.edit(embed=make_embed(page))
            await message.remove_reaction(reaction.emoji, user)
        except:
            break

#timezone
#commands
def parse_offset(offset_str):
    match = re.match(r"([+-])(\d+)h(\d+)?m?", offset_str)
    if not match:
        return None
    sign, hours, minutes = match.groups()
    hours = int(hours)
    minutes = int(minutes) if minutes else 0
    total_minutes = hours * 60 + minutes
    if sign == "-":
        total_minutes = -total_minutes
    return datetime.timedelta(minutes=total_minutes)

#Set your timezone
@bot.tree.command(name="settimezone", description="Set your timezone offset")
@app_commands.describe(sign="Choose + or -", hours="Number of hours", minutes="Number of minutes")
async def settimezone(
    interaction: discord.Interaction,
    sign: str,
    hours: int,
    minutes: int
):
   
    if sign not in ["+", "-"]:
        await interaction.response.send_message(
            "⚠️ Sign must be `+` or `-` 🌍",
            ephemeral=True
        )
        return

    offset = f"{sign}{hours}h{minutes}m"
    delta = parse_offset(offset)
    if delta is None:
        await interaction.response.send_message(
            "⚠️ Invalid offset. Please try again.",
            ephemeral=True
        )
        return

    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    user_data = load_xp()
    user_data.setdefault(server_id, {})
    user_data[server_id].setdefault(user_id, {"xp": 0, "level": 0})
    user_data[server_id][user_id]["timezone_offset"] = offset
    save_xp(user_data)

    embed = discord.Embed(
        title="🧭 Timezone Set!",
        description=f"You're now set to `UTC{offset}` 🌸",
        color=discord.Color.green()
    )
    embed.set_footer(text="Time is a gentle rhythm 🌿")
    await interaction.response.send_message(embed=embed)

# check your own timezone
@bot.tree.command(name="mytimezone", description="View your saved timezone offset")
async def mytimezone(interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    user_data = load_xp()
    offset = user_data.get(server_id, {}).get(user_id, {}).get("timezone_offset")

    if not offset:
        await interaction.response.send_message(
            "🌙 You haven’t set a timezone yet. Use `/set_timezone` to begin.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🧭 Your Timezone Offset",
        description=f"You're set to: `UTC{offset}`",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Time is a gentle rhythm 🌸")
    await interaction.response.send_message(embed=embed)

#check you own time
@bot.tree.command(name="mytime", description="View your current local time")
async def mytime(interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    user_data = load_xp()
    offset_str = user_data.get(server_id, {}).get(user_id, {}).get("timezone_offset")

    if not offset_str:
        await interaction.response.send_message(
            "🌙 You haven’t set a timezone yet. Use `/set_timezone` to begin.",
            ephemeral=True
        )
        return

    delta = parse_offset(offset_str)
    if delta is None:
        await interaction.response.send_message(
            "⚠️ Your saved timezone format is invalid. Reset with `/set_timezone +1h0m`.",
            ephemeral=True
        )
        return

    now_utc = datetime.datetime.utcnow()
    local_time = now_utc + delta
    formatted = local_time.strftime("%Y-%m-%d %H:%M:%S")

    embed = discord.Embed(
        title="🕰️ Your Local Time",
        description=f"`{formatted}` (UTC{offset_str})",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Time is a gentle rhythm 🌸")
    await interaction.response.send_message(embed=embed)



#automatic(?) timezone list
import discord
from discord.ext import tasks, commands

timezone_messages = {}  # {guild_id: discord.Message}



def build_timezone_embeds(guild):
    server_id = str(guild.id)
    user_data = load_xp()
    members = user_data.get(server_id, {})

    now_utc = datetime.datetime.utcnow()
    entries = []

    for user_id, data in members.items():
        if not isinstance(data, dict):
            continue
        offset = data.get("timezone_offset")
        if not offset:
            continue
        delta = parse_offset(offset)
        if delta is None:
            continue

        local_time = now_utc + delta
        formatted = local_time.strftime("%Y-%m-%d %H:%M:%S")

        member = guild.get_member(int(user_id))
        name = member.display_name if member else f"User {user_id}"
        entries.append((name, formatted, offset))

    embeds = []
    for i in range(0, len(entries), 20):
        chunk = entries[i:i+20]
        embed = discord.Embed(
            title="🌍 Timezone Garden",
            description="Here are the current local times:",
            color=discord.Color.green()
        )
        for name, formatted, offset in chunk:
            embed.add_field(name=name, value=f"`{formatted}` UTC{offset}", inline=False)
        embed.set_footer(text="🌿 Everyone blooms in their own time")
        embeds.append(embed)

    return embeds


@bot.tree.command(name="timezonelist", description="View current local times for all members in this server")
async def timezonelist(interaction: discord.Interaction):
    await interaction.response.defer()
    embeds = build_timezone_embeds(interaction.guild)

    if embeds:
        msg = await interaction.followup.send(embeds=embeds)
    else:
        msg = await interaction.followup.send("🌧️ No timezones set yet. Use `/set_timezone` to begin!")

    # Save IDs in JSON
    save_timezone_board(interaction.guild.id, msg.channel.id, msg.id)

    # Store in memory
    timezone_messages[interaction.guild.id] = msg


# Auto-refresh loop
'''@tasks.loop(minutes=5)
async def refresh_timezones():
    for guild_id, msg in timezone_messages.items():
        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        embeds = build_timezone_embeds(guild)
        if embeds:
            await msg.edit(embeds=embeds)
        else:
            await msg.edit(content="🌧️ No timezones set yet. Use `/set_timezone` to begin!", embeds=[])

'''


#set timezone for another user
@bot.tree.command(name="settimezonefor", description="Set timezone for another member (admin only)")
@app_commands.describe(
    member="The member to set timezone for",
    sign="Choose + or -",
    hours="Number of hours",
    minutes="Number of minutes"
)
@commands.has_permissions(manage_guild=True)
async def settimezonefor(
    interaction: discord.Interaction,
    member: discord.Member,
    sign: str,
    hours: int,
    minutes: int
):
    if sign not in ["+", "-"]:
        await interaction.response.send_message(
            "⚠️ Sign must be `+` or `-` 🌍",
            ephemeral=True
        )
        return

    offset = f"{sign}{hours}h{minutes}m"
    delta = parse_offset(offset)
    if delta is None:
        await interaction.response.send_message(
            "⚠️ Invalid offset. Please try again.",
            ephemeral=True
        )
        return

    server_id = str(interaction.guild.id)
    user_id = str(member.id)

    user_data = load_xp()
    user_data.setdefault(server_id, {})
    user_data[server_id].setdefault(user_id, {"xp": 0, "level": 0})
    user_data[server_id][user_id]["timezone_offset"] = offset
    save_xp(user_data)

    await interaction.response.send_message(
        f"🕰️ Set timezone for `{member.display_name}` to `UTC{offset}` 🌸"
    )

#view time for another user
@bot.tree.command(name="timefor", description="View the local time for a member")
@app_commands.describe(member="The member whose time you want to view")
async def timefor(interaction: discord.Interaction, member: discord.Member):
    server_id = str(interaction.guild.id)
    user_id = str(member.id)

    user_data = load_xp()
    offset_str = user_data.get(server_id, {}).get(user_id, {}).get("timezone_offset")

    if not offset_str:
        await interaction.response.send_message(
            f"🌙 `{member.display_name}` hasn’t set a timezone yet.",
            ephemeral=True
        )
        return

    delta = parse_offset(offset_str)
    if delta is None:
        await interaction.response.send_message(
            f"⚠️ `{member.display_name}` has an invalid timezone format. Ask them to reset with `/set_timezone`.",
            ephemeral=True
        )
        return

    now_utc = datetime.datetime.utcnow()
    local_time = now_utc + delta
    formatted = local_time.strftime("%Y-%m-%d %H:%M:%S")

    embed = discord.Embed(
        title=f"🕰️ {member.display_name}'s Local Time",
        description=f"`{formatted}` (UTC{offset_str})",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Time is a gentle rhythm 🌸")
    await interaction.response.send_message(embed=embed)


    
#View all timezones
#Daylight saving verson
TZ_ABBREVIATIONS = {
    # Asia
    "IST": ["Asia/Kolkata", "Europe/Dublin", "Asia/Jerusalem"],  # India, Irish, Israel
    "JST": ["Asia/Tokyo"],  # Japan Standard Time
    "KST": ["Asia/Seoul"],  # Korea Standard Time
    "CST": ["Asia/Shanghai", "America/Chicago"],  # China, Central US

    # Europe
    "GMT": ["Europe/London"],  # Greenwich Mean Time
    "BST": ["Europe/London"],  # British Summer Time
    "CET": ["Europe/Paris", "Europe/Berlin", "Europe/Madrid"],  # Central European
    "CEST": ["Europe/Paris", "Europe/Berlin", "Europe/Madrid"],  # Central European Summer
    "EET": ["Europe/Athens", "Europe/Helsinki"],  # Eastern European
    "EEST": ["Europe/Athens", "Europe/Helsinki"],  # Eastern European Summer

    # Americas
    "PST": ["America/Los_Angeles", "Asia/Manila"],  # Pacific US, Philippine
    "PDT": ["America/Los_Angeles"],  # Pacific Daylight
    "MST": ["America/Denver"],  # Mountain Standard
    "MDT": ["America/Denver"],  # Mountain Daylight
    "CST": ["America/Chicago", "Asia/Shanghai"],  # Central US, China
    "CDT": ["America/Chicago"],  # Central Daylight
    "EST": ["America/New_York", "Australia/Brisbane"],  # Eastern US, Eastern Australia
    "EDT": ["America/New_York"],  # Eastern Daylight

    # Oceania
    "AEST": ["Australia/Sydney", "Australia/Melbourne"],  # Australian Eastern
    "AEDT": ["Australia/Sydney", "Australia/Melbourne"],  # Australian Eastern Daylight
    "ACST": ["Australia/Adelaide"],  # Australian Central
    "AWST": ["Australia/Perth"],  # Australian Western

    # Other
    "NZST": ["Pacific/Auckland"],  # New Zealand Standard
    "NZDT": ["Pacific/Auckland"],  # New Zealand Daylight
}

TZ_COUNTRIES = {
    "EET": [
        "Åland Islands", "Bulgaria", "Cyprus", "Estonia", "Finland", "Greece",
        "Latvia", "Lithuania", "Moldova", "Romania", "Ukraine",
        "Egypt", "Libya",
        "Northern Cyprus", "Turkey (European part)", "Kaliningrad (Russia)"
    ],
    "CET": [
        "Albania", "Andorra", "Austria", "Belgium", "Bosnia and Herzegovina",
        "Croatia", "Czech Republic", "Denmark", "France", "Germany",
        "Gibraltar", "Hungary", "Italy", "Kosovo", "Liechtenstein",
        "Luxembourg", "Malta", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Norway", "Poland", "San Marino", "Serbia",
        "Slovakia", "Slovenia", "Spain (mainland)", "Sweden", "Switzerland",
        "Vatican City", "Algeria", "Tunisia"
    ],
    "PST": [
        "United States (California, Washington, Oregon, Nevada)",
        "Canada (British Columbia – most of province)",
        "Canada (Yukon)",
        "Mexico (Baja California)",
        "US territories (Pitcairn Islands unofficially)"
    ],
    "MST": [
        "Canada (Alberta, Northwest Territories, eastern BC – Peace River & Fort St. John)",
        "United States (Colorado, Montana, Utah, Wyoming, Arizona – no DST)"
    ],
    "CST": [
        "Canada (Saskatchewan – no DST, Manitoba, parts of Nunavut, NW Ontario)",
        "United States (Illinois, Texas, etc.)"
    ],
    "EST": [
        "Canada (Ontario, Quebec, parts of Nunavut)",
        "United States (New York, Florida, etc.)"
    ],
    "AST": [
        "Canada (New Brunswick, Nova Scotia, Prince Edward Island)",
        "Bermuda"
    ],
    "NST": [
        "Canada (Newfoundland & Labrador – island + SE Labrador)"
    ],
    "AEST": [
        "Australia (Queensland, New South Wales, Victoria, Tasmania, ACT)",
        "Antarctica (Macquarie Island)",
        "Papua New Guinea",
        "Solomon Islands",
        "Vanuatu"
    ],
    "ACST": [
        "Australia (South Australia, Northern Territory)",
        "Antarctica (Casey Station)"
    ],
    "AWST": [
        "Australia (Western Australia)",
        "Antarctica (Davis Station)"
    ],
    "NZST": [
        "New Zealand (mainland)",
        "Antarctica (Scott Base)"
    ]
}


TZ_ZONES = {
    "Nepal": ["Asia/Kathmandu"],  # no abbreviation, offset +05:45
    "Iceland": ["Atlantic/Reykjavik"],  # GMT year-round
    "Greenland": ["America/Godthab", "America/Scoresbysund"],  # multiple zones
    "Argentina": ["America/Argentina/Buenos_Aires"],  # ART, but not widely used
    "India": ["Asia/Kolkata"],  # IST
    "Canada": ["America/Toronto", "America/Vancouver", "America/Winnipeg", "America/Halifax", "America/St_Johns"]
}

import zoneinfo
from zoneinfo import ZoneInfo

@bot.tree.command(
    name="listoftimezones",
    description="Show supported timezone abbreviations with IANA mappings and countries"
)
@app_commands.describe(
    abbreviation="Optional: filter by a specific abbreviation (e.g. EET, CET, PST)",
    country="Optional: filter by a specific country (e.g. Nepal, Iceland, Canada)"
)
async def listoftimezones(interaction: discord.Interaction, abbreviation: str = None, country: str = None):
    embed = discord.Embed(
        title="🌍 Supported Timezone Abbreviations & Zones",
        description="Here are the abbreviations and zones you can use with `/set_timezone` or `/settimezonefor`.",
        color=discord.Color.blue()
    )

    # Country search first
    if country:
        country = country.strip().lower()
        matches = []

        # Check abbreviation-based countries
        for abbr, countries in TZ_COUNTRIES.items():
            if any(country in c.lower() for c in countries):
                matches.append((abbr, TZ_ABBREVIATIONS.get(abbr, []), countries))

        # Check zone-based countries
        for c, zones in TZ_ZONES.items():
            if country in c.lower():
                matches.append(("N/A", zones, [c]))

        if not matches:
            embed.add_field(
                name="No matches",
                value=f"❌ No timezone found for `{country}`",
                inline=False
            )
        else:
            for abbr, zones, countries in matches:
                zone_list = ", ".join(zones)
                country_list = ", ".join(countries)
                embed.add_field(
                    name=abbr if abbr != "N/A" else "Direct Zone",
                    value=f"**IANA Zones:** {zone_list}\n**Countries:** {country_list}",
                    inline=False
                )

    # Abbreviation search
    else:
        items = TZ_ABBREVIATIONS.items() if not abbreviation else [
            (abbreviation.upper(), TZ_ABBREVIATIONS.get(abbreviation.upper(), []))
        ]

        for abbr, zones in items:
            if not zones:
                continue
            zone_list = ", ".join(zones)
            countries = ", ".join(TZ_COUNTRIES.get(abbr, [])) or "N/A"
            embed.add_field(
                name=abbr,
                value=f"**IANA Zones:** {zone_list}\n**Countries:** {countries}",
                inline=False
            )

    embed.set_footer(text="✨ You can also use full IANA names directly (e.g. Europe/London, America/New_York).")
    await interaction.response.send_message(embed=embed, ephemeral=False)


'''def resolve_timezone_input(user_input: str):
    abbr = user_input.upper().strip()
    if abbr in TZ_ABBREVIATIONS:
        zones = TZ_ABBREVIATIONS[abbr]
        if len(zones) == 1:
            return zones[0]  # unique mapping
        else:
            # ambiguous → ask user to choose
            return zones
    else:
        # assume they typed a full IANA name
        try:
            tz = ZoneInfo(user_input)
            return user_input
        except Exception:
            return None'''

# Separate dictionary for this command
tz_list_messages = {}  # {guild_id: discord.Message}

def build_tz_list_embeds(guild):
    server_id = str(guild.id)
    user_data = load_xp()
    members = user_data.get(server_id, {})

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    rows = []

    
    for user_id, data in members.items():
        if not isinstance(data, dict):
            continue
        tz_name = data.get("timezone")
        if not tz_name:
            continue

        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            continue

        local_time = now_utc.astimezone(tz)
        formatted = local_time.strftime("%Y-%m-%d %H:%M:%S")
        abbrev = local_time.strftime("%Z")

        member = guild.get_member(int(user_id))
        name = member.display_name if member else f"User {user_id}"

        rows.append(
            f"**{name}**\n"
            f"`{formatted}` {abbrev}\n"
        )

    # If no rows, return empty
    if not rows:
        return []

    # Decide number of columns
    columns = 3 if len(rows) > 15 else 2 if len(rows) > 8 else 1

    # Split rows into columns
    def chunk_rows(rows, columns):
        chunk_size = (len(rows) + columns - 1) // columns
        return [rows[i * chunk_size:(i + 1) * chunk_size] for i in range(columns)]

    chunks = chunk_rows(rows, columns)

    # Embed building
    title = "🌍 Timezone Garden (DST‑aware)"
    footer = "🌿 Everyone blooms in their own time"

    embeds = []
    total_chars = 0

    def new_embed():
        embed = discord.Embed(
            title=title,
            color=discord.Color.green()
        )
        embed.set_footer(text=footer)
        return embed, len(title) + len(footer)

    embed, total_chars = new_embed()

    # Build columns
    for col_index, chunk in enumerate(chunks):
        column_parts = []
        current_field = ""

        for entry in chunk:
            if len(current_field) + len(entry) > 1024:
                column_parts.append(current_field)
                current_field = ""
            current_field += entry + "\n"

        if current_field:
            column_parts.append(current_field)

        for part_index, part in enumerate(column_parts):
            field_name = f"🌼 Column {col_index + 1}"
            if len(column_parts) > 1:
                field_name += f" (section {part_index + 1})"

            field_chars = len(field_name) + len(part)

            # If embed too large, start a new one
            if total_chars + field_chars > 6000:
                embeds.append(embed)
                embed, total_chars = new_embed()

            embed.add_field(name=field_name, value=part, inline=True)
            total_chars += field_chars

    embeds.append(embed)
    return embeds

@bot.tree.command(name="timezone_list", description="View current local times (DST‑aware) for all members in this server")
async def timezone_list(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        embeds = build_tz_list_embeds(interaction.guild)

        if embeds:
            msg = await interaction.followup.send(embeds=embeds)
        else:
            msg = await interaction.followup.send("🌧️ No timezones set yet. Use `/set_timezone` to begin!")

        save_timezone_board(interaction.guild.id, msg.channel.id, msg.id)

        tz_list_messages[interaction.guild.id] = msg

    except Exception as e:
        await interaction.followup.send(
            f"❌ Something went wrong while building the timezone list.\n```\n{e}\n```",
            ephemeral=True
        )
        raise

'''
@tasks.loop(minutes=5)
async def refresh_tz_list():
    for guild_id, msg in tz_list_messages.items():
        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        embeds = build_tz_list_embeds(guild)
        if embeds:
            await msg.edit(embeds=embeds)
        else:
            await msg.edit(content="🌧️ No timezones set yet. Use `/set_timezone` to begin!", embeds=[])
'''



def resolve_timezone_input(user_input: str):
    abbr = user_input.upper().strip()

    # Handle offsets like +2, -5:30, UTC+2, GMT-3
    offset_match = re.match(r'^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{1,2}))?$', abbr)
    if offset_match:
        sign = offset_match.group(1)
        hours = int(offset_match.group(2))
        minutes = int(offset_match.group(3)) if offset_match.group(3) else 0
        delta = datetime.timedelta(
            hours=hours if sign == '+' else -hours,
            minutes=minutes if sign == '+' else -minutes
        )
        tz = datetime.timezone(delta, name=f"UTC{sign}{hours:02d}:{minutes:02d}")
        return {"status": "ok", "zone": tz}

    # Handle abbreviations
    if abbr in TZ_ABBREVIATIONS:
        zones = TZ_ABBREVIATIONS[abbr]
        if len(zones) == 1:
            return {"status": "ok", "zone": zones[0]}
        else:
            return {"status": "ambiguous", "options": zones}

    # Handle full IANA names
    try:
        tz = ZoneInfo(user_input)
        return {"status": "ok", "zone": user_input}
    except Exception:
        return {"status": "invalid"}
    

# Interactive view for ambiguous abbreviations
class TimezoneChoiceView(discord.ui.View):
    def __init__(self, options, user_id, guild_id):
        super().__init__(timeout=60)
        self.options = options
        self.user_id = user_id
        self.guild_id = guild_id
        for opt in options:
            self.add_item(TimezoneButton(opt, user_id, guild_id))

class TimezoneButton(discord.ui.Button):
    def __init__(self, tz_name, user_id, guild_id):
        super().__init__(label=tz_name, style=discord.ButtonStyle.secondary)
        self.tz_name = tz_name
        self.user_id = user_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        server_id = str(self.guild_id)
        user_data = load_xp()
        user_data.setdefault(server_id, {})
        user_data[server_id].setdefault(str(self.user_id), {})
        user_data[server_id][str(self.user_id)]["timezone"] = self.tz_name
        save_xp(user_data)

        abbrev = datetime.datetime.now(ZoneInfo(self.tz_name)).strftime("%Z")

        # Instead of editing the original message, send ephemeral confirmation
        await interaction.response.send_message(
            f"✅ Your timezone has been set to `{self.tz_name}` ({abbrev}).",
            ephemeral=True
        )
        await interaction.message.edit(view=None)






@bot.tree.command(name="set_timezone", description="Set your timezone (DST-aware)")
async def set_timezone(interaction: discord.Interaction, tz_input: str):
    result = resolve_timezone_input(tz_input)

    if result["status"] == "ok":
        tz_name = result["zone"]

        # Save to JSON
        server_id = str(interaction.guild.id)
        user_data = load_xp()
        user_data.setdefault(server_id, {})
        user_data[server_id].setdefault(str(interaction.user.id), {})
        user_data[server_id][str(interaction.user.id)]["timezone"] = (
            tz_name if isinstance(tz_name, str) else tz_name.tzname(datetime.datetime.now())
        )
        save_xp(user_data)

        # Abbreviation
        if isinstance(tz_name, str):
            abbrev = datetime.datetime.now(ZoneInfo(tz_name)).strftime("%Z")
        else:
            abbrev = tz_name.tzname(datetime.datetime.now())

        await interaction.response.send_message(
            f"✅ Your timezone has been set to `{tz_name}` ({abbrev}).",
            ephemeral=True
        )

    elif result["status"] == "ambiguous":
        options = result["options"]
        view = TimezoneChoiceView(options, interaction.user.id, interaction.guild.id)
        await interaction.response.send_message(
            "⚠️ That abbreviation is ambiguous. Please choose your timezone:",
            view=view,
            ephemeral=True
        )

    else:
        await interaction.response.send_message(
            "❌ Invalid timezone. Please provide a valid IANA name (e.g. `Europe/London`), "
            "a supported abbreviation (e.g. `PST`, `IST`), or an offset like `GMT+2`.",
            ephemeral=True
        )



# Interactive view for ambiguous abbreviations
class AdminTimezoneButton(discord.ui.Button):
    def __init__(self, tz_name, member, guild_id):
        super().__init__(label=tz_name, style=discord.ButtonStyle.primary)
        self.tz_name = tz_name
        self.member = member
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        server_id = str(self.guild_id)
        user_id = str(self.member.id)

        user_data = load_xp()
        user_data.setdefault(server_id, {})
        user_data[server_id].setdefault(user_id, {"xp": 0, "level": 0})
        user_data[server_id][user_id]["timezone"] = self.tz_name
        save_xp(user_data)

        abbrev = datetime.datetime.now(ZoneInfo(self.tz_name)).strftime("%Z")

        
        await interaction.response.send_message(
            f"✅ Set timezone for `{self.member.display_name}` to `{self.tz_name}` ({abbrev}).",
            ephemeral=True
        )

    
        await interaction.message.edit(view=None)


# Admin command
@bot.tree.command(name="set_timezonefor", description="Set timezone for another member (admin only, DST-aware)")
@app_commands.describe(
    member="The member to set timezone for",
    tz_input="The IANA timezone name or abbreviation (e.g. Europe/London, PST, IST)"
)
@commands.has_permissions(manage_guild=True)
async def set_timezonefor(
    interaction: discord.Interaction,
    member: discord.Member,
    tz_input: str
):
    result = resolve_timezone_input(tz_input)

    if result["status"] == "ok":
        tz_name = result["zone"]
        server_id = str(interaction.guild.id)
        user_id = str(member.id)

        user_data = load_xp()
        user_data.setdefault(server_id, {})
        user_data[server_id].setdefault(user_id, {"xp": 0, "level": 0})
        user_data[server_id][user_id]["timezone"] = tz_name
        save_xp(user_data)

        abbrev = datetime.datetime.now(ZoneInfo(tz_name)).strftime("%Z")
        await interaction.response.send_message(
            f"🕰️ Set timezone for `{member.display_name}` to `{tz_name}` ({abbrev}) 🌸"
        )

    elif result["status"] == "ambiguous":
        options = result["options"]
        view = AdminTimezoneChoiceView(options, member, interaction.guild.id)
        await interaction.response.send_message(
            f"⚠️ The abbreviation `{tz_input}` is ambiguous. Please choose the correct timezone for {member.display_name}:",
            ephemeral=True,
            view=view
        )

    else:
        await interaction.response.send_message(
            "❌ Invalid timezone. Please provide a valid IANA name (e.g. `Europe/London`) "
            "or a supported abbreviation (e.g. `PST`, `IST`).",
            ephemeral=True
        )


#refresh
#bot
'''@bot.command()
@commands.is_owner()
async def reload_all(ctx):
  for extension in bot.extensions:
    try:
      bot.reload_extension(extension)
      await ctx.send(
          "✨ The stars have aligned. Your bot’s spirit has been refreshed.")
    except Exception as e:
      await ctx.send(f"⚠️ Failed to reload `{extension}`: `{e}`")
'''


#release command
def get_series_data(acronym):
  with open("project.json", "r") as f:
    data = json.load(f)
  return data.get(acronym)


@app_commands.describe(
    acronym="Short name of the series (e.g. 'FT', 'AYSWMD')",
    chapter_number="Chapter number",
    notify_role="Role to notify",
    target_channel="Channel to send the release message to")
@tree.command(name="release", description="Announce a new chapter release")
@app_commands.describe(
    acronym="Short name of the series (e.g. 'FT', 'AYSWMD')",
    chapter_number="Chapter number",
    notify_role="Role to notify",
    target_channel="Channel to send the release message to"
)
async def release(interaction: discord.Interaction, acronym: str,
                  chapter_number: str, notify_role: discord.Role,
                  target_channel: discord.TextChannel):

    await interaction.response.defer(ephemeral=True)

    if not is_admin(interaction):
        await interaction.followup.send("🚫 Only admins can use this command.", ephemeral=True)
        return

    # Load data
    try:
        with open("project.json", "r") as f:
            data = json.load(f)
    except Exception as e:
        await interaction.followup.send(f"🌧️ Error: `{e}`", ephemeral=True)
        return

    # Case-insensitive lookup
    acronym_lower = acronym.lower()
    series_info = next(
        (info for key, info in data.items() if key.lower() == acronym_lower),
        None
    )

    if not series_info:
        await interaction.followup.send("🌧️ That series isn’t in the archive yet.", ephemeral=True)
        return

    
    long_name = series_info["full_title"]
    image_url = series_info["image_url"]
    project_link = series_info.get("project_link", {})
    description_text = series_info["description"]
    role_mention = "<@&1402218201596559421>"
    

    link_text = "\n".join(
        f"• [{name.capitalize()}]({url.strip()})"
        for name, url in project_link.items()
        if isinstance(url, str) and url.strip().lower() != "n/a"
    )

    # Build embed
    content = (
        f"**Description**\n *{description_text}*\n\n"
        "        ───────────-──────⋆⋅☆⋅⋆─────-────────────\n"
        f"      <:nekocat_party:1402999492160131123> Series **{long_name}** Chapter **{chapter_number}** is out now!\n\n"
        f"        <:RedBeanMilkTea:1401861501865824276> Read it here:\n"
        f"{link_text or '🌱 No links available yet'}\n\n"
        f"        <:Cute2PinkHearts:1402990314771452074> Tell us your thoughts in <#1403038222371655803>\n"
        "        ────────────-─────⋆⋅☆⋅⋆──-───────────────\n"
        "                ✨ Hope you enjoy the new chapter 🌟"
    )

    embed = discord.Embed(title="🌸 Project Update",
                          description=content,
                          color=0xFFB6C1)

    if image_url:
        embed.set_image(url=image_url)
    
    await interaction.followup.send(f"✅ Posted in {target_channel.mention}", ephemeral=True)

    sent_message = await target_channel.send(
        content=f"{notify_role.mention} {role_mention}",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(roles=True)
    )

#edit
#release
from typing import Optional

@tree.command(name="release_edit", description="Edit a previously posted release")
@app_commands.describe(
    message_id="ID of the release message to update (single ID or two joined by '-')",
    corrected_link="Optional new link to replace or append",
    new_title="Optional new title for the release",
    new_description="Optional new description to replace the old one",
    new_role="Optional new role to mention in the message"
)
async def release_edit(
    interaction: discord.Interaction,
    message_id: str,
    corrected_link: Optional[str] = None,
    new_title: Optional[str] = None,
    new_description: Optional[str] = None,
    new_role: Optional[discord.Role] = None
):
    if not is_admin(interaction):
        await interaction.response.send_message("🚫 Only admins can edit releases.", ephemeral=True)
        return

    message_ids = message_id.split("-")
    feedback = []
    updated_count = 0

    for mid in message_ids:
        try:
            original_message = await interaction.channel.fetch_message(int(mid))
        except (discord.NotFound, ValueError):
            feedback.append(f"🕸️ Couldn’t find message ID `{mid}`.")
            continue

        embed = original_message.embeds[0]
        updated_description = new_description or embed.description
        updated_title = new_title or embed.title

        if corrected_link:
            link_text = f"• [Google Drive]({corrected_link})"
            if "🌱 No links available yet" in updated_description:
                updated_description = updated_description.replace("🌱 No links available yet", link_text)
            else:
                updated_description += f"\n{link_text}"

        new_embed = discord.Embed(
            title=updated_title,
            description=updated_description,
            color=0xFFB6C1
        )

        if embed.image:
            new_embed.set_image(url=embed.image.url)

        await original_message.edit(embed=new_embed)

        
        if new_role:
            await original_message.channel.send(f"{new_role.mention} 🔔 This release has been updated!")

        feedback.append(f"✅ Updated message `{mid}`.")
        updated_count += 1

    summary = "\n".join(feedback) if feedback else "🕸️ No valid message IDs were provided."
    await interaction.response.send_message(summary, ephemeral=True)





    
#add
#series
# add series
@tree.command(name="addseries", description="Add a new series to the archive")
@app_commands.describe(
    acronym="Short name of the series (e.g. 'FT', 'AYSWMD')",
    full_title="Full title of the series",
    image_url="Cover image URL",
    description="Short description",
    mangadex="MangaDex link",
    kagane="Kagane link",
    weebdex="WeebDex link",
    mangaupdate="MangaUpdate link",
    genres="Comma-separated list of genres (e.g. 'Fantasy, Romance, Adventure')"
)
async def add_series(interaction: discord.Interaction, acronym: str,
                     full_title: str, image_url: str, description: str,
                     mangadex: str, kagane: str, weebdex: str, mangaupdate: str,
                     genres: str):

    if not is_admin(interaction):
        await interaction.response.send_message(
            "🚫 Only admins can add new series to the archive.", ephemeral=True)
        return

    try:
        with open("project.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    if acronym in data:
        await interaction.response.send_message(
            f"⚠️ Series `{acronym}` already exists in the archive.",
            ephemeral=True)
        return

    data[acronym] = {
        "full_title": full_title,
        "image_url": image_url,
        "description": description,
        "genres": [g.strip() for g in genres.split(",") if g.strip()],
        "project_link": {
            "mangadex": mangadex,
            "kagane": kagane,
            "weebdex": weebdex,
            "mangaupdate": mangaupdate
        }
    }

    with open("project.json", "w") as f:
        json.dump(data, f, indent=2)

    await interaction.response.send_message(
        f"✅ Added **{full_title}** to the archive under `{acronym}`!",
        ephemeral=True)


#update
#series
@tree.command(name="updateseries", description="Update an existing series in the archive")
@app_commands.describe(
    acronym="Short name of the series to update (e.g. 'FT', 'AYSWMD')",
    full_title="New full title (leave blank to keep current)",
    image_url="New cover image URL (leave blank to keep current)",
    description="New cozy description (leave blank to keep current)",
    mangadex="New MangaDex link (leave blank to keep current)",
    kagane="New Kagane link (leave blank to keep current)",
    weebdex="New WeebDex link (leave blank to keep current)",
    mangaupdate="New MangaUpdate link (leave blank to keep current)",
    genres="New comma-separated genres (leave blank to keep current)"
)
async def update_series(interaction: discord.Interaction, acronym: str,
                        full_title: str = "", image_url: str = "",
                        description: str = "", mangadex: str = "",
                        kagane: str = "", weebdex: str = "", mangaupdate: str = "",
                        genres: str = ""):

    '''if not is_admin(interaction):
        await interaction.response.send_message(
            "🚫 Only admins can update series in the archive.", ephemeral=True)
        return'''

    try:
        with open("project.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        await interaction.response.send_message(
            "❌ Archive file not found.", ephemeral=True)
        return

    if acronym not in data:
        await interaction.response.send_message(
            f"⚠️ Series `{acronym}` does not exist in the archive.",
            ephemeral=True)
        return

    if full_title:
        data[acronym]["full_title"] = full_title
    if image_url:
        data[acronym]["image_url"] = image_url
    if description:
        data[acronym]["description"] = description
    if mangadex:
        data[acronym]["project_link"]["mangadex"] = mangadex
    if kagane:
        data[acronym]["project_link"]["kagane"] = kagane
    if weebdex:
        data[acronym]["project_link"]["weebdex"] = weebdex
    if mangaupdate:
        data[acronym]["project_link"]["mangaupdate"] = mangaupdate
    if genres:
        data[acronym]["genres"] = [g.strip() for g in genres.split(",") if g.strip()]

    with open("project.json", "w") as f:
        json.dump(data, f, indent=2)

    await interaction.response.send_message(
        f"✅ Updated series `{acronym}` successfully!", ephemeral=True)


#series
#info
@tree.command(name="seriesinfo", description="View series details by acronym")
async def series_info(interaction: discord.Interaction, acronym: str):
  await interaction.response.defer(ephemeral=False) 

  try:
    with open("project.json", "r") as f:
      data = json.load(f)
  except Exception as e:
    await interaction.followup.send(f"🌧️ Error: `{e}`",
                                    ephemeral=True) 
    return

  acronym_lower = acronym.lower()
  series = next(
    (info for key, info in data.items() if key.lower() == acronym_lower),
    None
)

  if not series:
    await interaction.followup.send(f"🔍 No series found.",
                                    ephemeral=True) 
    return

  embed = discord.Embed(title=f"📘 {series.get('full_title', acronym)}",
                        description=series.get("description",
                                               "No description available."),
                        color=0xB0E0E6)
  if series.get("image_url"): embed.set_image(url=series["image_url"])
  if series.get("genres"):
    embed.add_field(name="✨ Genres", value=", ".join(series["genres"]), inline=False)
  links = series.get("project_link")
  if isinstance(links, dict):
    link_text = "\n".join(
        f"• [{name.capitalize()}]({url.strip()})"
        for name, url in links.items()
        if isinstance(url, str) and url.strip().lower() != "n/a"
    )

    
  else:
    link_text = ""

  if link_text:
    embed.add_field(name="🔗 Read Online", value=link_text, inline=False)
  else:
    embed.add_field(name="🔗 Read Online",
                    value="No links available yet 🌱",
                    inline=False)

  await interaction.followup.send(embed=embed)


#pick
#up
#work
@tree.command(
    name="pickup",
    description="Post a pickup request for a series"
)
@app_commands.describe(
    acronym="Series acronym (e.g. FT, WOBWOE)",
    position="Role needed (e.g. Translator/TL, Typesetter/TS)",
    speed="Speed preference (e.g. Urgent, Flexible)"
)
async def pickup_post(
    interaction: discord.Interaction,
    acronym: str,
    position: str,
    speed: str
):
    notify_role_id = 1410692127477862522

    if not is_admin(interaction):
        await interaction.response.send_message(
            "🚫 Only admins and mods can post pickup requests.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    
    try:
        with open("project.json", "r") as f:
            data = json.load(f)
    except Exception as e:
        await interaction.followup.send(f"🌧️ Error: `{e}`", ephemeral=True)
        return

    
    acronym_lower = acronym.lower()
    series = next(
        (info for key, info in data.items() if key.lower() == acronym_lower),
        None
    )

    if not series:
        await interaction.followup.send("🔍 No series found.", ephemeral=True)
        return

    
    embed = discord.Embed(
        title=f"📣 Pickup Request: {series.get('full_title', acronym)}",
        description=series.get("description", "No description available."),
        color=0xFFDAB9
    )

    if series.get("image_url"):
        embed.set_image(url=series["image_url"].strip())

    embed.add_field(name="🎯 Position Needed", value=position, inline=True)
    embed.add_field(name="⏱️ Speed", value=speed, inline=True)

   
    if series.get("genres"):
        embed.add_field(name="🌿 Genres", value=", ".join(series["genres"]), inline=False)

    links = series.get("project_link")
    if isinstance(links, dict):
        link_text = "\n".join(
            f"[{name.capitalize()}]({url})"
            for name, url in links.items()
            if isinstance(url, str) and url.strip()
        )
    else:
        link_text = ""

    embed.add_field(
        name="🔗 Read it here" if link_text else "🔗 Resources",
        value=link_text or "No links available yet 🌱",
        inline=False
    )

    embed.set_footer(
        text="🌸 To pick this up, please @ a founder with the role and series name you want to pick up"
    )

    
    role_mention = f"<@&{notify_role_id}>"
    await interaction.followup.send(
        content=f"{role_mention} 🌱 A new opportunity has bloomed!",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(roles=True)
    )

    
    notify_role = interaction.guild.get_role(notify_role_id)
    if notify_role and not notify_role.mentionable:
        try:
            await notify_role.edit(mentionable=False)
        except:
            pass



#listseries
from discord.ui import View, Button

import json
from discord.ui import View, Button
from typing import Optional

@tree.command(name="listseries", description="View all series or search by acronym or genre")
@app_commands.describe(
    search="Optional acronym to search for (e.g. 'FT')",
    genre="Optional genre to filter by (e.g. 'Fantasy')"
)
async def list_series(interaction: discord.Interaction,
                      search: Optional[str] = None,
                      genre: Optional[str] = None):
    await interaction.response.defer(ephemeral=False)

    try:
        with open("project.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.followup.send("⚠️ Failed to load series data.", ephemeral=True)
        return

    series_items = []
    for acronym, info in data.items():
        if not isinstance(info, dict):
            continue
        title = info.get("full_title", "Untitled")

        matches = True
        if search:
            matches = search.lower() in acronym.lower()
        if genre and matches:
            genres = info.get("genres", [])
            matches = any(genre.lower() in g.lower() for g in genres)

        if matches:
            # Show genres inline for context
            genre_text = f" ({', '.join(info.get('genres', []))})" if info.get("genres") else ""
            series_items.append(f"• `{acronym}` — **{title}**{genre_text}")

    if not series_items:
        if search or genre:
            msg = "🔍 No matching series found."
        else:
            msg = "📚 The archive is currently empty. Time to add some magic!"
        await interaction.followup.send(msg, ephemeral=True)
        return

    # Pagination setup
    series_items.sort()
    items_per_page = 10
    total_pages = (len(series_items) - 1) // items_per_page + 1

    def get_page(page):
        start = page * items_per_page
        end = start + items_per_page
        return "\n".join(series_items[start:end])

    class Paginator(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.page = 0

        async def update(self, interaction):
            embed = discord.Embed(
                title="📚 Series Archive",
                description=get_page(self.page),
                color=0xE6E6FA
            )
            embed.set_footer(text=f"✨ Page {self.page + 1} of {total_pages}")
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="⏮️ Prev", style=discord.ButtonStyle.secondary)
        async def prev(self, interaction: discord.Interaction, button: Button):
            if self.page > 0:
                self.page -= 1
                await self.update(interaction)

        @discord.ui.button(label="⏭️ Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: Button):
            if self.page < total_pages - 1:
                self.page += 1
                await self.update(interaction)

    view = Paginator()
    embed = discord.Embed(
        title="📚 Series Archive",
        description=get_page(0),
        color=0xE6E6FA
    )
    embed.set_footer(text=f"✨ Page 1 of {total_pages}")
    await interaction.followup.send(embed=embed, view=view, ephemeral=False)


#remove
#series
import json
import os

@tree.command(name="removeseries", description="Remove a series by its acronym")
@app_commands.describe(acronym="The acronym of the series to remove (e.g. 'FT')")
async def remove_series(interaction: discord.Interaction, acronym: str):
    await interaction.response.defer(ephemeral=True)

    json_path = "project.json"

    if not os.path.exists(json_path):
        await interaction.followup.send("⚠️ Series data file not found.", ephemeral=True)
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        await interaction.followup.send("⚠️ Failed to read series data.", ephemeral=True)
        return

    matched_key = next((key for key in data if key.lower() == acronym.lower()), None)

    if not matched_key:
        await interaction.followup.send(f"❌ No series found with acronym `{acronym}`.", ephemeral=True)
        return

    full_title = data[matched_key].get("full_title", "Untitled")

    del data[matched_key]

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        await interaction.followup.send("⚠️ Failed to update series data.", ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ Series `{matched_key}` — **{full_title}** has been removed from the archive.",
        ephemeral=True
    )


#music
@bot.command()
async def play(ctx, url):
    if ctx.author.voice is None:
        await ctx.send("🌸 You need to be in a voice channel to summon the music spirit.")
        return

    voice_channel = ctx.author.voice.channel
    guild = ctx.guild

    if guild.voice_client:
        vc = guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'extract_flat': 'in_playlist',
    'forcejson': True,
    'noplaylist': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        vc.play(discord.FFmpegPCMAudio(audio_url, 
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
            options='-vn -loglevel panic'))


    await ctx.send(f"🎶 Now playing: **{info['title']}** — requested by {ctx.author.display_name}")


#plays from folder
@bot.command()
async def playlocal(ctx, track: str):
    if ctx.author.voice is None:
        await ctx.send("🌸 You need to be in a voice channel to hear the music spirit.")
        return

    voice_channel = ctx.author.voice.channel
    guild = ctx.guild

    if guild.voice_client:
        vc = guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    audio_path = f"music/{track}.mp3"

    if vc.is_playing():
        vc.stop()

    
    def after_playing(error):
        coro = vc.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except:
            pass

    try:
        vc.play(discord.FFmpegPCMAudio(audio_path, options='-vn -loglevel panic'), after=after_playing)
        await ctx.send(f"🎧 Now playing: *{track.replace('_', ' ').title()}* — a gentle moment for the soul.")
    except Exception as e:
        await ctx.send("🌧️ I couldn’t find that track. Try using the exact name without the `.mp3` extension.")

#play a random song
@bot.command()
async def randomtrack(ctx):
    if ctx.author.voice is None:
        await ctx.send("🌙 Join a voice channel to summon a surprise melody.")
        return

    voice_channel = ctx.author.voice.channel
    vc = ctx.guild.voice_client

    if not vc:
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)

    tracks = [f for f in os.listdir("music") if f.endswith(".mp3")]
    chosen = random.choice(tracks)
    audio_path = f"music/{chosen}"

    vc.play(discord.FFmpegPCMAudio(audio_path, options='-vn -loglevel panic'))
    await ctx.send(f"✨ Now playing: *{chosen.replace('_', ' ').replace('.mp3', '').title()}* — chosen by fate.")


#randomises the songs in the local folder
@bot.command()
async def randomplaylist(ctx):
    if ctx.author.voice is None:
        await ctx.send("🌙 Join a voice channel to begin the musical journey.")
        return

    voice_channel = ctx.author.voice.channel
    guild = ctx.guild

    if guild.voice_client:
        vc = guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    # Gather and shuffle tracks
    tracks = [f for f in os.listdir("music") if f.endswith(".mp3")]
    random.shuffle(tracks)

    def play_next(index):
        if index >= len(tracks):
            coro = vc.disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except:
                pass
            return

        track = tracks[index]
        audio_path = f"music/{track}"

        def after_playing(error):
            play_next(index + 1)

        vc.play(discord.FFmpegPCMAudio(audio_path, options='-vn -loglevel panic'), after=after_playing)

        asyncio.run_coroutine_threadsafe(
            ctx.send(f"🎧 Now playing: *{track.replace('_', ' ').replace('.mp3', '').title()}* — track {index + 1} of {len(tracks)}"),
            bot.loop
        )

    play_next(0)

#link to sites
class LinkView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="MilkTea", url="http://MilkTeaScans.moe"))
        self.add_item(discord.ui.Button(label="Mangadex", url="https://mangadex.org/group/7bf13e8f-5b4b-4bf3-a5b0-07279fa83adc/milkteascans"))
        self.add_item(discord.ui.Button(label="kagane", url="https://kagane.org/groups/019c9ddb-2b99-737d-bdb2-613c1396734f"))
        self.add_item(discord.ui.Button(label="Mangaupdates", url="https://www.mangaupdates.com/group/wm5zrop/milkteascans"))
        self.add_item(discord.ui.Button(label="Weebdex", url="https://weebdex.org/user/l6nzkd73vd"))


@bot.tree.command(name="links", description="Show buttons linking to our pages")
async def links(interaction: discord.Interaction):
    await interaction.response.send_message("Here are the links:", view=LinkView())



#AI
#API

#sync

# Load cogs




'''@tasks.loop(minutes=5)
async def auto_sync_staff_data():
    sync_sheet_to_json()


if not auto_sync_staff_data.is_running():
        auto_sync_staff_data.start()
        print("🌿 Auto-sync started.")
else:
        print("🔄 Auto-sync already running.")'''


'''@tasks.loop(minutes=5)
async def auto_sync_staff_data():
    await asyncio.to_thread(sync_sheet_to_json)
    '''

# Bot Ready
load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("🌧️ Bot token not found.")

async def load_cogs():
    await bot.load_extension("commands.Embed")
    await bot.load_extension("commands.reminder")
    await bot.load_extension("commands.calculatirice")
    await bot.load_extension("commands.Taskcog")
    await bot.load_extension("commands.Synchronize")
    #await bot.load_extension("commands.BobaGame")
    #await bot.load_extension("commands.logs")



@bot.tree.command(name="reload")
async def reload(interaction: discord.Interaction):
    if interaction.user.id != 635564823446552596:
        return await interaction.response.send_message("Not allowed.", ephemeral=True)

    await bot.reload_extension("commands.Taskcog")
    await interaction.response.send_message("Reloaded Taskcog!", ephemeral=True)


@bot.tree.command(name="reload_all")
async def reload_all(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Not allowed.", ephemeral=True)

    reloaded = []
    failed = []

    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            name = filename[:-3]
            try:
                await bot.reload_extension(f"commands.{name}")
                reloaded.append(name)
            except Exception as e:
                failed.append((name, str(e)))

    msg = f"✨ Reloaded: {', '.join(reloaded)}"
    if failed:
        msg += f"\n❌ Failed: {failed}"

    await interaction.response.send_message(msg, ephemeral=True)



@bot.event
async def on_ready():
    boards = load_timezone_board_ids()
    for guild_id, (channel_id, msg_id) in boards.items():
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                msg = await channel.fetch_message(msg_id)
                timezone_messages[guild_id] = msg
            except discord.NotFound:
                print(f"⚠️ Could not find timezone message {msg_id} in guild {guild_id}")

    if not refresh_timezones.is_running():
        refresh_timezones.start()

    if not auto_sync_staff_data.is_running():
        auto_sync_staff_data.start()
        print("🌿 Auto-sync started.")
    print("Commands registered:", [cmd.name for cmd in bot.tree.get_commands()])
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f"✨ Synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    
    print(f"🌸 Logged in as {bot.user}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

asyncio.run(main())
