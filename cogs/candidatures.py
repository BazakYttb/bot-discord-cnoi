import discord
from discord import app_commands
from discord.ext import commands
from config.settings import (
    CHANNEL_CANDIDATURES, 
    CATEGORY_TICKETS, 
    ROLE_STAFF, 
    POSTES_DISPONIBLES
)
import asyncio

class CandidatureView(discord.ui.View):
    """
    Vue persistante pour le menu déroulant de candidatures
    """
    def __init__(self):
        super().__init__(timeout=None)  # Persist après redémarrage
        self.add_item(CandidatureSelect())

class CandidatureSelect(discord.ui.Select):
    """
    Menu déroulant pour choisir le poste
    """
    def __init__(self):
        options = [
            discord.SelectOption(
                label=poste, 
                emoji=emoji,
                description=f"Postuler pour {poste}"
            )
            for poste, emoji in POSTES_DISPONIBLES.items()
        ]
        
        super().__init__(
            placeholder="Sélectionnez la raison de votre ticket",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="candidature_select"  # ID persistant
        )
    
    async def callback(self, interaction: discord.Interaction):
        poste_choisi = self.values[0]
        await creer_ticket_candidature(interaction, poste_choisi)

async def creer_ticket_candidature(interaction: discord.Interaction, poste: str):
    """
    Crée un ticket privé pour la candidature
    """
    guild = interaction.guild
    category = guild.get_channel(CATEGORY_TICKETS)
    role_staff = guild.get_role(ROLE_STAFF)
    
    if not category:
        await interaction.response.send_message(
            "❌ Erreur : Catégorie de tickets introuvable.",
            ephemeral=True
        )
        return
    
    # Création du salon ticket
    ticket_channel = await category.create_text_channel(
        name=f"candidature-{interaction.user.name}",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
    )
    
    # Message de confirmation
    await interaction.response.send_message(
        f"✅ Votre ticket de candidature pour **{poste}** a été créé : {ticket_channel.mention}",
        ephemeral=True
    )
    
    # Embed dans le ticket
    embed = discord.Embed(
        title=f"🎫 Candidature : {poste}",
        description=(
            f"**Candidat :** {interaction.user.mention}\n\n"
            "**Merci de répondre aux questions suivantes :**\n\n"
            "1️⃣ **Votre âge :**\n"
            "2️⃣ **Vos connaissances en RP :**\n"
            "3️⃣ **Vos motivations :**\n"
            "4️⃣ **Votre nom RP :**\n"
            "5️⃣ **Votre personnage RP :**\n"
            "6️⃣ **Description du personnage RP :**\n\n"
            f"*Un membre du {role_staff.mention} vous répondra prochainement.*"
        ),
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    
    embed.set_footer(text="Répondez directement dans ce salon")
    
    # Envoi du message + ping staff
    await ticket_channel.send(
        content=f"{role_staff.mention}",
        embed=embed
    )

class Candidatures(commands.Cog):
    """
    Cog pour gérer le système de candidatures avec tickets
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ajoute la vue persistante au bot au démarrage
        """
        self.bot.add_view(CandidatureView())
        print("  ✅ Vue de candidatures chargée")
    
    @app_commands.command(
        name="setup_candidatures",
        description="[ADMIN] Envoie le message de candidatures dans le salon"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_candidatures(self, interaction: discord.Interaction):
        """
        Envoie le message avec le menu déroulant
        """
        if interaction.channel_id != CHANNEL_CANDIDATURES:
            await interaction.response.send_message(
                f"❌ Cette commande doit être utilisée dans <#{CHANNEL_CANDIDATURES}>",
                ephemeral=True
            )
            return
        
        # Création de l'embed
        embed = discord.Embed(
            title="🎫 Système de tickets",
            description=(
                "**Besoin d'aide ?** Créez un ticket en sélectionnant la raison ci-dessous.\n\n"
                "Notre équipe vous répondra dans les **plus brefs délais**."
            ),
            color=discord.Color.blue()
        )
        
        # Envoi du message avec le menu
        await interaction.channel.send(
            embed=embed,
            view=CandidatureView()
        )
        
        await interaction.response.send_message(
            "✅ Message de candidatures envoyé !",
            ephemeral=True
        )
    
    @app_commands.command(
        name="fermer_ticket",
        description="[STAFF] Ferme le ticket actuel"
    )
    @app_commands.checks.has_role(ROLE_STAFF)
    async def fermer_ticket(self, interaction: discord.Interaction):
        """
        Ferme le ticket (supprime le salon)
        """
        if not interaction.channel.name.startswith("candidature-"):
            await interaction.response.send_message(
                "❌ Cette commande ne peut être utilisée que dans un ticket de candidature.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "🔒 **Ticket fermé.** Ce salon sera supprimé dans 5 secondes...",
            ephemeral=False
        )
        
        await asyncio.sleep(5)
        await interaction.channel.delete(reason="Ticket fermé par le staff")

async def setup(bot):
    await bot.add_cog(Candidatures(bot))
