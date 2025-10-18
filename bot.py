import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, View
import sqlite3
from datetime import datetime, date, time, timedelta
import calendar

# Initialize the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message-based commands if also used
bot = commands.Bot(command_prefix='!', intents=intents)

schedules = []

calendar_pictures = [
    "https://media.discordapp.net/attachments/1425681011844583504/1425685212620390490/FINAL_FANTASY_XIV_Online_20250918161915.jpg?ex=68e87c52&is=68e72ad2&hm=394027395f7ac689f631f0969e6e763abe99eb52b45facee55c122656dd06374&=&format=webp&width=1707&height=960", # Jan, Sozin
    "https://media.discordapp.net/attachments/1425681011844583504/1425685270875082782/FINAL_FANTASY_XIV_Online_20250921075851.jpg?ex=68e87c60&is=68e72ae0&hm=4e60cd914fd71eaabc54573ebe06dc3474186dbe88881efc9bcc68bd28c27e48&=&format=webp&width=1707&height=960", # Feb, Fia and Combop
    "https://media.discordapp.net/attachments/1425681011844583504/1425685066130001981/FINAL_FANTASY_XIV_Online_20250906122140.jpg?ex=68e87c2f&is=68e72aaf&hm=3a4794780592a5d1abd5b5d59da69e1abeaa4a4977cc492200c2b2f4b22e276f&=&format=webp&width=1707&height=960", # March, Cyclops
    "https://media.discordapp.net/attachments/1425681011844583504/1425684983229579304/FINAL_FANTASY_XIV_Online_20250824181954.jpg?ex=68e87c1b&is=68e72a9b&hm=d3b8e4b56e4eb65ae8f7b58c351fdd7bce47dc24e77019b40356446c0ddca199&=&format=webp&width=1707&height=960", # April, Eliza
    "https://media.discordapp.net/attachments/1425681011844583504/1425685026603008110/FINAL_FANTASY_XIV_Online_20250830234855.jpg?ex=68e87c26&is=68e72aa6&hm=6218e1bcc35b4c8a5bffd6e40fec4c1e252cc03c5404d24acbd8d5c2a6159401&=&format=webp&width=1707&height=960", # May, Freyja
    "https://media.discordapp.net/attachments/1425681011844583504/1425684945476780133/FINAL_FANTASY_XIV_Online_20250824175607.jpg?ex=68e87c12&is=68e72a92&hm=0d8e35b410bb99bd002df0b84cdd73ef0f767b851a5dfc9158f1bd2e6fff70a7&=&format=webp&width=1707&height=960", # June, Sorrell
    "https://media.discordapp.net/attachments/1425681011844583504/1425684903063978066/FINAL_FANTASY_XIV_Online_20250821114329.jpg?ex=68e87c08&is=68e72a88&hm=dc538f6d3af21e306caae53035fcb14f31cb994eb1ab0e9a186ce39cfa0ce4b2&=&format=webp&width=1707&height=960", # July, Gemini
    "https://media.discordapp.net/attachments/1425681011844583504/1425685153921105980/FINAL_FANTASY_XIV_Online_20250907163853.jpg?ex=68e87c44&is=68e72ac4&hm=29edaa771e68880f9b48f7b8fc3ceb8acdfe19ad1f5ae47854c8bb35f8445365&=&format=webp&width=1707&height=960", # August, Sorivian
    "https://media.discordapp.net/attachments/1425681011844583504/1425685111185342475/FINAL_FANTASY_XIV_Online_20250906123148.jpg?ex=68e87c3a&is=68e72aba&hm=920368f71ecf9a37f76733360c7ac16bf85437e85a8a0f935b9a9d806f13164e&=&format=webp&width=1707&height=960", # September, Scorpio
    "https://media.discordapp.net/attachments/1425681011844583504/1425685312146772050/FINAL_FANTASY_XIV_Online_20250921075929.jpg?ex=68e87c6a&is=68e72aea&hm=3a0ab9b748ac5fd7d0936387dcfba972a72053e376855b85f64fd2c3af5fa789&=&format=webp&width=1707&height=960", # October, Pigy
    "https://media.discordapp.net/attachments/1425681011844583504/1425684856452419664/FINAL_FANTASY_XIV_Online_20250821070524.jpg?ex=68e87bfd&is=68e72a7d&hm=cbd103d010b5b06a22c27d60b4e47a5bde3969ebd7a5f539e794c210897f0ee0&=&format=webp&width=1707&height=960", # November, Yealand
    "https://media.discordapp.net/attachments/1425681011844583504/1425823701835710627/FINAL_FANTASY_XIV_Online_20251009071251.jpg?ex=68e8fd4d&is=68e7abcd&hm=caa259e92fc3b3c44aadfab67d2892d8b20dba2f939d494c4773d99579ef4db7&=&format=webp&width=1707&height=960" # December, Cook
]

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
        timezone = int(i[7]) + 3
        et = int(i[2])
        et -= timezone*3600 # Minus is more... yeah, timezones.
        event_time = et # alias
        advertise_recurring = False
        inter = 604800
        dt_obj = datetime.fromtimestamp(et)
        if recurring:
            day_of_week = dt_obj.weekday() # Day of the week the event takes place
            day_of_month = dt_obj.day # Day of month event takes place
            if recurring_when == 0:
                tmp = event_time%604800 # How many seconds into the week it is.
                recurring_ts = tmp
            elif recurring_when == 1:
                inter = 2629746
                tmp = event_time%2629746 # Yeah, you get it right? This time, month.
                recurring_ts = tmp
            first_of_month = datetime(year_e, month_e, 1)
            first_ts = first_of_month.timestamp()
            r_event_ts = [first_ts + recurring_ts + inter*i for i in range(5)] # Works well enough, overflows into outside the calendar when needed with no fallout.
            # if int(first_ts)%inter > recurring_ts: # Detects if the first of the month is actually after the day of the week.
            #    print(recurring_ts)
            #    print(int(first_ts)%inter)
            #    r_event_ts.pop(0)
            r_event_dts = [datetime.fromtimestamp(int(i)) for i in r_event_ts]
            previous = 0
            print(day_of_week)
            print(day_of_month)
            for i in r_event_dts:
                day = i.day
                if recurring_when == 0:
                    diff = day_of_week - i.weekday()
                    # diff += diff/abs(diff)

                    i = datetime.fromtimestamp(i.timestamp() + diff*86400)
                    print("Old weekday", i.weekday())
                    day = i.day
                    print("New weekday", i.weekday())
                    print("Expected ", day_of_week)
                elif recurring_when == 1:
                    day = day_of_month
            for ts in r_event_dts:
                if abs(ts.timestamp() - current_time) <= 60:
                    advertise_recurring = True

        if (abs(et - current_time) <= 60 and et < current_time) or advertise_recurring:
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

