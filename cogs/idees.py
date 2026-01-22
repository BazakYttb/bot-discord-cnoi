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
        
        Args:
            titre: Titre de l'idée (obligatoire)
            description: Description détaillée (obligatoire)
            image: URL de l'image (optionnel)
        """
        
        # ✅ Vérifie qu'on est dans le bon channel
        if interaction.channel_id != CHANNEL_IDEES:
            channel_mention = f"<#{CHANNEL_IDEES}>"
            await interaction.response.send_message(
                f"❌ Cette commande ne peut être utilisée que dans {channel_mention}",
                ephemeral=True
            )
            return
        
        # ✅ Validation du titre (max 100 caractères)
        if len(titre) > 100:
            await interaction.response.send_message(
                "❌ Le titre ne peut pas dépasser 100 caractères !",
                ephemeral=True
            )
            return
        
        # ✅ Validation de la description (max 1000 caractères)
        if len(description) > 1000:
            await interaction.response.send_message(
                "❌ La description ne peut pas dépasser 1000 caractères !",
                ephemeral=True
            )
            return
        
        # ✅ Validation de l'URL de l'image (si fournie)
        if image:
            if not image.startswith(('http://', 'https://')):
                await interaction.response.send_message(
                    "❌ L'URL de l'image doit commencer par `http://` ou `https://`",
                    ephemeral=True
                )
                return
            
            # Vérifie que c'est bien une image
            extensions_valides = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            if not any(image.lower().endswith(ext) for ext in extensions_valides):
                await interaction.response.send_message(
                    f"❌ L'image doit avoir une extension valide : {', '.join(extensions_valides)}",
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
        
        # Footer avec ID de l'auteur (pour modération)
        embed.set_footer(
            text=f"ID: {interaction.user.id}"
        )
        
        # ✅ Envoi dans le channel
        try:
            message = await interaction.channel.send(embed=embed)
            
            # Ajout des réactions de vote
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            
            # Confirmation à l'utilisateur
            await interaction.response.send_message(
                "✅ Votre idée a été publiée avec succès !",
                ephemeral=True
            )
            
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Erreur lors de la publication : {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Idees(bot))
