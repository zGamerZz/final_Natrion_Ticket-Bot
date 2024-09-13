# Natrion Ticket Bot

Der Natrion Ticket Bot ist ein Discord-Bot, der es Benutzern ermöglicht, Support-Tickets zu erstellen und Hilfe zu erhalten. Der Bot wurde entwickelt, um in einem Discord-Server zu funktionieren und verwendet verschiedene Kategorien und Kanäle, um die Tickets zu organisieren.

## Funktionen

- Erstellung von Support-Tickets: Benutzer können ein Support-Ticket erstellen, um Hilfe zu erhalten.
- Hinzufügen von Mitgliedern: Administratoren können Mitglieder zu einem Ticket hinzufügen, um bei der Lösung des Problems zu helfen.
- Entfernen von Mitgliedern: Administratoren können Mitglieder aus einem Ticket entfernen, wenn sie nicht mehr benötigt werden.
- Löschen von Tickets: Administratoren können ein Ticket löschen, wenn es nicht mehr benötigt wird.

## Konfiguration

Die Konfiguration des Bots erfolgt über die `config.json`-Datei. Hier können Sie die Discord-Token, Server-IDs, Kanal-IDs, Rollen-IDs und andere Einstellungen festlegen. Stellen Sie sicher, dass Sie die Konfiguration entsprechend Ihren Anforderungen anpassen, bevor Sie den Bot starten.

```json
{
  "token": "Ihr Discord-Token",
  "guild_id": "Ihre Server-ID",
  "ticket_channel_id": "ID des Ticket-Kanals",
  "category_id_1": "ID der Kategorie 1",
  "category_id_2": "ID der Kategorie 2",
  "team_role_id_1": "ID der Team-Rolle 1",
  "team_role_id_2": "ID der Team-Rolle 2",
  "log_channel_id": "ID des Log-Kanals",
  "timezone": "Ihre Zeitzone",
  "embed_title": "Titel des Embeds",
  "embed_description": "Beschreibung des Embeds"
}
```

## Verwendung

Sobald der Bot gestartet ist und korrekt konfiguriert wurde, können Benutzer den Bot verwenden, um Support-Tickets zu erstellen. Administratoren haben zusätzliche Befehle zum Hinzufügen, Entfernen und Löschen von Mitgliedern.

Um ein Support-Ticket zu erstellen, verwenden Sie den Befehl `/ticket` im Ticket-Kanal. Administratoren können den Befehl `/add` verwenden, um Mitglieder hinzuzufügen, `/remove`, um Mitglieder zu entfernen, und `/delete`, um ein Ticket zu löschen.

## Beitrag

Wenn Sie einen Fehler finden oder Verbesserungsvorschläge haben, können Sie gerne einen Beitrag leisten. Erstellen Sie einfach eine Pull-Anfrage auf GitHub, um Ihre Änderungen vorzuschlagen.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Informationen finden Sie in der `LICENSE`-Datei.
