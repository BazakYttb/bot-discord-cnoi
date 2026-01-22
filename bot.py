"""
Bot Discord - Gestionnaire de Serveur
Fonctionnalités: Règles automatiques, Système d'idées
"""

import discord
from discord.ext import commands
import asyncio
import os
from config.settings import TOKEN, GUILD_ID


class MonBot(commands.Bot):
    """
    Classe principale du bot avec chargement automatique des cogs
    """
    
    def __init__(self):
        # Configuration des intents (permissions)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',  # Préfixe pour les commandes classiques (optionnel)
            intents=intents,
            help_command=None  # Désactive le !help par défaut
        )
    
    async def setup_hook(self):
        """
        Appelé avant le démarrage du bot
        Charge automatiquement tous les cogs
        """
        print("🔄 Chargement des modules...")
        
        # Liste des cogs à charger
        cogs_a_charger = [
            'cogs.regles',
            'cogs.idees'
        ]
        
        # Charge chaque cog
        for cog in cogs_a_charger:
            try:
                await self.load_extension(cog)
                print(f"  ✅ {cog} chargé")
            except Exception as e:
                print(f"  ❌ Erreur lors du chargement de {cog}: {e}")
        
        # Synchronise les commandes slash (rapide si GUILD_ID est défini)
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"🔄 Commandes synchronisées sur le serveur {GUILD_ID}")
        else:
            await self.tree.sync()
            print("🔄 Commandes synchronisées globalement (peut prendre 1h)")
    
    async def on_ready(self):
        """
        Appelé quand le bot est connecté et prêt
        """
        print("\n" + "="*50)
        print(f"✅ {self.user} est connecté et opérationnel!")
        print(f"📊 Connecté à {len(self.guilds)} serveur(s)")
        print(f"👥 {len(self.users)} utilisateurs visibles")
        print("="*50 + "\n")
        
        # Change le statut du bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="les règles 📜 | /idee"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """
        Gestion globale des erreurs
        """
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore les commandes inexistantes
        
        print(f"❌ Erreur: {error}")


# Point d'entrée du programme
async def main():
    """
    Fonction principale qui lance le bot
    """
    # Vérifie que le token existe
    if not TOKEN:
        print("❌ ERREUR: Token Discord manquant!")
        print("👉 Ajoute ton token dans le fichier .env")
        return
    
    # Crée et lance le bot
    bot = MonBot()
    
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt du bot...")
        await bot.close()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")



# Lance le bot
if __name__ == "__main__":
    asyncio.run(main())
