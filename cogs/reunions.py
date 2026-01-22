import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
import asyncio

class Reunions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/reunions.json'
        os.makedirs('data', exist_ok=True)
        self.reunions = self.load_data()
        
        # Lancement de la vérification des rappels
        self.bot.loop.create_task(self.check_reminders())
    
    def load_data(self):
        """Charge les réunions depuis le JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            print("⚠️  Fichier reunions.json corrompu, réinitialisation...")
        return []
    
    def save_data(self):
        """Sauvegarde les réunions dans le JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.reunions, f, indent=4, ensure_ascii=False)
    
    async def check_reminders(self):
        """Vérifie toutes les 60 secondes si des rappels doivent être envoyés"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = datetime.utcnow()
                
                for reunion in self.reunions:
                    date_reunion = datetime.fromisoformat(reunion['date'])
                    rappel_1h = date_reunion - timedelta(hours=1)
                    
                    # Rappel 1h avant
                    if not reunion.get('rappel_envoye') and now >= rappel_1h and now < date_reunion:
                        await self.send_reminder(reunion)
                        reunion['rappel_envoye'] = True
                        self.save_data()
                    
                    # Suppression des anciennes réunions (24h après)
                    if now > date_reunion + timedelta(hours=24):
                        self.reunions.remove(reunion)
                        self.save_data()
                
            except Exception as e:
                print(f"Erreur vérification rappels: {e}")
            
            await asyncio.sleep(60)  # Vérification toutes les minutes
    
    async def send_reminder(self, reunion):
        """Envoie le rappel de réunion"""
        try:
            guild = self.bot.get_guild(reunion['guild_id'])
            if not guild:
                return
            
            channel = guild.get_channel(reunion['channel_id'])
            if not channel:
                return
            
            # Mention des participants
            mentions = " ".join([f"<@{user_id}>" for user_id in reunion['participants']])
            
            embed = discord.Embed(
                title="⏰ Rappel de Réunion",
                description=f"**{reunion['titre']}** commence dans **1 heure** !",
                color=discord.Color.orange(),
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
            
            embed.set_footer(text=f"Organisé par {reunion['organisateur_name']}")
            
            await channel.send(content=mentions, embed=embed)
            
        except Exception as e:
            print(f"Erreur envoi rappel: {e}")
    
    @app_commands.command(
        name="reunion",
        description="[STAFF] Planifier une réunion officielle"
    )
    @app_commands.describe(
        titre="Titre de la réunion",
        date="Date au format JJ/MM/AAAA (ex: 25/01/2025)",
        heure="Heure au format HH:MM (ex: 14:30)",
        sujet="Sujet principal de la réunion"
    )
    async def reunion(
        self, 
        interaction: discord.Interaction, 
        titre: str,
        date: str,
        heure: str,
        sujet: str
    ):
        """Planifie une réunion"""
        
        # Vérification du rôle staff
        role_staff = interaction.guild.get_role(int(os.getenv('ROLE_STAFF')))
        if role_staff not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Seul le staff peut planifier des réunions !",
                ephemeral=True
            )
        
        # Parsing de la date/heure
        try:
            jour, mois, annee = map(int, date.split('/'))
            heure_h, heure_m = map(int, heure.split(':'))
            date_reunion = datetime(annee, mois, jour, heure_h, heure_m)
            
            # Vérification que la date est dans le futur
            if date_reunion <= datetime.utcnow():
                return await interaction.response.send_message(
                    "❌ La date de la réunion doit être dans le futur !",
                    ephemeral=True
                )
            
        except ValueError:
            return await interaction.response.send_message(
                "❌ Format de date/heure invalide !\n**Date :** JJ/MM/AAAA\n**Heure :** HH:MM",
                ephemeral=True
            )
        
        # Création de l'embed
        embed = discord.Embed(
            title=f"📅 Réunion Planifiée : {titre}",
            color=discord.Color.blue(),
            timestamp=date_reunion
        )
        
        embed.add_field(
            name="📋 Sujet",
            value=sujet,
            inline=False
        )
        
        embed.add_field(
            name="🕒 Date et Heure",
            value=f"**{date_reunion.strftime('%d/%m/%Y à %H:%M')}** (UTC)\n\n⏰ Rappel automatique 1h avant",
            inline=False
        )
        
        embed.add_field(
            name="👤 Organisateur",
            value=interaction.user.mention,
            inline=True
        )
        
        embed.set_footer(text="Réagis avec ✅ pour confirmer ta présence")
        
        # Envoi du message
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Ajout de la réaction
        await message.add_reaction("✅")
        
        # Sauvegarde dans le JSON
        self.reunions.append({
            'id': message.id,
            'titre': titre,
            'sujet': sujet,
            'date': date_reunion.isoformat(),
            'organisateur_id': interaction.user.id,
            'organisateur_name': interaction.user.name,
            'channel_id': interaction.channel.id,
            'guild_id': interaction.guild.id,
            'participants': [],
            'rappel_envoye': False
        })
        self.save_data()
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gère les confirmations de présence"""
        # Ignore les réactions du bot
        if payload.user_id == self.bot.user.id:
            return
        
        # Vérifie si c'est une réunion
        reunion = next((r for r in self.reunions if r['id'] == payload.message_id), None)
        if not reunion or str(payload.emoji) != "✅":
            return
        
        # Ajoute le participant
        if payload.user_id not in reunion['participants']:
            reunion['participants'].append(payload.user_id)
            self.save_data()
            
            # Message de confirmation (optionnel)
            try:
                channel = self.bot.get_channel(payload.channel_id)
                user = await self.bot.fetch_user(payload.user_id)
                await channel.send(
                    f"✅ {user.mention} a confirmé sa présence à la réunion **{reunion['titre']}** !",
                    delete_after=10
                )
            except:
                pass

async def setup(bot):
    await bot.add_cog(Reunions(bot))
