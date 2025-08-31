import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# Initialize the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message-based commands if also used
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

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
        cursor.execute("SELECT * FROM allowed_roles WHERE server_id = ?;", (guild_id,))
        allowed_roles = cursor.fetchall()
        conn.close()
        verified = False
        for i in allowed_roles:
            verified = i in interaction.user.roles
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
    
f = open("secret.txt", "r")
token = f.read()

# Run the bot
bot.run(token)