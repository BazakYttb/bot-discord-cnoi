import discord
from discord import app_commands
from discord.ext import commands
from config.settings import CHANNEL_ORGANIGRAMME
import json
import os

class Organigramme(commands.Cog):
    """
    Cog pour gérer l'organigramme gouvernemental modifiable
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/organigramme.json"
        self.message_id = None  # ID du message à éditer
        
        # Créer le dossier data s'il n'existe pas
        os.makedirs("data", exist_ok=True)
        
        # Charger les données
        self.load_data()
    
    def load_data(self):
        """
        Charge les données depuis le JSON
        """
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.gouvernement = data.get('gouvernement', {})
                self.message_id = data.get('message_id')
        else:
            # Données par défaut
            self.gouvernement = {
                "Empereur": "Non défini",
                "Ministre des Armées": "Non défini",
                "Ministre de l'Impérialisme": "Non défini",
                "Ministre des Affaires Étrangères": "Non défini",
                "Ministre de la Culture": "Non défini",
                "Ministère Principal": "Non défini"
            }
            self.save_data()
    
    def save_data(self):
        """
        Sauvegarde les données dans le JSON
        """
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'gouvernement': self.gouvernement,
                'message_id': self.message_id
            }, f, indent=4, ensure_ascii=False)
    
    def create_embed(self):
        """
        Crée l'embed de l'organigramme
        """
        embed = discord.Embed(
            title="🏛️ Organigramme du Gouvernement",
            description="Voici la composition actuelle du gouvernement impérial :",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        for poste, titulaire in self.gouvernement.items():
            embed.add_field(
                name=f"👤 {poste}",
                value=titulaire,
                inline=False
            )
        
        embed.set_footer(text="Mis à jour automatiquement")
        
        return embed
    
    @commands.Cog.listener()
    async def on_ready(self):
        """
        Met à jour le message au démarrage du bot
        """
        await self.update_message()
    
    async def update_message(self):
        """
        Met à jour ou crée le message de l'organigramme
        """
        channel = self.bot.get_channel(CHANNEL_ORGANIGRAMME)
        if not channel:
            print(f"  ⚠️ Channel organigramme {CHANNEL_ORGANIGRAMME} introuvable")
            return
        
        embed = self.create_embed()
        
        if self.message_id:
            try:
                message = await channel.fetch_message(self.message_id)
                await message.edit(embed=embed)
                print("  ✅ Organigramme mis à jour")
            except discord.NotFound:
                # Le message a été supprimé, on en crée un nouveau
                message = await channel.send(embed=embed)
                self.message_id = message.id
                self.save_data()
                print("  ✅ Nouveau message d'organigramme créé")
        else:
            # Première fois, on crée le message
            message = await channel.send(embed=embed)
            self.message_id = message.id
            self.save_data()
            print("  ✅ Message d'organigramme créé")
    
    @app_commands.command(
        name="modifier_poste",
        description="[ADMIN] Modifie un poste dans l'organigramme"
    )
    @app_commands.describe(
        poste="Le poste à modifier",
        titulaire="Le nom du nouveau titulaire (mention ou texte)"
    )
    @app_commands.default_permissions(administrator=True)
    async def modifier_poste(
        self, 
        interaction: discord.Interaction,
        poste: str,
        titulaire: str
    ):
        """
        Modifie un poste dans l'organigramme
        """
        if poste not in self.gouvernement:
            await interaction.response.send_message(
                f"❌ Le poste `{poste}` n'existe pas.\n\n"
                f"**Postes disponibles :**\n" + 
                "\n".join(f"• {p}" for p in self.gouvernement.keys()),
                ephemeral=True
            )
            return
        
        self.gouvernement[poste] = titulaire
        self.save_data()
        await self.update_message()
        
        await interaction.response.send_message(
            f"✅ **{poste}** a été mis à jour : {titulaire}",
            ephemeral=True
        )
    
    @modifier_poste.autocomplete('poste')
    async def poste_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        """
        Autocomplétion pour les postes
        """
        return [
            app_commands.Choice(name=poste, value=poste)
            for poste in self.gouvernement.keys()
            if current.lower() in poste.lower()
        ]

async def setup(bot):
    await bot.add_cog(Organigramme(bot))
