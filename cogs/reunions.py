import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import asyncio

class Reunions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/reunions.json"
        self.reunions = self.load_data()
        self.check_reminders.start()  # Démarre la boucle de vérification
    
    def load_data(self):
        """Charge les réunions depuis le fichier JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_data(self):
        """Sauvegarde les réunions dans le fichier JSON"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.reunions, f, indent=4, ensure_ascii=False)
    
    def cog_unload(self):
        """Arrête la boucle lors du déchargement du cog"""
        self.check_reminders.cancel()
    
    @tasks.loop(minutes=1)  # Vérifie toutes les minutes
    async def check_reminders(self):
        """Vérifie et envoie les rappels de réunions"""
        try:
            now = datetime.now()
            reunions_a_supprimer = []
            
            for reunion in self.reunions:
                date_reunion = datetime.fromisoformat(reunion['date'])
                
                # Calcul des moments de rappel
                rappel_30min = date_reunion - timedelta(minutes=30)
                rappel_5min = date_reunion - timedelta(minutes=5)
                
                # ⏰ RAPPEL 30 MINUTES AVANT
                if not reunion.get('rappel_30min_envoye') and now >= rappel_30min and now < date_reunion:
                    await self.send_reminder(reunion, "30 minutes", discord.Color.blue())
                    reunion['rappel_30min_envoye'] = True
                    self.save_data()
                    print(f"✅ Rappel 30min envoyé pour: {reunion['titre']}")
                
                # ⏰ RAPPEL 5 MINUTES AVANT
                if not reunion.get('rappel_5min_envoye') and now >= rappel_5min and now < date_reunion:
                    await self.send_reminder(reunion, "5 minutes", discord.Color.orange())
                    reunion['rappel_5min_envoye'] = True
                    self.save_data()
                    print(f"✅ Rappel 5min envoyé pour: {reunion['titre']}")
                
                # 🚀 RAPPEL AU DÉBUT DE LA RÉUNION
                if not reunion.get('rappel_debut_envoye') and now >= date_reunion and now < date_reunion + timedelta(minutes=5):
                    await self.send_reminder(reunion, "maintenant", discord.Color.red(), debut=True)
                    reunion['rappel_debut_envoye'] = True
                    self.save_data()
                    print(f"✅ Rappel DÉBUT envoyé pour: {reunion['titre']}")
                
                # 🗑️ Suppression des anciennes réunions (24h après)
                if now > date_reunion + timedelta(hours=24):
                    reunions_a_supprimer.append(reunion)
            
            # Nettoyage
            for reunion in reunions_a_supprimer:
                self.reunions.remove(reunion)
                print(f"🗑️ Réunion supprimée: {reunion['titre']}")
            
            if reunions_a_supprimer:
                self.save_data()
        
        except Exception as e:
            print(f"❌ Erreur vérification rappels: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        """Attend que le bot soit prêt avant de démarrer la boucle"""
        await self.bot.wait_until_ready()
    
    async def send_reminder(self, reunion, temps, couleur, debut=False):
        """Envoie un rappel de réunion"""
        try:
            guild = self.bot.get_guild(reunion['guild_id'])
            if not guild:
                return
            
            channel = guild.get_channel(reunion['channel_id'])
            if not channel:
                return
            
            # Mention des participants
            mentions = " ".join([f"<@{user_id}>" for user_id in reunion['participants']])
            
            if debut:
                titre = "🔴 LA RÉUNION COMMENCE MAINTENANT !"
                description = f"**{reunion['titre']}** démarre **tout de suite** !"
            else:
                titre = f"⏰ Rappel de Réunion - Dans {temps}"
                description = f"**{reunion['titre']}** commence dans **{temps}** !"
            
            embed = discord.Embed(
                title=titre,
                description=description,
                color=couleur,
                timestamp=datetime.fromisoformat(reunion['date'])
            )
            
            embed.add_field(
                name="📋 Sujet",
                value=reunion['sujet'],
                inline=False
            )
            
            embed.add_field(
                name="👥 Participants Attendus",
                value=f"{len(reunion['participants'])} personnes",
                inline=True
            )
            
            if debut:
                embed.add_field(
                    name="🎯 Action Requise",
                    value="**Rejoignez le salon vocal maintenant !**",
                    inline=False
                )
            
            embed.set_footer(text=f"Organisé par {reunion['organisateur_name']}")
            
            await channel.send(content=mentions, embed=embed)
            
        except Exception as e:
            print(f"❌ Erreur envoi rappel: {e}")
    
    @app_commands.command(
        name="reunion",
        description="📅 Planifier une réunion avec rappels automatiques"
    )
    @app_commands.describe(
        date="Date (format: JJ/MM/AAAA)",
        heure="Heure (format: HH:MM)",
        titre="Titre de la réunion",
        sujet="Sujet/ordre du jour",
        participants="Mentionnez les participants (@membre1 @membre2...)"
    )
    async def reunion(
        self,
        interaction: discord.Interaction,
        date: str,
        heure: str,
        titre: str,
        sujet: str,
        participants: str
    ):
        try:
            # Parse de la date et heure
            date_str = f"{date} {heure}"
            date_reunion = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            
            # Vérification que la date est dans le futur
            if date_reunion <= datetime.now():
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="La date doit être dans le futur !",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Extraction des IDs des participants
            participant_ids = []
            for word in participants.split():
                if word.startswith('<@') and word.endswith('>'):
                    user_id = word.strip('<@!>')
                    try:
                        participant_ids.append(int(user_id))
                    except ValueError:
                        continue
            
            if not participant_ids:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Aucun participant valide mentionné !",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Création de la réunion
            reunion_data = {
                'id': len(self.reunions) + 1,
                'guild_id': interaction.guild_id,
                'channel_id': interaction.channel_id,
                'organisateur_id': interaction.user.id,
                'organisateur_name': interaction.user.display_name,
                'date': date_reunion.isoformat(),
                'titre': titre,
                'sujet': sujet,
                'participants': participant_ids,
                'rappel_30min_envoye': False,
                'rappel_5min_envoye': False,
                'rappel_debut_envoye': False,
                'created_at': datetime.now().isoformat()
            }
            
            self.reunions.append(reunion_data)
            self.save_data()
            
            # Confirmation
            embed = discord.Embed(
                title="✅ Réunion Planifiée",
                description=f"**{titre}**",
                color=discord.Color.green(),
                timestamp=date_reunion
            )
            
            embed.add_field(
                name="📋 Sujet",
                value=sujet,
                inline=False
            )
            
            embed.add_field(
                name="👥 Participants",
                value=f"{len(participant_ids)} personnes",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Rappels",
                value="📣 **30 minutes** avant\n📣 **5 minutes** avant\n🔴 **Au début** de la réunion",
                inline=False
            )
            
            embed.set_footer(text=f"ID: {reunion_data['id']} • Organisateur: {interaction.user.display_name}")
            
            # Mention des participants
            mentions = " ".join([f"<@{uid}>" for uid in participant_ids])
            
            await interaction.response.send_message(content=mentions, embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Format Invalide",
                description="**Format attendu :**\n📅 Date: `JJ/MM/AAAA`\n🕐 Heure: `HH:MM`\n\n**Exemple:** `25/12/2024` et `14:30`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur s'est produite: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="voir_reunions",
        description="📋 Voir toutes les réunions planifiées"
    )
    async def voir_reunions(self, interaction: discord.Interaction):
        if not self.reunions:
            embed = discord.Embed(
                title="📅 Aucune Réunion",
                description="Aucune réunion n'est planifiée pour le moment.",
                color=discord.Color.blue()
            )
            return await interaction.response.send_message(embed=embed)
        
        # Trier par date
        reunions_triees = sorted(
            [r for r in self.reunions if datetime.fromisoformat(r['date']) > datetime.now()],
            key=lambda x: x['date']
        )
        
        if not reunions_triees:
            embed = discord.Embed(
                title="📅 Aucune Réunion à Venir",
                description="Toutes les réunions sont passées.",
                color=discord.Color.blue()
            )
            return await interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="📅 Réunions Planifiées",
            description=f"**{len(reunions_triees)}** réunion(s) à venir",
            color=discord.Color.blue()
        )
        
        for reunion in reunions_triees[:10]:  # Max 10
            date_reunion = datetime.fromisoformat(reunion['date'])
            
            # Calcul du temps restant
            delta = date_reunion - datetime.now()
            jours = delta.days
            heures = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if jours > 0:
                temps_restant = f"Dans {jours}j {heures}h"
            elif heures > 0:
                temps_restant = f"Dans {heures}h {minutes}min"
            else:
                temps_restant = f"Dans {minutes}min"
            
            embed.add_field(
                name=f"🗓️ {reunion['titre']}",
                value=f"📅 {date_reunion.strftime('%d/%m/%Y à %H:%M')}\n⏰ {temps_restant}\n👥 {len(reunion['participants'])} participants\n📝 ID: `{reunion['id']}`",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="annuler_reunion",
        description="🗑️ Annuler une réunion planifiée"
    )
    @app_commands.describe(
        reunion_id="ID de la réunion à annuler"
    )
    async def annuler_reunion(self, interaction: discord.Interaction, reunion_id: int):
        reunion = next((r for r in self.reunions if r['id'] == reunion_id), None)
        
        if not reunion:
            embed = discord.Embed(
                title="❌ Réunion Introuvable",
                description=f"Aucune réunion avec l'ID `{reunion_id}`.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Vérification des permissions
        if reunion['organisateur_id'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Refusée",
                description="Seul l'organisateur ou un administrateur peut annuler cette réunion.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Suppression
        self.reunions.remove(reunion)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Réunion Annulée",
            description=f"La réunion **{reunion['titre']}** a été annulée.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Reunions(bot))
