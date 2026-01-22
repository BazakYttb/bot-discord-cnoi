import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class Statistiques(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/statistiques.json"
        self.stats = self.load_data()
    
    def load_data(self):
        """Charge les stats depuis le JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"serveur": {"messages": 0, "commandes": 0}, "membres": {}}
        return {"serveur": {"messages": 0, "commandes": 0}, "membres": {}}
    
    def save_data(self):
        """Sauvegarde les stats"""
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur sauvegarde stats : {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Stats serveur
        self.stats["serveur"]["messages"] += 1
        
        # Stats membre
        user_id = str(message.author.id)
        if user_id not in self.stats["membres"]:
            self.stats["membres"][user_id] = {
                "messages": 0,
                "commandes": 0,
                "reactions": 0
            }
        
        self.stats["membres"][user_id]["messages"] += 1
        self.save_data()  # ✅ SAUVEGARDE AUTO
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            self.stats["serveur"]["commandes"] += 1
            
            user_id = str(interaction.user.id)
            if user_id in self.stats["membres"]:
                self.stats["membres"][user_id]["commandes"] += 1
            
            self.save_data()  # ✅ SAUVEGARDE AUTO
    
    @app_commands.command(name="stats", description="Voir les statistiques")
    @app_commands.describe(
        type="Type de statistiques",
        membre="Membre ciblé (optionnel)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Serveur", value="serveur"),
        app_commands.Choice(name="Membre", value="membre")
    ])
    async def stats(self, interaction: discord.Interaction, type: app_commands.Choice[str], membre: discord.Member = None):
        if type.value == "serveur":
            embed = discord.Embed(
                title="📊 Statistiques du Serveur",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="💬 Messages Totaux",
                value=f"`{self.stats['serveur']['messages']}`",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Commandes Utilisées",
                value=f"`{self.stats['serveur']['commandes']}`",
                inline=True
            )
            
            embed.add_field(
                name="👥 Membres Actifs",
                value=f"`{len(self.stats['membres'])}`",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
        
        elif type.value == "membre":
            target = membre or interaction.user
            user_id = str(target.id)
            
            if user_id not in self.stats["membres"]:
                embed = discord.Embed(
                    title="❌ Aucune Donnée",
                    description=f"{target.mention} n'a pas encore d'activité enregistrée.",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            stats = self.stats["membres"][user_id]
            
            embed = discord.Embed(
                title=f"📊 Statistiques de {target.display_name}",
                color=discord.Color.green()
            )
            
            embed.add_field(name="💬 Messages", value=f"`{stats['messages']}`", inline=True)
            embed.add_field(name="⚡ Commandes", value=f"`{stats['commandes']}`", inline=True)
            embed.add_field(name="😊 Réactions", value=f"`{stats.get('reactions', 0)}`", inline=True)
            
            embed.set_thumbnail(url=target.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistiques(bot))
