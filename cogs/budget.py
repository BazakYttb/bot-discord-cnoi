import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

class Budget(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/budget.json"
        self.budget_data = self.load_data()

    def load_data(self):
        """Charge les données du budget depuis le fichier JSON"""
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "solde": 0,
                "transactions": []
            }

    def save_data(self):
        """Sauvegarde les données du budget"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.budget_data, f, indent=4, ensure_ascii=False)

    def ajouter_transaction(self, montant: float, type_transaction: str, description: str, auteur: str):
        """Ajoute une transaction au système"""
        transaction = {
            "date": datetime.now().isoformat(),
            "montant": montant,
            "type": type_transaction,
            "description": description,
            "auteur": auteur
        }
        
        self.budget_data["transactions"].append(transaction)
        
        if type_transaction == "entree":
            self.budget_data["solde"] += montant
        else:
            self.budget_data["solde"] -= montant
        
        self.save_data()

    def generer_graphique(self) -> BytesIO:
        """Génère un graphique de l'évolution du budget"""
        if not self.budget_data["transactions"]:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Aucune donnée disponible', 
                   ha='center', va='center', fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            dates = []
            soldes = []
            solde_cumul = 0
            
            for trans in self.budget_data["transactions"]:
                date = datetime.fromisoformat(trans["date"])
                dates.append(date)
                
                if trans["type"] == "entree":
                    solde_cumul += trans["montant"]
                else:
                    solde_cumul -= trans["montant"]
                
                soldes.append(solde_cumul)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dates, soldes, marker='o', linewidth=2, markersize=6, color='#5865F2')
            ax.fill_between(dates, soldes, alpha=0.3, color='#5865F2')
            
            ax.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax.set_ylabel('Solde (€)', fontsize=12, fontweight='bold')
            ax.set_title('Évolution du Budget', fontsize=14, fontweight='bold')
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            plt.xticks(rotation=45)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer

    @app_commands.command(name="budget_voir", description="💰 Voir le budget actuel")
    async def budget_voir(self, interaction: discord.Interaction):
        """Affiche le budget avec graphique"""
        
        # Génération du graphique
        graphique = self.generer_graphique()
        
        # Calcul des statistiques
        total_entrees = sum(t["montant"] for t in self.budget_data["transactions"] if t["type"] == "entree")
        total_sorties = sum(t["montant"] for t in self.budget_data["transactions"] if t["type"] == "sortie")
        
        # Création de l'embed
        embed = discord.Embed(
            title="💰 Budget de l'État",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💵 Solde Actuel",
            value=f"**{self.budget_data['solde']:,.2f} €**",
            inline=False
        )
        
        embed.add_field(name="📈 Entrées totales", value=f"{total_entrees:,.2f} €", inline=True)
        embed.add_field(name="📉 Sorties totales", value=f"{total_sorties:,.2f} €", inline=True)
        embed.add_field(name="🔢 Transactions", value=str(len(self.budget_data["transactions"])), inline=True)
        
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}")
        
        file = discord.File(graphique, filename="budget.png")
        embed.set_image(url="attachment://budget.png")
        
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="budget_ajouter", description="➕ Ajouter de l'argent au budget")
    @app_commands.describe(
        montant="Montant à ajouter (en euros)",
        source="Source de l'argent (ex: Impôts, Donations)"
    )
    async def budget_ajouter(self, interaction: discord.Interaction, montant: float, source: str):
        """Ajoute de l'argent au budget"""
        
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif !", ephemeral=True)
            return
        
        self.ajouter_transaction(montant, "entree", source, interaction.user.display_name)
        
        embed = discord.Embed(
            title="✅ Argent Ajouté",
            description=f"**+{montant:,.2f} €** ajoutés au budget",
            color=discord.Color.green()
        )
        embed.add_field(name="Source", value=source, inline=False)
        embed.add_field(name="Nouveau Solde", value=f"**{self.budget_data['solde']:,.2f} €**", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="budget_depenser", description="➖ Dépenser de l'argent")
    @app_commands.describe(
        montant="Montant à retirer (en euros)",
        raison="Raison de la dépense (ex: Salaires, Achats)"
    )
    async def budget_depenser(self, interaction: discord.Interaction, montant: float, raison: str):
        """Retire de l'argent du budget"""
        
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif !", ephemeral=True)
            return
        
        if montant > self.budget_data["solde"]:
            await interaction.response.send_message(
                f"❌ Fonds insuffisants ! Solde actuel : {self.budget_data['solde']:,.2f} €",
                ephemeral=True
            )
            return
        
        self.ajouter_transaction(montant, "sortie", raison, interaction.user.display_name)
        
        embed = discord.Embed(
            title="✅ Dépense Effectuée",
            description=f"**-{montant:,.2f} €** retirés du budget",
            color=discord.Color.red()
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Nouveau Solde", value=f"**{self.budget_data['solde']:,.2f} €**", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="budget_historique", description="📜 Voir l'historique des transactions")
    async def budget_historique(self, interaction: discord.Interaction):
        """Affiche les 10 dernières transactions"""
        
        if not self.budget_data["transactions"]:
            await interaction.response.send_message("📭 Aucune transaction enregistrée.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📜 Historique des Transactions",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Prendre les 10 dernières transactions
        dernieres = self.budget_data["transactions"][-10:][::-1]
        
        for trans in dernieres:
            date = datetime.fromisoformat(trans["date"]).strftime("%d/%m/%Y %H:%M")
            signe = "+" if trans["type"] == "entree" else "-"
            symbole = "📈" if trans["type"] == "entree" else "📉"
            
            embed.add_field(
                name=f"{symbole} {date}",
                value=f"**{signe}{trans['montant']:,.2f} €** - {trans['description']}\n*Par {trans['auteur']}*",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="budget_reset", description="🔄 Réinitialiser le budget (ADMIN)")
    @app_commands.checks.has_permissions(administrator=True)
    async def budget_reset(self, interaction: discord.Interaction):
        """Réinitialise complètement le budget"""
        
        self.budget_data = {
            "solde": 0,
            "transactions": []
        }
        self.save_data()
        
        await interaction.response.send_message("✅ Le budget a été réinitialisé à zéro.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Budget(bot))
