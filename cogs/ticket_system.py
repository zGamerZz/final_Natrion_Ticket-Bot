import discord
import asyncio
import pytz
import json
import sqlite3
from datetime import datetime
import chat_exporter
import io
from discord.ext import commands

# Diese Zeile lädt die Konfiguration aus der config.json Datei
with open("config.json", mode="r") as config_file:
    config = json.load(config_file)

GUILD_ID = config["guild_id"]
TICKET_CHANNEL = config["ticket_channel_id"]
CATEGORY_ID1 = config["category_id_1"]
CATEGORY_ID2 = config["category_id_2"]
TEAM_ROLE1 = config["team_role_id_1"]
TEAM_ROLE2 = config["team_role_id_2"]
LOG_CHANNEL = config["log_channel_id"]
TIMEZONE = config["timezone"]
EMBED_TITLE = config["embed_title"]
EMBED_DESCRIPTION = config["embed_description"]

# Diese Zeile erstellt und verbindet sich mit der Datenbank
conn = sqlite3.connect('Database.db')
cur = conn.cursor()

# Erstellt die Tabelle, wenn sie nicht existiert
cur.execute("""CREATE TABLE IF NOT EXISTS ticket 
           (id INTEGER PRIMARY KEY AUTOINCREMENT, discord_name TEXT, discord_id INTEGER, ticket_channel TEXT, ticket_created TIMESTAMP)""")
conn.commit()

class Ticket_System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.clear_deleted_tickets()
    #
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot geladen  | ticket_system.py ✅')
        self.bot.add_view(MyView(bot=self.bot))
        self.bot.add_view(CloseButton(bot=self.bot))
        self.bot.add_view(TicketOptions(bot=self.bot))
        self.clear_deleted_tickets()  # Optional: Beim Bot-Start aufrufen

    # Schließt die Verbindung zur Datenbank beim Herunterfahren des Bots
    @commands.Cog.listener()
    async def on_bot_shutdown():
        cur.close()
        conn.close()

    def clear_deleted_tickets(self):
        cur.execute("SELECT id, ticket_channel FROM ticket")
        tickets = cur.fetchall()
        
        for ticket in tickets:
            ticket_id, channel_id = ticket
            channel = self.bot.get_channel(channel_id)
            if not channel:  # Channel existiert nicht mehr
                cur.execute("DELETE FROM ticket WHERE id=?", (ticket_id,))
                conn.commit()
                print(f"Ticket {ticket_id} entfernt, da der Kanal nicht mehr existiert.")

# Allgemeiner Support Modal
class GeneralSupportModal(discord.ui.Modal):
    def __init__(self, bot):
        self.bot = bot  # Bot speichern für späteren Zugriff
        super().__init__(title="Allgemeiner Support")

        # Eingabefelder hinzufügen
        self.add_item(discord.ui.InputText(label="Was ist dein Anliegen?", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        # Gilde holen
        guild = self.bot.get_guild(GUILD_ID)

        # Benutzerinformationen abrufen
        user_id = interaction.user.id
        user_name = interaction.user.name
        creation_date = datetime.now()

        # Datenbankverbindung herstellen
        conn = sqlite3.connect('Database.db')
        cur = conn.cursor()

        # Ticket in die Datenbank einfügen
        cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date))
        conn.commit()

        # Holen der Ticketnummer aus der Datenbank
        await asyncio.sleep(1)
        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
        ticket_number = cur.fetchone()[0]

        # Kategorie und Ticket-Kanal erstellen
        category = self.bot.get_channel(CATEGORY_ID2)
        ticket_channel = await guild.create_text_channel(f"ticket-{ticket_number}", category=category, topic=f"{interaction.user.id}")

        # Berechtigungen für das Team festlegen
        await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für den Benutzer festlegen
        await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für @everyone festlegen
        await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False)

        # Begrüßungsnachricht im Ticket-Kanal senden
        embed_welcome = discord.Embed(description=f'Willkommen {interaction.user.mention},\nWie kann ich dir helfen?',
                                      color=discord.Colour.blue())
        await ticket_channel.send(embed=embed_welcome, view=CloseButton(bot=self.bot))

        # Anliegen des Benutzers aus dem Modal sammeln
        issue = self.children[0].value

        # Embed mit dem Anliegen des Benutzers erstellen
        embed_issue = discord.Embed(title="Allgemeiner Support", color=discord.Colour.green())
        embed_issue.add_field(name="Was ist dein Anliegen?", value=issue, inline=False)
        embed_issue.set_footer(text=f"Eingereicht von {interaction.user.name}")

        # Embed mit dem Anliegen im Ticket-Kanal senden
        await ticket_channel.send(embed=embed_issue)

        # Ticket-Kanal-ID in die Datenbank aktualisieren
        channel_id = ticket_channel.id
        cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
        conn.commit()

        # Schließen der Datenbankverbindung
        cur.close()
        conn.close()

        # Bestätigungsnachricht direkt an den Benutzer senden, ohne followup
        embed_confirmation = discord.Embed(description=f'📬 Ticket wurde erstellt! Siehe hier --> {ticket_channel.mention}',
                                           color=discord.Colour.green())
        await interaction.response.send_message(embed=embed_confirmation, ephemeral=True)  # Sende direkt eine Nachricht

        # Ursprüngliche Nachricht editieren und das Auswahlmenü zurücksetzen
        await asyncio.sleep(1)
        embed_reset = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.Colour.blue())
        await interaction.message.edit(embed=embed_reset, view=MyView(bot=self.bot))

