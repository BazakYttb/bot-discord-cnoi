import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta

class Reunions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/reunions.json"
        self.reunions = self.load_data()
        self.check_reminders.start()
    
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
    
    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """Vérifie et envoie les rappels de réunions"""
        try:
            now = datetime.now()
            reunions_a_supprimer = []
            
            for reunion in self.reunions:
                date_reunion = datetime.fromisoformat(reunion['date'])
                
                rappel_30min = date_reunion - timedelta(minutes=30)
                rappel_5min = date_reunion - timedelta(minutes=5)
                
                # ⏰ RAPPEL 30 MINUTES AVANT
                if not reunion.get('rappel_30min_envoye') and now >= rappel_30min and now < date_reunion:
                    await self.send_reminder(reunion, "30 minutes", discord.Color.blue())
                    reunion['rappel_30min_envoye'] = True
                    self.save_data()
                
                # ⏰ RAPPEL 5 MINUTES AVANT
                if not reunion.get('rappel_5min_envoye') and now >= rappel_5min and now < date_reunion:
                    await self.send_reminder(reunion, "5 minutes", discord.Color.orange())
                    reunion['rappel_5min_envoye'] = True
                    self.save_data()
                
                # 🚀 RAPPEL AU DÉBUT
                if not reunion.get('rappel_debut_envoye') and now >= date_reunion and now < date_reunion + timedelta(minutes=5):
                    await self.send_reminder(reunion, "maintenant", discord.Color.red(), debut=True)
                    reunion['rappel_debut_envoye'] = True
                    self.save_data()
                
                # 🗑️ Suppression 24h après
                if now > date_reunion + timedelta(hours=24):
                    reunions_a_supprimer.append(reunion)
            
            for reunion in reunions_a_supprimer:
                self.reunions.remove(reunion)
            
            if reunions_a_supprimer:
                self.save_data()
        
        except Exception as e:
            print(f"❌ Erreur vérification rappels: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
    
    async def send_reminder(self, reunion, temps, couleur, debut=False):
        """Envoie un rappel dans le channel"""
        try:
            guild = self.bot.get_guild(reunion['guild_id'])
            if not guild:
                return
            
            channel = guild.get_channel(reunion['channel_id'])
            if not channel:
                return
            
            # 🎯 PING UNIQUEMENT LES PARTICIPANTS CONFIRMÉS (✅)
            mentions = " ".join([f"<@{user_id}>" for user_id in reunion.get('participants_confirmes', [])])
            
            if not mentions:
                mentions = "⚠️ Aucun participant confirmé"
            
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
            
            nb_confirmes = len(reunion.get('participants_confirmes', []))
            nb_absents = len(reunion.get('participants_absents', []))
            
            embed.add_field(
                name="👥 Participants",
                value=f"✅ Confirmés : **{nb_confirmes}**\n❌ Absents : **{nb_absents}**",
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
        description="📅 Planifier une réunion avec système de confirmation"
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
            date_str = f"{date} {heure}"
            date_reunion = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            
            if date_reunion <= datetime.now():
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="La date doit être dans le futur !",
                    color=discord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Extraction des IDs
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
            
            # Création embed principal
            embed = discord.Embed(
                title="📅 Nouvelle Réunion Planifiée",
                description=f"**{titre}**",
                color=discord.Color.blue(),
                timestamp=date_reunion
            )
            
            embed.add_field(
                name="📋 Sujet",
                value=sujet,
                inline=False
            )
            
            embed.add_field(
                name="🕐 Date & Heure",
                value=f"📅 {date_reunion.strftime('%d/%m/%Y')}\n🕐 {date_reunion.strftime('%H:%M')}",
                inline=True
            )
            
            embed.add_field(
                name="👥 Participants Invités",
                value=f"{len(participant_ids)} personne(s)",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Rappels Automatiques",
                value="📣 30 minutes avant\n📣 5 minutes avant\n🔴 Au début",
                inline=False
            )
            
            embed.add_field(
                name="📌 Confirmer sa Présence",
                value="✅ Je serai présent\n❌ Je serai absent",
                inline=False
            )
            
            embed.set_footer(text=f"Organisé par {interaction.user.display_name}")
            
            # Envoi du message
            mentions = " ".join([f"<@{uid}>" for uid in participant_ids])
            await interaction.response.send_message(content=mentions, embed=embed)
            message = await interaction.original_response()
            
            # Ajout des réactions
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            # Sauvegarde
            reunion_data = {
                'id': len(self.reunions) + 1,
                'message_id': message.id,
                'guild_id': interaction.guild_id,
                'channel_id': interaction.channel_id,
                'organisateur_id': interaction.user.id,
                'organisateur_name': interaction.user.display_name,
                'date': date_reunion.isoformat(),
                'titre': titre,
                'sujet': sujet,
                'participants_invites': participant_ids,
                'participants_confirmes': [],
                'participants_absents': [],
                'rappel_30min_envoye': False,
                'rappel_5min_envoye': False,
                'rappel_debut_envoye': False,
                'created_at': datetime.now().isoformat()
            }
            
            self.reunions.append(reunion_data)
            self.save_data()
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Format Invalide",
                description="**Format attendu :**\n📅 Date: `JJ/MM/AAAA`\n🕐 Heure: `HH:MM`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gère les réactions ✅ et ❌"""
        # Ignore le bot
        if payload.user_id == self.bot.user.id:
            return
        
        # Trouve la réunion
        reunion = next((r for r in self.reunions if r.get('message_id') == payload.message_id), None)
        if not reunion:
            return
        
        # Vérifie que c'est un participant invité
        if payload.user_id not in reunion['participants_invites']:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        
        # ✅ CONFIRMATION DE PRÉSENCE
        if str(payload.emoji) == "✅":
            # Retire des absents si présent
            if payload.user_id in reunion['participants_absents']:
                reunion['participants_absents'].remove(payload.user_id)
            
            # Ajoute aux confirmés
            if payload.user_id not in reunion['participants_confirmes']:
                reunion['participants_confirmes'].append(payload.user_id)
                self.save_data()
                
                # 📩 ENVOI DU MP
                try:
                    date_reunion = datetime.fromisoformat(reunion['date'])
                    embed = discord.Embed(
                        title="✅ Confirmation de Présence",
                        description=f"Vous êtes bien inscrit à la réunion **{reunion['titre']}**",
                        color=discord.Color.green(),
                        timestamp=date_reunion
                    )
                    
                    embed.add_field(
                        name="📅 Date",
                        value=date_reunion.strftime('%d/%m/%Y à %H:%M'),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📋 Sujet",
                        value=reunion['sujet'],
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⏰ Rappels",
                        value="Vous recevrez des pings :\n📣 30 min avant\n📣 5 min avant\n🔴 Au début",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Organisé par {reunion['organisateur_name']}")
                    
                    await user.send(embed=embed)
                except discord.Forbidden:
                    print(f"⚠️ Impossible d'envoyer un MP à {user.name}")
        
        # ❌ DÉCLARATION D'ABSENCE
        elif str(payload.emoji) == "❌":
            # Retire des confirmés
            if payload.user_id in reunion['participants_confirmes']:
                reunion['participants_confirmes'].remove(payload.user_id)
            
            # Ajoute aux absents
            if payload.user_id not in reunion['participants_absents']:
                reunion['participants_absents'].append(payload.user_id)
                self.save_data()
                
                # 📩 MP D'ABSENCE
                try:
                    date_reunion = datetime.fromisoformat(reunion['date'])
                    embed = discord.Embed(
                        title="❌ Absence Enregistrée",
                        description=f"Votre absence à la réunion **{reunion['titre']}** a été enregistrée.",
                        color=discord.Color.red(),
                        timestamp=date_reunion
                    )
                    
                    embed.add_field(
                        name="📅 Date",
                        value=date_reunion.strftime('%d/%m/%Y à %H:%M'),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="ℹ️ Information",
                        value="Vous ne recevrez pas de rappels pour cette réunion.",
                        inline=False
                    )
                    
                    await user.send(embed=embed)
                except discord.Forbidden:
                    print(f"⚠️ Impossible d'envoyer un MP à {user.name}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Gère le retrait des réactions"""
        reunion = next((r for r in self.reunions if r.get('message_id') == payload.message_id), None)
        if not reunion:
            return
        
        if str(payload.emoji) == "✅" and payload.user_id in reunion['participants_confirmes']:
            reunion['participants_confirmes'].remove(payload.user_id)
            self.save_data()
        
        elif str(payload.emoji) == "❌" and payload.user_id in reunion['participants_absents']:
            reunion['participants_absents'].remove(payload.user_id)
            self.save_data()
    
    @app_commands.command(
        name="voir_reunions",
        description="📋 Voir toutes les réunions planifiées"
    )
    async def voir_reunions(self, interaction: discord.Interaction):
        reunions_futures = [
            r for r in self.reunions 
            if datetime.fromisoformat(r['date']) > datetime.now()
        ]
        
        if not reunions_futures:
            embed = discord.Embed(
                title="📅 Aucune Réunion",
                description="Aucune réunion planifiée pour le moment.",
                color=discord.Color.blue()
            )
            return await interaction.response.send_message(embed=embed)
        
        reunions_triees = sorted(reunions_futures, key=lambda x: x['date'])
        
        embed = discord.Embed(
            title="📅 Réunions à Venir",
            description=f"**{len(reunions_triees)}** réunion(s) planifiée(s)",
            color=discord.Color.blue()
        )
        
        for reunion in reunions_triees[:10]:
            date_reunion = datetime.fromisoformat(reunion['date'])
            delta = date_reunion - datetime.now()
            
            if delta.days > 0:
                temps = f"Dans {delta.days}j {delta.seconds//3600}h"
            else:
                temps = f"Dans {delta.seconds//3600}h {(delta.seconds%3600)//60}min"
            
            nb_confirmes = len(reunion.get('participants_confirmes', []))
            nb_absents = len(reunion.get('participants_absents', []))
            
            embed.add_field(
                name=f"🗓️ {reunion['titre']}",
                value=f"📅 {date_reunion.strftime('%d/%m/%Y à %H:%M')}\n⏰ {temps}\n✅ {nb_confirmes} confirmés • ❌ {nb_absents} absents",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="annuler_reunion",
        description="🗑️ Annuler une réunion"
    )
    @app_commands.describe(reunion_id="ID de la réunion")
    async def annuler_reunion(self, interaction: discord.Interaction, reunion_id: int):
        reunion = next((r for r in self.reunions if r['id'] == reunion_id), None)
        
        if not reunion:
            embed = discord.Embed(
                title="❌ Introuvable",
                description=f"Aucune réunion avec l'ID `{reunion_id}`.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        if reunion['organisateur_id'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Refusée",
                description="Seul l'organisateur ou un admin peut annuler.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.reunions.remove(reunion)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Réunion Annulée",
            description=f"**{reunion['titre']}** a été annulée.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Reunions(bot))
