import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
from datetime import datetime, date, time, timedelta
import calendar

# Initialize the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message-based commands if also used
bot = commands.Bot(command_prefix='!', intents=intents)

schedules = []

# Decorators
def is_manager():
    async def predicate(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        conn = sqlite3.connect('tonbase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM server WHERE id = ?;", (guild_id,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("INSERT INTO server (id) VALUES (?);", (guild_id,))
            conn.commit()
        cursor.execute("SELECT role_id FROM allowed_roles WHERE server_id = ?;", (guild_id,))
        allowed_roles = cursor.fetchall()
        conn.close()
        verified = False
        for i in allowed_roles[0]:
            verified = i in [j.id for j in interaction.user.roles]
        return verified
    return app_commands.check(predicate)

def admin_only():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Commands to add and remove manager roles
@bot.command()
async def sync(ctx):
    print("sync command")
    if ctx.author.id == 382977855920930816:
        await bot.tree.sync()
        await ctx.send(f"Synced commands to the the servers!")
    else:
        await ctx.send('You must be the owner to use this command!')

@bot.tree.command(name="addrole", description="Adds a calendar manager role.")
@admin_only()
async def addrole(interaction: discord.Interaction, role: discord.Role):
    guild_id = interaction.guild_id
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM server WHERE id = ?;", (guild_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO server (id) VALUES (?);", (guild_id,))
    role_id = role.id
    cursor.execute("SELECT 1 FROM allowed_roles WHERE role_id = ?;", (role_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO allowed_roles (role_id, server_id) VALUES (?, ?);", (role_id, guild_id,))
    conn.commit()
    conn.close()
    await interaction.response.send_message("Added role named " + role.name + " with id " + str(role_id) + " to the list of calendar managers!")

@bot.tree.command(name="delrole", description="Removes a calendar manager role. Fails if specified role is not in the list.")
@admin_only()
async def delrole(interaction: discord.Interaction, role: discord.Role):
    guild_id = interaction.guild_id
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM server WHERE id = ?;", (guild_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO server (id) VALUES (?);", (guild_id,))
    role_id = role.id
    cursor.execute("SELECT 1 FROM allowed_roles WHERE role_id = ?;", (role_id,))
    result = cursor.fetchone()
    if result is not None:
        cursor.execute("DELETE FROM allowed_roles WHERE role_id = ?;", (role_id,))
    conn.commit()
    conn.close()
    await interaction.response.send_message("Removed role named " + role.name + " with id " + str(role_id) + " from the list of calendar managers!")

@bot.tree.command(name="managers", description="Lists all manager roles in this server.")
async def managers(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM server WHERE id = ?;", (guild_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO server (id) VALUES (?);", (guild_id,))
        conn.commit()
    cursor.execute("SELECT role_id FROM allowed_roles WHERE server_id = ?;", (guild_id,))
    allowed_roles = cursor.fetchall()
    conn.close()
    guild = interaction.guild
    message = ", ".join([guild.get_role(i[0]).name for i in allowed_roles])
    await interaction.response.send_message("The roles with permission to manage the calendar are " + message + ".")

@tasks.loop(minutes=1)
async def check_event():
    current_time = datetime.now()
    current_time = current_time.timestamp()
    for i in schedules:
        today = date.today()
        year_e = today.year
        month_e = today.month
        recurring = i[4]
        recurring_when = i[5]
        et = int(i[2])
        event_time = et # alias
        advertise_recurring = False
        inter = 604800
        if recurring:
            if recurring_when == 0:
                tmp = event_time%604800 # How many seconds into the week it is.
                recurring_ts = tmp

            elif recurring_when == 1:
                inter = 2629746
                tmp = event_time%2629746 # Yeah, you get it right? This time, month.
                recurring_ts = tmp
            first_of_month = datetime(year_e, month_e, 1)
            first_ts = first_of_month.timestamp()
            r_event_ts = [first_ts + recurring_ts + inter*i for i in range(4)] # Works well enough, overflows into outside the calendar when needed with no fallout.
            if int(first_ts)%inter > recurring_ts: # Detects if the first of the month is actually after the day of the week.
               r_event_ts.pop(0)
            for ts in r_event_ts:
                if abs(ts - current_time) <= 60:
                    advertise_recurring = True

        if abs(et - current_time) <= 60 or advertise_recurring:
            channel_id = i[-3]
            guild_id = i[-1]
            event_id = i[0]
            event_name = i[1]
            conn = sqlite3.connect("tonbase.db")
            cursor = conn.cursor()
            cursor.execute("SELECT ping_role FROM events WHERE id = ?", (event_id,))

            role_pings = "<@&"+str(cursor.fetchone()[0])+">"
            guild = bot.get_guild(guild_id)
            if guild is None:
                print("Guild not found.")
                return

            channel = guild.get_channel(channel_id)
            if channel is None:
                print("Channel not found.")
                return
            conn.close()
            await channel.send(f"Alert! The event \"{event_name}\" is about to start! {role_pings}")

# @bot.tree.command(name="check", description="Check the next event.")
# async def check(interaction : discord.Interaction):
#     await check_event()

@bot.tree.command(name="addevent", description="Adds an event to the list. Only usable by managers.")
@is_manager()
@app_commands.choices(recurring_when = [
    app_commands.Choice(name="Weekly", value=0), app_commands.Choice(name="Monthly", value=1)
])
async def add(interaction : discord.Interaction, cal_date : str, cal_time : str, channel : discord.TextChannel, role : discord.Role, recurring_when : app_commands.Choice[int], recurring : int, name : str = "Event", description : str = "Description.", image : str = ""):
    cal_date = [int(i) for i in cal_date.split("/")]
    date_obj = date(cal_date[2], cal_date[0], cal_date[1])
    cal_time = [int(i) for i in cal_time.split(":")]
    time_obj = time(cal_time[0], cal_time[1], 0)
    datetime_obj = datetime.combine(date_obj, time_obj)
    timestamp = datetime_obj.timestamp()
    host_id = int(interaction.user.id)
    guild_id = interaction.guild_id
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM server WHERE id = ?;", (guild_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO server (id) VALUES (?);", (guild_id,))
        conn.commit()
    cursor.execute("INSERT INTO events (name, time, host_id, recurring, recurring_when, description, image_url, notification_channel, ping_role, server_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, int(timestamp), host_id, recurring, recurring_when.value, description, image, channel.id, role.id, guild_id,))
    conn.commit()
    cursor.execute("SELECT * FROM events WHERE time = ?", (int(timestamp),))
    added_event = cursor.fetchone()
    schedules.append(added_event)
    conn.close()
    await interaction.response.send_message("Done! Created event.")

@bot.tree.command(name="calendar", description="Displays a calendar with events.")
@app_commands.describe(month="Pick a month to see the calendar.")
@app_commands.choices(month = [
    app_commands.Choice(name=calendar.month_name[i], value=i)
    for i in range(1, 13)
])
async def toncal(interaction : discord.Interaction, month : app_commands.Choice[int], year : int = 0):
    embed = discord.Embed(
        title=calendar.month_name[month.value],
        description=f"Welcome to the {calendar.month_name[month.value]} calendar for the Tonberry FC!",
        color=discord.Color.green()
    )
    today = date.today()
    if year == 0:
        year = today.year
    cal = calendar.TextCalendar(calendar.SUNDAY)
    cal_str = cal.formatmonth(year, month.value)
    guild_id = interaction.guild_id
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE server_id=?",(guild_id,))
    events = cursor.fetchall()
    min_time = 0
    min_diff = 9999999999999999999999999 # Messy? Blame Python
    min_name = ""
    for event in events:
        event_time = event[2]
        event_name = event[1]
        recurring = event[4]
        recurring_when = event[5] # This is a surprise tool that will help us later
        color = 32
        dt_obj = datetime.fromtimestamp(int(event_time))
        dt_now = datetime.now()
        ts_now = dt_now.timestamp()
        if abs(ts_now - event_time) < min_diff:
            min_diff = abs(ts_now - event_time)
            min_time = event_time
            min_name = event_name
        day_e = dt_obj.day
        month_e = dt_obj.month
        year_e = dt_obj.year
        recurring_ts = 0
        inter = 604800

        if month.value == month_e and year_e == year:
            index = cal_str.find("Su ")
            cal_str2 = cal_str[index::]
            cal_str2 = cal_str2.replace(" " + str(day_e) + " ", f" \u001b[4;{color}m{str(day_e)}\u001b[0m ", 1)
            cal_str = cal_str2

        if recurring:
            if recurring_when == 0:
                tmp = event_time%604800 # How many seconds into the week it is.
                recurring_ts = tmp

            elif recurring_when == 1:
                inter = 2629746
                tmp = event_time%2629746 # Yeah, you get it right? This time, month.
                recurring_ts = tmp
            first_of_month = datetime(year_e, month_e, 1)
            first_ts = first_of_month.timestamp()
            r_event_ts = [first_ts + recurring_ts + inter*i for i in range(4)] # Works well enough, overflows into outside the calendar when needed with no fallout.
            if int(first_ts)%inter > recurring_ts: # Detects if the first of the month is actually after the day of the week.
               r_event_ts.pop(0)
            r_event_dts = [datetime.fromtimestamp(int(i)) for i in r_event_ts]
            for i in r_event_dts:
                day = i.day
                cal_str = cal_str.replace(" " + str(day) + " ", f" \u001b[4;{color}m{str(day)}\u001b[0m ", 1)
            
        
    embed.set_image(url="https://img-9gag-fun.9cache.com/photo/a87V7Ne_460s.jpg") # Temporary image
    embed.add_field(name="Calendar (colored green = event in the day)", value=(f"```ansi\n{cal_str}\n```\n " + f" Next up:\n {min_name}, <t:{int(min_time)}:R>."))
    embed.set_footer(text="Brought to you by the Tonberries FC.")
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM server;")
    result = cursor.fetchone()
    if result is None:
        return
    cursor.execute("SELECT * FROM events;")
    global schedules # This is pain
    schedules += cursor.fetchall()
    conn.close()
    check_event.start()
    
f = open("secret.txt", "r")
token = f.read()

# Run the bot
bot.run(token)