import discord
from discord import app_commands
from discord.ext import commands
from config.settings import CHANNEL_IDEES

class Idees(commands.Cog):
    """
    Cog pour gérer le système de propositions d'idées
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="idee",
        description="Proposer une nouvelle idée pour le serveur"
    )
    @app_commands.describe(
        titre="Le titre de votre idée (court et explicite)",
        description="Description détaillée de votre idée",
        image="URL d'une image illustrant votre idée (optionnel)"
    )
    async def idee(
        self, 
        interaction: discord.Interaction,
        titre: str,
        description: str,
        image: str = None
    ):
        """
        Commande pour soumettre une idée avec titre, description et image optionnelle
        """
        
        # ✅ Vérifie qu'on est dans le bon channel
        if interaction.channel_id != CHANNEL_IDEES:
            channel_mention = f"<#{CHANNEL_IDEES}>"
            await interaction.response.send_message(
                f"❌ Cette commande ne peut être utilisée que dans {channel_mention}",
                ephemeral=True
            )
            return
        
        # ✅ Validation de l'URL de l'image (si fournie)
        if image and not (image.startswith('http://') or image.startswith('https://')):
            await interaction.response.send_message(
                "❌ L'URL de l'image doit commencer par `http://` ou `https://`",
                ephemeral=True
            )
            return
        
        # ✅ Création de l'embed
        embed = discord.Embed(
            title=f"💡 {titre}",
            description=description,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Ajout de l'auteur
        embed.set_author(
            name=f"Proposé par {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Ajout de l'image si fournie
        if image:
            embed.set_image(url=image)
        
        # Footer
        embed.set_footer(text="Réagissez avec 👍 pour approuver ou 👎 pour désapprouver")
        
        # ✅ Réponse éphémère à l'utilisateur
        await interaction.response.send_message(
            "✅ Votre idée a été publiée avec succès !",
            ephemeral=True
        )
        
        # ✅ Publication de l'embed dans le channel
        message = await interaction.channel.send(embed=embed)
        
        # ✅ Ajout des réactions
        await message.add_reaction("👍")
        await message.add_reaction("👎")

# ⚠️ CETTE FONCTION EST OBLIGATOIRE ⚠️
async def setup(bot):
    """
    Fonction appelée par bot.load_extension()
    """
    await bot.add_cog(Idees(bot))
