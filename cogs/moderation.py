import discord
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="clear",
        description="🗑️ Supprimer des messages dans un salon"
    )
    @app_commands.describe(
        nombre="Nombre de messages à supprimer (max 100)",
        membre="Supprimer uniquement les messages d'un membre spécifique (optionnel)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        nombre: int,
        membre: discord.Member = None
    ):
        # Vérification du nombre
        if nombre < 1 or nombre > 100:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Le nombre doit être entre 1 et 100.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Réponse immédiate pour éviter le timeout
        await interaction.response.defer(ephemeral=True)
        
        channel = interaction.channel
        
        try:
            if membre:
                # Supprime uniquement les messages d'un membre spécifique
                deleted = await channel.purge(
                    limit=nombre,
                    check=lambda m: m.author == membre
                )
                description = f"✅ {len(deleted)} message(s) de {membre.mention} supprimé(s)."
            else:
                # Supprime tous les messages
                deleted = await channel.purge(limit=nombre)
                description = f"✅ {len(deleted)} message(s) supprimé(s)."
            
            embed = discord.Embed(
                title="🗑️ Messages Supprimés",
                description=description,
                color=discord.Color.green()
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Manquante",
                description="Je n'ai pas la permission de supprimer des messages.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur est survenue : {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="clear_all",
        description="⚠️ DANGER : Supprimer TOUS les messages du salon actuel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_all(self, interaction: discord.Interaction):
        # Bouton de confirmation
        view = ConfirmView(interaction.user)
        
        embed = discord.Embed(
            title="⚠️ CONFIRMATION REQUISE",
            description=(
                "**ATTENTION : Cette action va supprimer TOUS les messages de ce salon !**\n\n"
                "Cela peut prendre du temps et est **irréversible**.\n\n"
                "Êtes-vous absolument certain ?"
            ),
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        # Attend la réponse
        await view.wait()
        
        if view.value:
            await interaction.followup.send("🗑️ Suppression en cours...", ephemeral=True)
            
            channel = interaction.channel
            deleted_count = 0
            
            try:
                while True:
                    # Discord limite à 100 messages par purge
                    deleted = await channel.purge(limit=100)
                    deleted_count += len(deleted)
                    
                    if len(deleted) < 100:
                        break
                
                embed = discord.Embed(
                    title="✅ Salon Nettoyé",
                    description=f"**{deleted_count}** messages supprimés avec succès.",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description=f"Erreur lors de la suppression : {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

class ConfirmView(discord.ui.View):
    """Vue de confirmation pour clear_all"""
    def __init__(self, user):
        super().__init__(timeout=30)
        self.value = None
        self.user = user
    
    @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "❌ Seul l'auteur de la commande peut confirmer.",
                ephemeral=True
            )
        
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "❌ Seul l'auteur de la commande peut annuler.",
                ephemeral=True
            )
        
        self.value = False
        self.stop()
        
        embed = discord.Embed(
            title="✅ Annulé",
            description="Aucun message n'a été supprimé.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
