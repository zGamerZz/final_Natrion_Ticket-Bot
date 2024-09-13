import discord
import json
import chat_exporter
import io
import pytz
from datetime import datetime
import sqlite3
from discord import *
from discord.ext import commands
from discord.ext.commands import has_permissions
from cogs.ticket_system import MyView

# Diese Zeile lädt die Konfiguration aus der config.json Datei
with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

TICKET_CHANNEL = config["ticket_channel_id"]
GUILD_ID = config["guild_id"]
LOG_CHANNEL = config["log_channel_id"]
TIMEZONE = config["timezone"]
EMBED_TITLE = config["embed_title"]
EMBED_DESCRIPTION = config["embed_description"]

# Diese Zeile erstellt und verbindet sich mit der Datenbank
conn = sqlite3.connect('Database.db')
cur = conn.cursor()

class Ticket_Command(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot geladen  | ticket_commands.py ✅')

    @commands.Cog.listener()
    async def on_bot_shutdown():
        cur.close()
        conn.close()
    #
    # Slash-Befehl, um das Ticket-Menü im Ticket-Kanal anzuzeigen. Muss nur einmal verwendet werden.
    @commands.slash_command(name="ticket")
    @has_permissions(administrator=True)
    async def ticket(self, ctx):
        self.channel = self.bot.get_channel(TICKET_CHANNEL)
        embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
        await self.channel.send(embed=embed, view=MyView(self.bot))
        await ctx.respond("Ticket-Menü wurde gesendet!", ephemeral=True)

    # Slash-Befehl, um Mitglieder zum Ticket hinzuzufügen
    @commands.slash_command(name="add", description="Füge ein Mitglied zum Ticket hinzu")
    async def add(self, ctx, member: Option(discord.Member, description="Welches Mitglied möchtest du zum Ticket hinzufügen", required=True)):
        if "ticket-" in ctx.channel.name or "ticket-closed-" in ctx.channel.name:
            await ctx.channel.set_permissions(member, send_messages=True, read_messages=True, add_reactions=False,
                                                embed_links=True, attach_files=True, read_message_history=True,
                                                external_emojis=True)
            self.embed = discord.Embed(description=f'{member.mention} wurde zu diesem Ticket <#{ctx.channel.id}> hinzugefügt! \n Benutze /remove, um einen Benutzer zu entfernen.', color=discord.colour.Color.green())
            await ctx.respond(embed=self.embed)
        else:
            self.embed = discord.Embed(description=f'Dieser Befehl kann nur in einem Ticket verwendet werden!', color=discord.colour.Color.red())
            await ctx.respond(embed=self.embed)

    # Slash-Befehl, um Mitglieder aus dem Ticket zu entfernen
    @commands.slash_command(name="remove", description="Entferne ein Mitglied aus dem Ticket")
    async def remove(self, ctx, member: Option(discord.Member, description="Welches Mitglied möchtest du aus dem Ticket entfernen", required=True)):
        if "ticket-" in ctx.channel.name or "ticket-closed-" in ctx.channel.name:
            await ctx.channel.set_permissions(member, send_messages=False, read_messages=False, add_reactions=False,
                                                embed_links=False, attach_files=False, read_message_history=False,
                                                external_emojis=False)
            self.embed = discord.Embed(description=f'{member.mention} wurde aus diesem Ticket <#{ctx.channel.id}> entfernt! \n Benutze /add, um einen Benutzer hinzuzufügen.', color=discord.colour.Color.green())
            await ctx.respond(embed=self.embed)
        else:
            self.embed = discord.Embed(description=f'Dieser Befehl kann nur in einem Ticket verwendet werden!', color=discord.colour.Color.red())
            await ctx.respond(embed=self.embed)

    @commands.slash_command(name="delete", description="Lösche das Ticket")
    async def delete_ticket(self, ctx):
        guild = self.bot.get_guild(GUILD_ID)
        channel = self.bot.get_channel(LOG_CHANNEL)
        ticket_id = ctx.channel.id

        cur.execute("SELECT id, discord_id, ticket_created FROM ticket WHERE ticket_channel=?", (ticket_id,))
        ticket_data = cur.fetchone()
        id, ticket_creator_id, ticket_created = ticket_data
        ticket_creator = guild.get_member(ticket_creator_id)

        ticket_created_unix = self.convert_to_unix_timestamp(ticket_created)
        timezone = pytz.timezone(TIMEZONE)
        ticket_closed = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        ticket_closed_unix = self.convert_to_unix_timestamp(ticket_closed)

        # Erstellen des Transkripts
        military_time: bool = True
        transcript = await chat_exporter.export(ctx.channel, limit=200, tz_info=TIMEZONE, military_time=military_time, bot=self.bot)
        
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transkript-{ctx.channel.name}.html")
        transcript_file2 = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transkript-{ctx.channel.name}.html")
        
        embed = discord.Embed(description=f'Ticket wird in 5 Sekunden gelöscht.', color=0xff0000)
        transcript_info = discord.Embed(title=f"Ticket gelöscht | {ctx.channel.name}", color=discord.colour.Color.blue())
        transcript_info.add_field(name="ID", value=id, inline=True)
        transcript_info.add_field(name="Geöffnet von", value=ticket_creator.mention, inline=True)
        transcript_info.add_field(name="Geschlossen von", value=ctx.author.mention, inline=True)
        transcript_info.add_field(name="Ticket erstellt", value=f"<t:{ticket_created_unix}:f>", inline=True)
        transcript_info.add_field(name="Ticket geschlossen", value=f"<t:{ticket_closed_unix}:f>", inline=True)

        await ctx.respond(embed=embed)
        try:
            await ticket_creator.send(embed=transcript_info, file=transcript_file)
        except:
            transcript_info.add_field(name="Fehler", value="Direktnachrichten des Ticket-Erstellers sind deaktiviert", inline=True)

        await channel.send(embed=transcript_info, file=transcript_file2)
        await asyncio.sleep(3)
        await ctx.channel.delete(reason="Ticket gelöscht")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        dt_obj = datetime.strptime(date_string, date_format)
        berlin_tz = pytz.timezone('Europe/Berlin')
        dt_obj = berlin_tz.localize(dt_obj)
        dt_obj_utc = dt_obj.astimezone(pytz.utc)
        return int(dt_obj_utc.timestamp())