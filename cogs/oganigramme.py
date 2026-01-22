import discord
from discord import app_commands
from discord.ext import commands
import os
import json

class Organigramme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(os.getenv('CHANNEL_ORGANIGRAMME'))
        self.data_file = "data/organigramme.json"
        
        # Créer le dossier data s'il n'existe pas
        os.makedirs("data", exist_ok=True)
        
        # Initialiser les données
        self.data = self._load_data()

    def _load_data(self):
        """Charge les données depuis le JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Données par défaut
            default_data = {
                "Ministre des Armées": "Poste vacant",
                "Ministre de l'Impérialisme": "Poste vacant",
                "Ministre des Affaires Étrangères": "Poste vacant",
                "Ministre de la Culture": "Poste vacant",
                "Ministère Principal": "Poste vacant",
                "Secrétaire": "Poste vacant"
            }
            self._save_data(default_data)
            return default_data

    def _save_data(self, data=None):
        """Sauvegarde les données dans le JSON"""
        if data is None:
            data = self.data
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @app_commands.command(name="modifier_poste", description="Modifie un poste de l'organigramme")
    @app_commands.describe(
        poste="Le poste à modifier",
        titulaire="Le nom du nouveau titulaire"
    )
    @app_commands.default_permissions(administrator=True)
    async def modifier_poste(self, interaction: discord.Interaction, poste: str, titulaire: str):
        """Modifie un poste dans l'organigramme"""
        
        # Vérifier que le poste existe
        if poste not in self.data:
            postes_disponibles = "\n".join(f"• {p}" for p in self.data.keys())
            return await interaction.response.send_message(
                f"❌ Poste inconnu !\n\n**Postes disponibles :**\n{postes_disponibles}",
                ephemeral=True
            )
        
        # Modifier le poste
        self.data[poste] = titulaire
        self._save_data()
        
        # Mettre à jour le message
        await self._update_message()
        
        await interaction.response.send_message(
            f"✅ **{poste}** mis à jour → **{titulaire}**",
            ephemeral=True
        )

    async def _update_message(self):
        """Met à jour le message de l'organigramme"""
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"❌ Salon d'organigramme introuvable (ID: {self.channel_id})")
            return
        
        # Supprimer les anciens messages du bot
        async for message in channel.history(limit=10):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                except:
                    pass
        
        # Créer le nouvel embed
        embed = discord.Embed(
            title="🏛️ Organigramme du Gouvernement",
            description="*Composition actuelle du cabinet ministériel*",
            color=discord.Color.gold()
        )
        
        for poste, titulaire in self.data.items():
            embed.add_field(
                name=f"👤 {poste}",
                value=titulaire,
                inline=False
            )
        
        embed.set_footer(text="Mise à jour automatique • /modifier_poste")
        
        await channel.send(embed=embed)

    @modifier_poste.autocomplete('poste')
    async def poste_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour les postes"""
        return [
            app_commands.Choice(name=poste, value=poste)
            for poste in self.data.keys()
            if current.lower() in poste.lower()
        ][:25]  # Discord limite à 25 choix

    @commands.Cog.listener()
    async def on_ready(self):
        """Envoie l'organigramme au démarrage"""
        await self._update_message()
        print("✅ Organigramme mis à jour")

async def setup(bot):
    await bot.add_cog(Organigramme(bot))