@bot.tree.command(name="addevent", description="Adds an event to the list. Only usable by managers. Default timezone is GMT-3.")
@is_manager()
@app_commands.choices(recurring_when = [
    app_commands.Choice(name="Weekly", value=0), app_commands.Choice(name="Monthly", value=1)
])
async def add(interaction : discord.Interaction, cal_date : str, cal_time : str, channel : discord.TextChannel, role : discord.Role, recurring_when : app_commands.Choice[int], recurring : bool, name : str = "Event", description : str = "Description.", timezone : int = -3):
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
    cursor.execute("INSERT INTO events (name, time, host_id, recurring, recurring_when, description, timezone, notification_channel, ping_role, server_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, int(timestamp), host_id, recurring, recurring_when.value, description, timezone, channel.id, role.id, guild_id,))
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
        description=f"Welcome to the {calendar.month_name[month.value]} calendar for the Tonberry FC! Timezone displayed is GMT-3.",
        color=discord.Color.green()
    )
    today = date.today()
    if year == 0:
        year = today.year
    cal = calendar.TextCalendar(calendar.SUNDAY)
    cal_str = cal.formatmonth(year, month.value)
    index = cal_str.find("Su ")
    cal_str = cal_str[index::]
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
        timezone = event[7] + 3
        event_time -= timezone*3600 # Minus is more... yeah, timezones.
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
            cal_str = cal_str.replace(str(day_e), f"\u001b[4;{color}m{str(day_e)}\u001b[0m", 1)

        if recurring:
            day_of_week = dt_obj.weekday() # Day of the week the event takes place
            day_of_month = dt_obj.day # Day of month event takes place
            if recurring_when == 0:
                tmp = event_time%604800 # How many seconds into the week it is.
                recurring_ts = tmp
            elif recurring_when == 1:
                inter = 2629746
                tmp = event_time%2629746 # Yeah, you get it right? This time, month.
                recurring_ts = tmp
            first_of_month = datetime(year, month.value, 1)
            first_ts = first_of_month.timestamp()
            r_event_ts = [first_ts + recurring_ts + inter*i for i in range(5)] # Works well enough, overflows into outside the calendar when needed with no fallout.
            # if int(first_ts)%inter > recurring_ts: # Detects if the first of the month is actually after the day of the week.
            #    print(recurring_ts)
            #    print(int(first_ts)%inter)
            #    r_event_ts.pop(0)
            r_event_dts = [datetime.fromtimestamp(int(i)) for i in r_event_ts]
            previous = 0
            print(day_of_week)
            print(day_of_month)
            for i in r_event_dts:
                day = i.day
                if recurring_when == 0:
                    diff = day_of_week - i.weekday()
                    # diff += diff/abs(diff)

                    i = datetime.fromtimestamp(i.timestamp() + diff*86400)
                    print("Old weekday", i.weekday())
                    day = i.day
                    print("New weekday", i.weekday())
                    print("Expected ", day_of_week)
                elif recurring_when == 1:
                    day = day_of_month

                if day > previous:
                    previous = day
                    cal_str = cal_str.replace(str(day), f"\u001b[4;{color}m{str(day)}\u001b[0m", 1)
    upcoming = ""
    if min_time != 0:
        upcoming = f" Next up:\n {min_name}, <t:{int(min_time)}:R>."
        
        
    embed.set_image(url=calendar_pictures[month.value - 1])
    embed.add_field(name="Calendar (colored green = event in the day)", value=(f"```ansi\n{cal_str}\n```\n " + upcoming))
    embed.set_footer(text="Brought to you by the Tonberries FC.")
    await interaction.response.send_message(embed=embed)

