import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class Personnages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/personnages.json'
        os.makedirs('data', exist_ok=True)
        self.personnages = self.load_data()
    
    def load_data(self):
        """Charge les personnages depuis le JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            print("⚠️  Fichier personnages.json corrompu, réinitialisation...")
        return {}
    
    def save_data(self):
        """Sauvegarde les personnages dans le JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.personnages, f, indent=4, ensure_ascii=False)
    
    @app_commands.command(
        name="personnage",
        description="Créer ou consulter une fiche personnage RP"
    )
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
                return await interaction.response.send_message(
                    f"❌ {target.mention} n'a pas encore créé de fiche personnage !",
                    ephemeral=True
                )
            
            # Récupération des données
            data = self.personnages[user_id]
            
            # Création de l'embed
            embed = discord.Embed(
                title=f"📜 Fiche Personnage de {data['nom_rp']}",
                color=discord.Color.gold(),
                timestamp=datetime.fromisoformat(data['date_creation'])
            )
            
            embed.set_thumbnail(url=target.display_avatar.url)
            
            embed.add_field(
                name="👤 Identité",
                value=f"**Nom :** {data['nom_rp']}\n**Âge :** {data['age']} ans\n**Origine :** {data['origine']}",
                inline=False
            )
            
            embed.add_field(
                name="📖 Biographie",
                value=data['biographie'][:1024],  # Limite Discord
                inline=False
            )
            
            embed.add_field(
                name="🎭 Personnalité",
                value=data.get('personnalite', 'Non renseignée')[:1024],
                inline=False
            )
            
            embed.set_footer(text=f"Joueur Discord : {target.name}")
            
            await interaction.response.send_message(embed=embed)

class PersonnageModal(discord.ui.Modal, title="Création de Fiche Personnage"):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = str(user_id)
        
        # Pré-remplir si le personnage existe déjà
        existing = self.cog.personnages.get(self.user_id, {})
        
        self.nom_rp = discord.ui.TextInput(
            label="Nom Complet RP",
            placeholder="Ex: Jean-Baptiste de Valois",
            default=existing.get('nom_rp', ''),
            max_length=100,
            required=True
        )
        
        self.age = discord.ui.TextInput(
            label="Âge",
            placeholder="Ex: 35",
            default=existing.get('age', ''),
            max_length=3,
            required=True
        )
        
        self.origine = discord.ui.TextInput(
            label="Origine/Région",
            placeholder="Ex: Duché de Bourgogne",
            default=existing.get('origine', ''),
            max_length=100,
            required=True
        )
        
        self.biographie = discord.ui.TextInput(
            label="Biographie",
            placeholder="Raconte l'histoire de ton personnage...",
            default=existing.get('biographie', ''),
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        self.personnalite = discord.ui.TextInput(
            label="Personnalité/Traits",
            placeholder="Ex: Ambitieux, rusé, loyal...",
            default=existing.get('personnalite', ''),
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False
        )
        
        self.add_item(self.nom_rp)
        self.add_item(self.age)
        self.add_item(self.origine)
        self.add_item(self.biographie)
        self.add_item(self.personnalite)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Sauvegarde des données
        self.cog.personnages[self.user_id] = {
            'nom_rp': self.nom_rp.value,
            'age': self.age.value,
            'origine': self.origine.value,
            'biographie': self.biographie.value,
            'personnalite': self.personnalite.value,
            'date_creation': datetime.utcnow().isoformat()
        }
        self.cog.save_data()
        
        # Confirmation
        embed = discord.Embed(
            title="✅ Fiche Personnage Enregistrée",
            description=f"**{self.nom_rp.value}** est maintenant créé(e) !\n\nUtilise `/personnage voir` pour la consulter.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Personnages(bot))
