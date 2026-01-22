import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
from discord.ui import Modal, TextInput

class PersonnageModal(Modal, title="Fiche Personnage RP"):
    nom_rp = TextInput(
        label="Nom RP",
        placeholder="Ex: Jean Dupont",
        required=True,
        max_length=50
    )
    
    age = TextInput(
        label="Âge",
        placeholder="Ex: 25 ans",
        required=True,
        max_length=20
    )
    
    origine = TextInput(
        label="Origine",
        placeholder="Ex: Paris, France",
        required=True,
        max_length=100
    )
    
    histoire = TextInput(
        label="Histoire (optionnel)",
        placeholder="Raconte l'histoire de ton personnage...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = str(user_id)
        
        # Pré-remplir si le personnage existe
        if self.user_id in self.cog.personnages:
            perso = self.cog.personnages[self.user_id]
            self.nom_rp.default = perso.get("nom_rp", "")
            self.age.default = perso.get("age", "")
            self.origine.default = perso.get("origine", "")
            self.histoire.default = perso.get("histoire", "")

    async def on_submit(self, interaction: discord.Interaction):
        self.cog.personnages[self.user_id] = {
            "nom_rp": self.nom_rp.value,
            "age": self.age.value,
            "origine": self.origine.value,
            "histoire": self.histoire.value or "Aucune histoire",
            "discord_name": str(interaction.user),
            "date_creation": datetime.now().isoformat()
        }
        
        # ✅ SAUVEGARDE IMMÉDIATE
        self.cog.save_data()
        
        embed = discord.Embed(
            title="✅ Personnage Enregistré !",
            description=f"**{self.nom_rp.value}** a été créé avec succès.",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Âge", value=self.age.value, inline=True)
        embed.add_field(name="🌍 Origine", value=self.origine.value, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Personnages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/personnages.json"
        self.personnages = self.load_data()
    
    def load_data(self):
        """Charge les données depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Erreur chargement personnages : {e}")
                return {}
        return {}
    
    def save_data(self):
        """Sauvegarde les données dans le fichier JSON"""
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.personnages, f, indent=2, ensure_ascii=False)
            print(f"💾 Personnages sauvegardés ({len(self.personnages)} fiches)")
        except Exception as e:
            print(f"❌ Erreur sauvegarde personnages : {e}")
    
    @app_commands.command(name="creer_personnage", description="Créer ou modifier ta fiche personnage RP")
    async def creer_personnage(self, interaction: discord.Interaction):
        modal = PersonnageModal(self, interaction.user.id)
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="voir_personnage", description="Voir la fiche d'un personnage")
    async def voir_personnage(self, interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        user_id = str(target.id)
        
        if user_id not in self.personnages:
            embed = discord.Embed(
                title="❌ Aucun Personnage",
                description=f"{target.mention} n'a pas encore créé de personnage.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        perso = self.personnages[user_id]
        
        embed = discord.Embed(
            title=f"📋 Fiche de {perso['nom_rp']}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👤 Âge", value=perso['age'], inline=True)
        embed.add_field(name="🌍 Origine", value=perso['origine'], inline=True)
        embed.add_field(name="📖 Histoire", value=perso['histoire'], inline=False)
        embed.add_field(name="💬 Discord", value=perso['discord_name'], inline=True)
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Créé le {perso['date_creation'][:10]}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Personnages(bot))
