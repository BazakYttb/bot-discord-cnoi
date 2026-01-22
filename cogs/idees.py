import discord
from discord.ext import commands
import asyncio
import sys
import os

# Import des configurations
from config.settings import TOKEN, GUILD_ID

class DiscordBot(commands.Bot):
    """
    Classe principale du bot Discord
    """
    
    def __init__(self):
        # Configuration des intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',  # Préfixe pour les commandes legacy (sync)
            intents=intents,
            help_command=None
        )
        
        self.guild_id = GUILD_ID
    
    async def setup_hook(self):
        """
        Méthode appelée avant que le bot se connecte
        Charge les cogs et synchronise les commandes
        """
        print("🔄 Chargement des modules...")
        
        # Liste des cogs à charger
        cogs_list = [
            'cogs.regles',
            'cogs.idees'
        ]
        
        # Chargement des cogs
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"  ✅ {cog} chargé")
            except Exception as e:
                print(f"  ❌ Erreur lors du chargement de {cog}: {e}")
                sys.exit(1)
        
        # Synchronisation des commandes avec le serveur Discord
        try:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"🔄 {len(synced)} commandes synchronisées sur le serveur {self.guild_id}")
        except Exception as e:
            print(f"❌ Erreur lors de la synchronisation: {e}")
            sys.exit(1)
    
    async def on_ready(self):
        """
        Événement déclenché quand le bot est connecté
        """
        print(f"✅ {self.user} est connecté et opérationnel!")
        print(f"📊 Serveurs: {len(self.guilds)}")
        print(f"👥 Utilisateurs: {len(self.users)}")
        
        # Définir le statut du bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="les idées | /idee"
            )
        )

# Création de l'instance du bot
bot = DiscordBot()

# ==========================================
# COMMANDE DE SYNCHRONISATION (ADMIN ONLY)
# ==========================================

@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    """
    Commande pour forcer la synchronisation des slash commands
    Utilisable uniquement par le propriétaire du bot
    """
    try:
        guild = discord.Object(id=bot.guild_id)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        await ctx.send(f"✅ {len(synced)} commandes synchronisées !")
    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")

# ==========================================
# GESTION DES ERREURS GLOBALES
# ==========================================

@bot.event
async def on_command_error(ctx, error):
    """Gestion des erreurs des commandes"""
    if isinstance(error, commands.NotOwner):
        await ctx.send("❌ Seul le propriétaire du bot peut utiliser cette commande.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore les commandes inconnues
    else:
        print(f"❌ Erreur: {error}")

# ==========================================
# DÉMARRAGE DU BOT
# ==========================================

async def main():
    """
    Fonction principale pour démarrer le bot
    """
    try:
        async with bot:
            await bot.start(TOKEN)
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot arrêté proprement")
