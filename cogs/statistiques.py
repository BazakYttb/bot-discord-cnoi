import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import Counter

class Statistiques(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/stats.json"
        self.stats = self.load_stats()

    def load_stats(self):
        """Charge les statistiques depuis le fichier JSON"""
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Fichier stats.json corrompu, réinitialisation...")
                return self.init_stats()
        return self.init_stats()

    def init_stats(self):
        """Initialise la structure des stats"""
        return {
            "serveur": {
                "messages_total": 0,
                "commandes_utilisees": 0,
                "membres_rejoints": 0,
                "membres_partis": 0
            },
            "membres": {}
        }

    def save_stats(self):
        """Sauvegarde les statistiques"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4, ensure_ascii=False)

    def update_member_stats(self, user_id: int, stat_type: str, increment: int = 1):
        """Met à jour les stats d'un membre"""
        user_id = str(user_id)
        
        if user_id not in self.stats["membres"]:
            self.stats["membres"][user_id] = {
                "messages": 0,
                "commandes": 0,
                "reactions": 0,
                "derniere_activite": datetime.now().isoformat()
            }
        
        if stat_type in self.stats["membres"][user_id]:
            self.stats["membres"][user_id][stat_type] += increment
            self.stats["membres"][user_id]["derniere_activite"] = datetime.now().isoformat()
        
        self.save_stats()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Compte les messages (sauf bots)"""
        if message.author.bot:
            return
        
        self.stats["serveur"]["messages_total"] += 1
        self.update_member_stats(message.author.id, "messages")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Compte les arrivées"""
        self.stats["serveur"]["membres_rejoints"] += 1
        self.save_stats()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Compte les départs"""
        self.stats["serveur"]["membres_partis"] += 1
        self.save_stats()

    @app_commands.command(name="stats", description="Afficher les statistiques du serveur ou d'un membre")
    @app_commands.describe(
        type="Type de statistiques",
        membre="Membre à consulter (optionnel)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Serveur", value="serveur"),
        app_commands.Choice(name="Membre", value="membre")
    ])
    async def stats(
        self,
        interaction: discord.Interaction,
        type: app_commands.Choice[str],
        membre: discord.Member = None
    ):
        """Affiche les statistiques"""
        
        if type.value == "serveur":
            stats = self.stats["serveur"]
            
            embed = discord.Embed(
                title="📊 Statistiques du Serveur",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="💬 Messages",
                value=f"`{stats['messages_total']:,}`",
                inline=True
            )
            
            embed.add_field(
                name="📥 Arrivées",
                value=f"`{stats['membres_rejoints']}`",
                inline=True
            )
            
            embed.add_field(
                name="📤 Départs",
                value=f"`{stats['membres_partis']}`",
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
            embed.add_field(name="😊 Réactions", value=f"`{stats['reactions']}`", inline=True)
            
            embed.set_thumbnail(url=target.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistiques(bot))
