import discord
from discord import app_commands
from discord.ext import commands
from config.settings import CHANNEL_IDEES


class ModalIdee(discord.ui.Modal, title="📝 Proposer une Idée"):
    """
    Modal (formulaire) pour soumettre une idée
    """
    
    # Champ titre (obligatoire)
    titre = discord.ui.TextInput(
        label="Titre de l'idée",
        placeholder="Ex: Ajouter un système de niveaux",
        required=True,
        max_length=100
    )
    
    # Champ description (obligatoire)
    description = discord.ui.TextInput(
        label="Description détaillée",
        placeholder="Décrivez votre idée en détail...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    # Champ images (optionnel)
    images = discord.ui.TextInput(
        label="Liens d'images (optionnel)",
        placeholder="https://exemple.com/image1.png, https://exemple.com/image2.png",
        required=False,
        max_length=500
    )
    
    def __init__(self, channel_idees):
        super().__init__()
        self.channel_idees = channel_idees
    
    async def on_submit(self, interaction: discord.Interaction):
        """
        Appelé quand l'utilisateur valide le formulaire
        """
        # Création de l'embed pour l'idée
        embed = discord.Embed(
            title=f"💡 {self.titre.value}",
            description=self.description.value,
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_author(
            name=f"Proposé par {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Ajoute les images si fournies
        if self.images.value:
            # Prend la première URL comme image principale
            urls = [url.strip() for url in self.images.value.split(',')]
            if urls and urls[0].startswith('http'):
                embed.set_image(url=urls[0])
            
            # Ajoute les autres URLs dans un champ
            if len(urls) > 1:
                embed.add_field(
                    name="📎 Images supplémentaires",
                    value="\n".join([f"[Image {i+1}]({url})" for i, url in enumerate(urls[1:])]),
                    inline=False
                )
        
        embed.set_footer(text="Réagissez avec 👍 ou 👎 pour voter!")
        
        # Envoie l'idée dans le channel
        message = await self.channel_idees.send(embed=embed)
        
        # Ajoute les réactions automatiquement
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        
        # Confirmation à l'utilisateur
        await interaction.response.send_message(
            "✅ Ton idée a été publiée avec succès!",
            ephemeral=True
        )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """
        Gestion des erreurs du modal
        """
        await interaction.response.send_message(
            f"❌ Une erreur est survenue: {str(error)}",
            ephemeral=True
        )


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
    async def idee(self, interaction: discord.Interaction):
        """
        Commande pour ouvrir le formulaire de soumission d'idée
        """
        # Vérifie qu'on est dans le bon channel
        if interaction.channel_id != CHANNEL_IDEES:
            channel_mention = f"<#{CHANNEL_IDEES}>"
            await interaction.response.send_message(
                f"⚠️ Cette commande ne fonctionne que dans {channel_mention}!",
                ephemeral=True
            )
            return
        
        # Récupère le channel des idées
        channel_idees = self.bot.get_channel(CHANNEL_IDEES)
        
        if channel_idees is None:
            await interaction.response.send_message(
                "❌ Channel des idées introuvable!",
                ephemeral=True
            )
            return
        
        # Ouvre le modal (formulaire)
        modal = ModalIdee(channel_idees)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(Idees(bot))