class EventBrowse(View):
    def __init__(self, current_ts, index, interaction_og):
        super().__init__()
        # button_next = Button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
        # button_previous = Button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
        # button_delete = Button(label="X", style=discord.ButtonStyle.primary, custom_id="del")
        # self.add_item(button_next)
        # self.add_item(button_previous)
        # self.add_item(button_delete)
        self.current_ts = current_ts
        self.index = index
        self.interaction = interaction_og

    
    @discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
    @is_manager()
    async def button_callback1(self, interaction: discord.Interaction, button: Button):
        conn = sqlite3.connect('tonbase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE server_id = ?", (int(interaction.guild_id),))
        server_events = cursor.fetchall()
        conn.close()
        switch_to = server_events[self.index - 1]
        self.index -= 1
        await self.interaction.edit_original_response(content=f"Event called {switch_to[1]} <t:{switch_to[2]}:R>.\nDescription: {switch_to[6]}\nHosted by: <@{switch_to[3]}>.")

    @discord.ui.button(label="x", style=discord.ButtonStyle.primary, custom_id="del")
    @is_manager()
    async def button_callback3(self, interaction: discord.Interaction, button: Button):
        conn = sqlite3.connect('tonbase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE server_id = ?", (int(interaction.guild_id),))
        server_events = cursor.fetchall()
        id = server_events[self.index][0]
        current = server_events[self.index]
        cursor.execute("DELETE FROM events WHERE id = ?", (id,))
        print(id)
        conn.commit()
        conn.close()
        await self.interaction.edit_original_response(content=f"Event called ~~{current[1]}~~ **CANCELLED** <t:{current[2]}:R>.\nDescription: {current[6]}\nHosted by: <@{current[3]}>.")

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
    @is_manager()
    async def button_callback2(self, interaction: discord.Interaction, button: Button):
        conn = sqlite3.connect('tonbase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE server_id = ?", (int(interaction.guild_id),))
        server_events = cursor.fetchall()
        conn.close()
        switch_to = server_events[self.index + 1]
        self.index += 1
        await self.interaction.edit_original_response(content=f"Event called {switch_to[1]} <t:{switch_to[2]}:R>.\nDescription: {switch_to[6]}\nHosted by: <@{switch_to[3]}>.")


@bot.tree.command(name="events", description="Displays a list of events which can be removed.")
@is_manager()
async def eventlist(interaction : discord.Interaction):
    current_ts = datetime.now().timestamp()
    conn = sqlite3.connect('tonbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE server_id = ?", (int(interaction.guild_id),))
    server_events = cursor.fetchall()
    conn.close()
    smallest = 9999999999999999999999
    smallest_e = None
    index = 0
    for k, i in enumerate(server_events):
        et = i[2] + (i[7] + 3)*3600
        if i[2] >= current_ts and i[2] <= smallest: # Yet to happen, but also the smallest one.
            smallest = i[2]
            smallest_e = i
            index = k
    response = ""
    if not smallest_e:
        response = "No events!"
    else:
        response = f"Event called {smallest_e[1]} <t:{smallest_e[2]}:R>.\nDescription: {smallest_e[6]}\nHosted by: <@{smallest_e[3]}>."
    view = EventBrowse(current_ts, index, interaction)
    await interaction.response.send_message(response, view=view)

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