# Bewerbung Modal
class BewerbungModal(discord.ui.Modal):
    def __init__(self, bot):
        self.bot = bot  # Bot speichern für späteren Zugriff
        super().__init__(title="Bewerbung")

        # Eingabefelder hinzufügen
        self.add_item(discord.ui.InputText(label="Als was möchtest du dich bewerben?", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Wie alt bist du?", style=discord.InputTextStyle.short))
        self.add_item(discord.ui.InputText(label="Frage 2", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Frage 3", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Frage 4", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        # Gilde holen
        guild = self.bot.get_guild(GUILD_ID)

        # Benutzerinformationen abrufen
        user_id = interaction.user.id
        user_name = interaction.user.name
        creation_date = datetime.now()

        # Datenbankverbindung herstellen
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        # Ticket in die Datenbank einfügen
        cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date))
        conn.commit()

        # Holen der Ticketnummer aus der Datenbank
        await asyncio.sleep(1)
        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
        ticket_number = cur.fetchone()[0]

        # Kategorie und Ticket-Kanal erstellen
        category = self.bot.get_channel(CATEGORY_ID2)
        ticket_channel = await guild.create_text_channel(f"ticket-{ticket_number}", category=category, topic=f"{interaction.user.id}")

        # Berechtigungen für das Team festlegen
        await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für den Benutzer festlegen
        await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für @everyone festlegen
        await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False)

        # Begrüßungsnachricht im Ticket-Kanal senden
        embed_welcome = discord.Embed(description=f'Willkommen {interaction.user.mention},\nWie kann ich dir helfen?',
                                      color=discord.Colour.blue())
        await ticket_channel.send(embed=embed_welcome, view=CloseButton(bot=self.bot))

        # Informationen aus dem Modal sammeln
        job_application = self.children[0].value
        age = self.children[1].value
        question_2 = self.children[2].value
        question_3 = self.children[3].value
        question_4 = self.children[4].value

        # Embed mit den Bewerbungsinformationen erstellen
        embed_application = discord.Embed(title="Bewerbung", color=discord.Colour.orange())
        embed_application.add_field(name="Als was möchtest du dich bewerben?", value=job_application, inline=False)
        embed_application.add_field(name="Wie alt bist du?", value=age, inline=False)
        embed_application.add_field(name="Frage 2", value=question_2, inline=False)
        embed_application.add_field(name="Frage 3", value=question_3, inline=False)
        embed_application.add_field(name="Frage 4", value=question_4, inline=False)
        embed_application.set_footer(text=f"Eingereicht von {interaction.user.name}")

        # Embed im Ticket-Kanal senden
        await ticket_channel.send(embed=embed_application)

        # Ticket-Kanal-ID in die Datenbank aktualisieren
        channel_id = ticket_channel.id
        cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
        conn.commit()

        # Schließen der Datenbankverbindung
        cur.close()
        conn.close()

        # Bestätigungsnachricht direkt an den Benutzer senden
        embed_confirmation = discord.Embed(description=f'📬 Ticket wurde erstellt! Siehe hier --> {ticket_channel.mention}',
                                           color=discord.Colour.green())
        await interaction.response.send_message(embed=embed_confirmation, ephemeral=True)

        # Ursprüngliche Nachricht editieren und das Auswahlmenü zurücksetzen
        await asyncio.sleep(1)
        embed_reset = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.Colour.blue())
        await interaction.message.edit(embed=embed_reset, view=MyView(bot=self.bot))

