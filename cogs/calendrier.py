import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class Calendrier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/calendrier.json"
        self.channel_id = 1462916585793786061  # Channel du calendrier
        self.events = self.load_data()
    
    def load_data(self):
        """Charge les événements depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_data(self):
        """Sauvegarde les événements dans le fichier JSON"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=4, ensure_ascii=False)
    
    def get_week_key(self):
        """Retourne la clé de la semaine actuelle (ex: 2024-W52)"""
        now = datetime.now()
        return f"{now.year}-W{now.isocalendar()[1]:02d}"
    
    def init_week(self, week_key):
        """Initialise une nouvelle semaine vide"""
        if week_key not in self.events:
            self.events[week_key] = {
                "lundi": {},
                "mardi": {},
                "mercredi": {},
                "jeudi": {},
                "vendredi": {},
                "samedi": {},
                "dimanche": {}
            }
            for jour in self.events[week_key]:
                for heure in range(0, 24, 2):
                    self.events[week_key][jour][f"{heure:02d}:00"] = []
    
    def generate_calendar_embed(self, week_key):
        """Génère l'embed du calendrier"""
        self.init_week(week_key)
        
        embed = discord.Embed(
            title="📅 Calendrier de la Semaine",
            description=f"**Semaine {week_key.split('-W')[1]} - {datetime.now().year}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        jours_emoji = {
            "lundi": "🔵",
            "mardi": "🟢",
            "mercredi": "🟡",
            "jeudi": "🟠",
            "vendredi": "🔴",
            "samedi": "🟣",
            "dimanche": "⚪"
        }
        
        for jour, emoji in jours_emoji.items():
            events_text = ""
            for heure in sorted(self.events[week_key][jour].keys()):
                events = self.events[week_key][jour][heure]
                if events:
                    events_text += f"\n**{heure}** - " + " | ".join(events)
            
            if not events_text:
                events_text = "\n*Aucun événement*"
            
            embed.add_field(
                name=f"{emoji} {jour.upper()}",
                value=events_text,
                inline=False
            )
        
        embed.set_footer(text="Utilisez /event_ajouter pour planifier un événement")
        return embed
    
    async def update_calendar_message(self):
        """Met à jour le message du calendrier dans le channel"""
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        
        week_key = self.get_week_key()
        embed = self.generate_calendar_embed(week_key)
        
        # Cherche le dernier message du bot dans le channel
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds:
                await message.edit(embed=embed)
                return
        
        # Si aucun message trouvé, en envoie un nouveau
        await channel.send(embed=embed)
    
    @app_commands.command(
        name="event_ajouter",
        description="📅 Ajouter un événement au calendrier"
    )
    @app_commands.describe(
        jour="Jour de la semaine",
        heure="Heure de début (format: 00, 02, 04, 06, 08, 10, 12, 14, 16, 18, 20, 22)",
        evenement="Description de l'événement"
    )
    @app_commands.choices(jour=[
        app_commands.Choice(name="🔵 Lundi", value="lundi"),
        app_commands.Choice(name="🟢 Mardi", value="mardi"),
        app_commands.Choice(name="🟡 Mercredi", value="mercredi"),
        app_commands.Choice(name="🟠 Jeudi", value="jeudi"),
        app_commands.Choice(name="🔴 Vendredi", value="vendredi"),
        app_commands.Choice(name="🟣 Samedi", value="samedi"),
        app_commands.Choice(name="⚪ Dimanche", value="dimanche")
    ])
    @app_commands.choices(heure=[
        app_commands.Choice(name="00:00", value="00"),
        app_commands.Choice(name="02:00", value="02"),
        app_commands.Choice(name="04:00", value="04"),
        app_commands.Choice(name="06:00", value="06"),
        app_commands.Choice(name="08:00", value="08"),
        app_commands.Choice(name="10:00", value="10"),
        app_commands.Choice(name="12:00", value="12"),
        app_commands.Choice(name="14:00", value="14"),
        app_commands.Choice(name="16:00", value="16"),
        app_commands.Choice(name="18:00", value="18"),
        app_commands.Choice(name="20:00", value="20"),
        app_commands.Choice(name="22:00", value="22")
    ])
    async def event_ajouter(
        self, 
        interaction: discord.Interaction,
        jour: app_commands.Choice[str],
        heure: app_commands.Choice[str],
        evenement: str
    ):
        week_key = self.get_week_key()
        self.init_week(week_key)
        
        heure_format = f"{heure.value}:00"
        
        # Ajoute l'événement
        self.events[week_key][jour.value][heure_format].append(evenement)
        self.save_data()
        
        # Met à jour le calendrier
        await self.update_calendar_message()
        
        embed = discord.Embed(
            title="✅ Événement Ajouté",
            description=f"**{jour.name}** à **{heure_format}**\n\n📝 {evenement}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="event_supprimer",
        description="🗑️ Supprimer un événement du calendrier"
    )
    @app_commands.describe(
        jour="Jour de la semaine",
        heure="Heure de l'événement",
        index="Numéro de l'événement (1, 2, 3...)"
    )
    @app_commands.choices(jour=[
        app_commands.Choice(name="🔵 Lundi", value="lundi"),
        app_commands.Choice(name="🟢 Mardi", value="mardi"),
        app_commands.Choice(name="🟡 Mercredi", value="mercredi"),
        app_commands.Choice(name="🟠 Jeudi", value="jeudi"),
        app_commands.Choice(name="🔴 Vendredi", value="vendredi"),
        app_commands.Choice(name="🟣 Samedi", value="samedi"),
        app_commands.Choice(name="⚪ Dimanche", value="dimanche")
    ])
    @app_commands.choices(heure=[
        app_commands.Choice(name="00:00", value="00"),
        app_commands.Choice(name="02:00", value="02"),
        app_commands.Choice(name="04:00", value="04"),
        app_commands.Choice(name="06:00", value="06"),
        app_commands.Choice(name="08:00", value="08"),
        app_commands.Choice(name="10:00", value="10"),
        app_commands.Choice(name="12:00", value="12"),
        app_commands.Choice(name="14:00", value="14"),
        app_commands.Choice(name="16:00", value="16"),
        app_commands.Choice(name="18:00", value="18"),
        app_commands.Choice(name="20:00", value="20"),
        app_commands.Choice(name="22:00", value="22")
    ])
    async def event_supprimer(
        self,
        interaction: discord.Interaction,
        jour: app_commands.Choice[str],
        heure: app_commands.Choice[str],
        index: int
    ):
        week_key = self.get_week_key()
        self.init_week(week_key)
        
        heure_format = f"{heure.value}:00"
        events = self.events[week_key][jour.value][heure_format]
        
        if index < 1 or index > len(events):
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Aucun événement n°{index} trouvé à cette date.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Supprime l'événement (index - 1 car liste commence à 0)
        removed_event = events.pop(index - 1)
        self.save_data()
        
        # Met à jour le calendrier
        await self.update_calendar_message()
        
        embed = discord.Embed(
            title="✅ Événement Supprimé",
            description=f"**{jour.name}** à **{heure_format}**\n\n~~{removed_event}~~",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="calendrier_afficher",
        description="📅 Afficher/Mettre à jour le calendrier"
    )
    async def calendrier_afficher(self, interaction: discord.Interaction):
        await self.update_calendar_message()
        
        embed = discord.Embed(
            title="✅ Calendrier Mis à Jour",
            description="Le calendrier a été actualisé dans le salon prévu.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Calendrier(bot))
