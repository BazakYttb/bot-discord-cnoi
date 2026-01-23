import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class AssistantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # ✅ LISTE COMPLÈTE DES COGS (avec calendrier et modération)
        self.initial_extensions = [
            'cogs.regles',
            'cogs.idees',
            'cogs.candidatures',
            'cogs.organigramme',
            'cogs.personnages',
            'cogs.statistiques',
            'cogs.reunions',
            'cogs.calendrier',       # ← NOUVEAU
            'cogs.moderation'        # ← NOUVEAU
        ]

    async def setup_hook(self):
        """Charge les cogs au démarrage"""
        print("🔄 Chargement des modules...")

        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"  ✅ {extension} chargé")
            except Exception as e:
                print(f"  ❌ Erreur lors du chargement de {extension} : {e}")

        # Synchroniser les commandes avec Discord
        guild_id = os.getenv('GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"🔄 Commandes synchronisées sur le serveur {guild_id}")
        else:
            await self.tree.sync()
            print("🔄 Commandes synchronisées globalement")

    async def on_ready(self):
        print("=" * 50)
        print(f"✅ Bot | {self.user} est connecté et opérationnel!")
        print(f"📊 Connecté à {len(self.guilds)} serveur(s)")
        print(f"👥 {len(self.users)} utilisateurs visibles")
        print("=" * 50)

async def main():
    bot = AssistantBot()

    try:
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt du bot...")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class AssistantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        # ✅ LISTE COMPLÈTE DES COGS (avec calendrier et modération)
        self.initial_extensions = [
            'cogs.regles',
            'cogs.idees',
            'cogs.candidatures',
            'cogs.organigramme',
            'cogs.personnages',
            'cogs.statistiques',
            'cogs.reunions',
            'cogs.calendrier',       # ← NOUVEAU
            'cogs.moderation'        # ← NOUVEAU
        ]

    async def setup_hook(self):
        """Charge les cogs au démarrage"""
        print("🔄 Chargement des modules...")

        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"  ✅ {extension} chargé")
            except Exception as e:
                print(f"  ❌ Erreur lors du chargement de {extension} : {e}")

        # Synchroniser les commandes avec Discord
        guild_id = os.getenv('GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"🔄 Commandes synchronisées sur le serveur {guild_id}")
        else:
            await self.tree.sync()
            print("🔄 Commandes synchronisées globalement")

    async def on_ready(self):
        print("=" * 50)
        print(f"✅ Bot | {self.user} est connecté et opérationnel!")
        print(f"📊 Connecté à {len(self.guilds)} serveur(s)")
        print(f"👥 {len(self.users)} utilisateurs visibles")
        print("=" * 50)

async def main():
    bot = AssistantBot()

    try:
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt du bot...")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