# Weitere Klassen folgen...


# Bewerbung Modal
class BewerbungModal(discord.ui.Modal):
    def __init__(self, bot):
        self.bot = bot  # Bot speichern für späteren Zugriff
        super().__init__(title="Bewerbung")

        # Eingabefelder hinzufügen
        self.add_item(discord.ui.InputText(label="Als was möchtest du dich bewerben?", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Wie alt bist du?", style=discord.InputTextStyle.short))
        self.add_item(discord.ui.InputText(label="Frage 2", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Frage 3", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Frage 4", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        # Gilde holen
        guild = self.bot.get_guild(GUILD_ID)

        # Benutzerinformationen abrufen
        user_id = interaction.user.id
        user_name = interaction.user.name
        creation_date = datetime.now()

        # Datenbankverbindung herstellen (du musst sicherstellen, dass conn und cur hier definiert sind)
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        # Ticket in die Datenbank einfügen
        cur.execute("INSERT INTO ticket (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)", (user_name, user_id, creation_date))
        conn.commit()

        # Holen der Ticketnummer aus der Datenbank
        await asyncio.sleep(1)
        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
        ticket_number = cur.fetchone()[0]

        # Kategorie und Ticket-Kanal erstellen
        category = self.bot.get_channel(CATEGORY_ID2)
        ticket_channel = await guild.create_text_channel(f"ticket-{ticket_number}", category=category, topic=f"{interaction.user.id}")

        # Berechtigungen für das Team festlegen
        await ticket_channel.set_permissions(guild.get_role(TEAM_ROLE2), send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für den Benutzer festlegen
        await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False,
                                             embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

        # Berechtigungen für @everyone festlegen
        await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False)

        # Begrüßungsnachricht im Ticket-Kanal senden
        embed_welcome = discord.Embed(description=f'Willkommen {interaction.user.mention},\nWie kann ich dir helfen?',
                                      color=discord.Colour.blue())
        await ticket_channel.send(embed=embed_welcome, view=CloseButton(bot=self.bot))

        # Informationen aus dem Modal sammeln
        job_application = self.children[0].value
        age = self.children[1].value
        question2 = self.children[2].value
        question3 = self.children[3].value
        question4 = self.children[4].value

        # Embed mit den Antworten des Benutzers erstellen
        embed_answers = discord.Embed(title="Bewerbung", color=discord.Colour.green())
        embed_answers.add_field(name="Als was möchtest du dich bewerben?", value=job_application, inline=False)
        embed_answers.add_field(name="Wie alt bist du?", value=age, inline=False)
        embed_answers.add_field(name="Frage 2", value=question2, inline=False)
        embed_answers.add_field(name="Frage 3", value=question3, inline=False)
        embed_answers.add_field(name="Frage 4", value=question4, inline=False)
        embed_answers.set_footer(text=f"Eingereicht von {interaction.user.name}")

        # Embed mit den Antworten im Ticket-Kanal senden
        await ticket_channel.send(embed=embed_answers)

        # Ticket-Kanal-ID in die Datenbank aktualisieren
        channel_id = ticket_channel.id
        cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
        conn.commit()

        # Bestätigungsnachricht direkt an den Benutzer senden, ohne followup
        embed_confirmation = discord.Embed(description=f'📬 Ticket wurde erstellt! Siehe hier --> {ticket_channel.mention}',
                                           color=discord.Colour.green())
        await interaction.response.send_message(embed=embed_confirmation, ephemeral=True)  # Sende direkt eine Nachricht

        # Ursprüngliche Nachricht editieren und das Auswahlmenü zurücksetzen
        await asyncio.sleep(1)
        embed_reset = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.Colour.blue())
        await interaction.message.edit(embed=embed_reset, view=MyView(bot=self.bot))




# Auswahlmenü für Supportoptionen
class MyView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="support",
        placeholder="Wähle eine Ticket-Option",
        options=[
            discord.SelectOption(
                label="Allgemeiner Support",
                description="Hier erhältst du Unterstützung!",
                emoji="❓",
                value="support1"
            ),
            discord.SelectOption(
                label="Bewerbung",
                description="Bewerbe dich bei uns!",
                emoji="📛",
                value="support2"
            )
        ]
    )
    async def callback(self, select, interaction):
        # Je nach Auswahl ein anderes Modal öffnen
        if select.values[0] == "support1":
            modal = GeneralSupportModal(bot=self.bot)
        elif select.values[0] == "support2":
            modal = BewerbungModal(bot=self.bot)

        await interaction.response.send_modal(modal)



# Erster Button für das Ticket
class CloseButton(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket löschen 🎫", style = discord.ButtonStyle.blurple, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket löschen 🎫", description="Bist du sicher, dass du dieses Ticket löschen möchtest?", color=discord.colour.Color.green())
        await interaction.response.send_message(embed=embed, view=TicketOptions(bot=self.bot)) # Dies zeigt dem Benutzer die Ticket-Optionen-Ansicht
        await interaction.message.edit(view=self)


# Buttons zum Wiederöffnen oder Löschen des Tickets
class TicketOptions(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket löschen 🎫", style = discord.ButtonStyle.red, custom_id="delete")
    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = self.bot.get_guild(GUILD_ID)
        channel = self.bot.get_channel(LOG_CHANNEL)
        ticket_id = interaction.channel.id

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
        transcript = await chat_exporter.export(interaction.channel, limit=200, tz_info=TIMEZONE, military_time=military_time, bot=self.bot)
        
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transkript-{interaction.channel.name}.html")
        transcript_file2 = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transkript-{interaction.channel.name}.html")
        
        embed = discord.Embed(description=f'Ticket wird in 5 Sekunden gelöscht.', color=0xff0000)
        transcript_info = discord.Embed(title=f"Ticket gelöscht | {interaction.channel.name}", color=discord.colour.Color.blue())
        transcript_info.add_field(name="ID", value=id, inline=True)
        transcript_info.add_field(name="Geöffnet von", value=ticket_creator.mention, inline=True)
        transcript_info.add_field(name="Geschlossen von", value=interaction.user.mention, inline=True)
        transcript_info.add_field(name="Ticket erstellt", value=f"<t:{ticket_created_unix}:f>", inline=True)
        transcript_info.add_field(name="Ticket geschlossen", value=f"<t:{ticket_closed_unix}:f>", inline=True)

        await interaction.response.send_message(embed=embed)
        try:
            await ticket_creator.send(embed=transcript_info, file=transcript_file)
        except:
            transcript_info.add_field(name="Fehler", value="Direktnachrichten des Ticket-Erstellers sind deaktiviert", inline=True)

        await channel.send(embed=transcript_info, file=transcript_file2)
        await asyncio.sleep(3)
        await interaction.channel.delete(reason="Ticket gelöscht")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        try:
            # Zuerst versuchen wir, Millisekunden zu parsen
            date_format = "%Y-%m-%d %H:%M:%S.%f"
            dt_obj = datetime.strptime(date_string, date_format)
        except ValueError:
            # Wenn keine Millisekunden vorhanden sind, wird ohne Millisekunden geparst
            date_format = "%Y-%m-%d %H:%M:%S"
            dt_obj = datetime.strptime(date_string, date_format)
        
        berlin_tz = pytz.timezone('Europe/Berlin')
        dt_obj = berlin_tz.localize(dt_obj)
        dt_obj_utc = dt_obj.astimezone(pytz.utc)
        return int(dt_obj_utc.timestamp())

