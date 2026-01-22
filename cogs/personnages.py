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
        
        # Pré-remplir si le personnage existe déjà
        if self.user_id in self.cog.personnages:
            perso = self.cog.personnages[self.user_id]
            self.nom_rp.default = perso.get("nom_rp", "")
            self.age.default = perso.get("age", "")
            self.origine.default = perso.get("origine", "")
            self.histoire.default = perso.get("histoire", "")

    async def on_submit(self, interaction: discord.Interaction):
        # Sauvegarde dans la base de données
        self.cog.personnages[self.user_id] = {
            "nom_rp": self.nom_rp.value,
            "age": self.age.value,
            "origine": self.origine.value,
            "histoire": self.histoire.value,
            "date_creation": datetime.now().isoformat()
        }
        
        self.cog.save_personnages()
        
        embed = discord.Embed(
            title="✅ Fiche Personnage Enregistrée",
            description=f"**{self.nom_rp.value}** a été créé/modifié avec succès !",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Personnages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/personnages.json"
        self.personnages = self.load_personnages()

    def load_personnages(self):
        """Charge les personnages depuis le fichier JSON"""
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Fichier personnages.json corrompu, réinitialisation...")
                return {}
        return {}

    def save_personnages(self):
        """Sauvegarde les personnages dans le fichier JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.personnages, f, indent=4, ensure_ascii=False)

    @app_commands.command(name="personnage", description="Gérer sa fiche personnage RP")
    @app_commands.describe(
        action="Action à effectuer",
        membre="Membre à consulter (optionnel pour 'voir')"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Créer/Modifier mon personnage", value="create"),
        app_commands.Choice(name="Voir un personnage", value="voir")
    ])
    async def personnage(
        self, 
        interaction: discord.Interaction, 
        action: app_commands.Choice[str],
        membre: discord.Member = None
    ):
        """Gestion des fiches personnages"""
        
        if action.value == "create":
            # Modal pour créer/modifier le personnage
            modal = PersonnageModal(self, interaction.user.id)
            await interaction.response.send_modal(modal)
        
        elif action.value == "voir":
            target = membre or interaction.user
            user_id = str(target.id)
            
            # Vérification si le personnage existe
            if user_id not in self.personnages:
                embed = discord.Embed(
                    title="❌ Aucune Fiche Trouvée",
                    description=f"{target.mention} n'a pas encore créé de personnage.",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Affichage de la fiche
            perso = self.personnages[user_id]
            
            embed = discord.Embed(
                title=f"📋 Fiche de {perso['nom_rp']}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="👤 Nom RP", value=perso['nom_rp'], inline=True)
            embed.add_field(name="🎂 Âge", value=perso['age'], inline=True)
            embed.add_field(name="🌍 Origine", value=perso['origine'], inline=True)
            
            if perso.get('histoire'):
                embed.add_field(name="📖 Histoire", value=perso['histoire'], inline=False)
            
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.set_footer(text=f"Créé le {perso['date_creation'][:10]}")
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Personnages(bot))
