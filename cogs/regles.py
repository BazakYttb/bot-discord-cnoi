import discord
from discord.ext import commands
from config.settings import CHANNEL_REGLES, REGLES_TEXTE


class Regles(commands.Cog):
    """
    Cog pour gérer l'affichage des règles du serveur
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """
        Envoie automatiquement les règles au démarrage du bot
        """
        await self.envoyer_regles()
    
    async def envoyer_regles(self):
        """
        Envoie ou met à jour les règles dans le channel dédié
        """
        try:
            channel = self.bot.get_channel(CHANNEL_REGLES)
            
            if channel is None:
                print(f"⚠️ Channel règles introuvable (ID: {CHANNEL_REGLES})")
                return
            
            # Supprime les anciens messages du bot dans le channel
            async for message in channel.history(limit=100):
                if message.author == self.bot.user:
                    await message.delete()
            
            # Crée un embed stylé pour les règles
            embed = discord.Embed(
                title="📜 Règles du Serveur",
                description=REGLES_TEXTE,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Merci de respecter ces règles pour une bonne ambiance !")
            
            await channel.send(embed=embed)
            print(f"✅ Règles envoyées dans #{channel.name}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi des règles: {e}")
    
    @discord.app_commands.command(
        name="regles",
        description="Renvoie les règles du serveur dans le channel approprié"
    )
    @discord.app_commands.default_permissions(administrator=True)
    async def regles_command(self, interaction: discord.Interaction):
        """
        Commande réservée aux admins pour renvoyer les règles manuellement
        """
        await interaction.response.defer(ephemeral=True)
        await self.envoyer_regles()
        await interaction.followup.send("✅ Règles renvoyées avec succès!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Regles(bot))
