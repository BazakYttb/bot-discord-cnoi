import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os

class Statistiques(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/stats.json'
        os.makedirs('data', exist_ok=True)
        self.stats = self.load_data()
    
    def load_data(self):
        """Charge les stats depuis le JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            print("⚠️  Fichier stats.json corrompu, réinitialisation...")
        return {}
    
    def save_data(self):
        """Sauvegarde les stats dans le JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4, ensure_ascii=False)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Enregistre les messages pour les stats"""
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Initialisation si nécessaire
        if user_id not in self.stats:
            self.stats[user_id] = {
                'messages_total': 0,
                'messages_semaine': {},
                'date_arrivee': datetime.utcnow().isoformat()
            }
        
        # Incrémentation
        self.stats[user_id]['messages_total'] += 1
        
        if today not in self.stats[user_id]['messages_semaine']:
            self.stats[user_id]['messages_semaine'][today] = 0
        self.stats[user_id]['messages_semaine'][today] += 1
        
        self.save_data()
    
    @app_commands.command(
        name="stats",
        description="Voir les statistiques du serveur ou d'un membre"
    )
    @app_commands.describe(
        type="Type de statistiques à afficher",
        membre="Membre à consulter (pour stats membre)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="📊 Statistiques du Serveur", value="serveur"),
        app_commands.Choice(name="👤 Statistiques d'un Membre", value="membre")
    ])
    async def stats(
        self, 
        interaction: discord.Interaction, 
        type: app_commands.Choice[str],
        membre: discord.Member = None
    ):
        """Affiche les statistiques"""
        
        if type.value == "serveur":
            await self.stats_serveur(interaction)
        elif type.value == "membre":
            await self.stats_membre(interaction, membre)
    
    async def stats_serveur(self, interaction: discord.Interaction):
        """Stats globales du serveur"""
        guild = interaction.guild
        
        # Calcul des membres actifs (cette semaine)
        semaine_passee = datetime.utcnow() - timedelta(days=7)
        actifs_semaine = 0
        
        for user_id, data in self.stats.items():
            for date_str, count in data.get('messages_semaine', {}).items():
                date = datetime.fromisoformat(date_str + "T00:00:00")
                if date >= semaine_passee and count > 0:
                    actifs_semaine += 1
                    break
        
        # Candidatures en attente (si le cog existe)
        candidatures_cog = self.bot.get_cog('Candidatures')
        tickets_ouverts = 0
        if candidatures_cog:
            category = guild.get_channel(int(os.getenv('CATEGORY_TICKETS')))
            if category:
                tickets_ouverts = len(category.channels)
        
        # Postes vacants (si le cog existe)
        organigramme_cog = self.bot.get_cog('Organigramme')
        postes_vacants = 0
        if organigramme_cog:
            postes_vacants = sum(
                1 for poste in organigramme_cog.data.values() 
                if "vacant" in poste.lower()
            )
        
        # Création de l'embed
        embed = discord.Embed(
            title=f"📊 Statistiques de {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(
            name="👥 Membres",
            value=f"**Total :** {guild.member_count}\n**Actifs (7j) :** {actifs_semaine}\n**En ligne :** {sum(1 for m in guild.members if m.status != discord.Status.offline)}",
            inline=True
        )
        
        embed.add_field(
            name="📝 Activité",
            value=f"**Candidatures :** {tickets_ouverts}\n**Postes Vacants :** {postes_vacants}\n**Salons :** {len(guild.channels)}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Serveur",
            value=f"**Créé le :** {guild.created_at.strftime('%d/%m/%Y')}\n**Région :** {guild.preferred_locale}\n**Boost :** Niveau {guild.premium_tier}",
            inline=True
        )
        
        embed.set_footer(text="Données en temps réel")
        
        await interaction.response.send_message(embed=embed)
    
    async def stats_membre(self, interaction: discord.Interaction, membre: discord.Member = None):
        """Stats individuelles d'un membre"""
        target = membre or interaction.user
        user_id = str(target.id)
        
        # Récupération des stats
        if user_id not in self.stats:
            return await interaction.response.send_message(
                f"❌ Aucune statistique disponible pour {target.mention}",
                ephemeral=True
            )
        
        data = self.stats[user_id]
        
        # Calcul messages cette semaine
        semaine_passee = datetime.utcnow() - timedelta(days=7)
        messages_semaine = 0
        
        for date_str, count in data.get('messages_semaine', {}).items():
            date = datetime.fromisoformat(date_str + "T00:00:00")
            if date >= semaine_passee:
                messages_semaine += count
        
        # Date d'arrivée
        date_arrivee = datetime.fromisoformat(data['date_arrivee'])
        jours_presence = (datetime.utcnow() - date_arrivee).days
        
        # Embed
        embed = discord.Embed(
            title=f"📊 Statistiques de {target.display_name}",
            color=target.color,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(
            name="💬 Messages",
            value=f"**Total :** {data['messages_total']}\n**Cette semaine :** {messages_semaine}\n**Moyenne/jour :** {data['messages_total'] // max(jours_presence, 1)}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Présence",
            value=f"**Arrivé le :** {date_arrivee.strftime('%d/%m/%Y')}\n**Depuis :** {jours_presence} jours\n**Rôle principal :** {target.top_role.mention}",
            inline=True
        )
        
        # Fiche personnage (si elle existe)
        personnages_cog = self.bot.get_cog('Personnages')
        if personnages_cog and user_id in personnages_cog.personnages:
            perso = personnages_cog.personnages[user_id]
            embed.add_field(
                name="🎭 Personnage RP",
                value=f"**Nom :** {perso['nom_rp']}\n**Âge :** {perso['age']} ans",
                inline=False
            )
        
        embed.set_footer(text=f"ID : {target.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="leaderboard",
        description="Classement des membres les plus actifs"
    )
    @app_commands.describe(
        periode="Période du classement"
    )
    @app_commands.choices(periode=[
        app_commands.Choice(name="📅 Cette semaine", value="semaine"),
        app_commands.Choice(name="📊 Total (all-time)", value="total")
    ])
    async def leaderboard(self, interaction: discord.Interaction, periode: app_commands.Choice[str]):
        """Affiche le classement des membres"""
        
        if periode.value == "total":
            # Classement total
            classement = sorted(
                self.stats.items(),
                key=lambda x: x[1]['messages_total'],
                reverse=True
            )[:10]
            
            titre = "🏆 TOP 10 - Messages Total"
            description = ""
            
            for i, (user_id, data) in enumerate(classement, 1):
                member = interaction.guild.get_member(int(user_id))
                if member:
                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"**{i}.**"
                    description += f"{medal} {member.mention} - **{data['messages_total']}** messages\n"
        
        else:  # semaine
            # Calcul messages cette semaine
            semaine_passee = datetime.utcnow() - timedelta(days=7)
            scores = {}
            
            for user_id, data in self.stats.items():
                score = 0
                for date_str, count in data.get('messages_semaine', {}).items():
                    date = datetime.fromisoformat(date_str + "T00:00:00")
                    if date >= semaine_passee:
                        score += count
                if score > 0:
                    scores[user_id] = score
            
            classement = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
            
            titre = "🏆 TOP 10 - Cette Semaine"
            description = ""
            
            for i, (user_id, score) in enumerate(classement, 1):
                member = interaction.guild.get_member(int(user_id))
                if member:
                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"**{i}.**"
                    description += f"{medal} {member.mention} - **{score}** messages\n"
        
        embed = discord.Embed(
            title=titre,
            description=description or "Aucune donnée disponible",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text="Classement mis à jour en temps réel")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistiques(bot))
