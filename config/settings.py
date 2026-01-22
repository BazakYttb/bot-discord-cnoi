"""
Configuration centralisée du bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Token
TOKEN = os.getenv('DISCORD_TOKEN')

# IDs des channels
CHANNEL_REGLES = int(os.getenv('CHANNEL_REGLES'))
CHANNEL_IDEES = int(os.getenv('CHANNEL_IDEES'))

# ID du serveur (pour sync rapide)
GUILD_ID = int(os.getenv('GUILD_ID'))

# Règles du serveur (modifiable facilement)
REGLES_TEXTE = """
# 📜 RÈGLES DU SERVEUR

**1️⃣ Respect**
Soyez respectueux envers tous les membres. Aucune insulte, harcèlement ou discrimination ne sera tolérée.

**2️⃣ Pas de spam**
Évitez de spammer les messages, les mentions ou les emojis.

**3️⃣ Contenu approprié**
Pas de contenu NSFW, violent ou illégal.

**4️⃣ Langage**
Utilisez un langage correct. Les insultes excessives sont interdites.

**5️⃣ Publicité**
Aucune publicité sans autorisation des modérateurs.

**6️⃣ Pseudonyme**
Utilisez un pseudo approprié et mentionnable.

**7️⃣ Canaux**
Utilisez les bons canaux pour les bonnes discussions.

**8️⃣ Modération**
Les décisions des modérateurs sont finales. En cas de désaccord, contactez-les en privé.

⚠️ **Le non-respect de ces règles peut entraîner un avertissement, un mute ou un bannissement.**

✅ En restant sur ce serveur, vous acceptez ces règles.
"""

# ========================================
# 🎫 SYSTÈME DE CANDIDATURES
# ========================================
CHANNEL_CANDIDATURES = 1463967316583776299  # Salon où apparaît le menu
CATEGORY_TICKETS = 1463968783621296238      # Catégorie pour créer les tickets
ROLE_STAFF = 1462916583927316624            # Rôle à ping et autorisé à fermer

# Postes disponibles (modifie selon tes besoins)
POSTES_DISPONIBLES = {
    "Ministre des Armées": "🛡️",
    "Ministre de l'Impérialisme": "👑",
    "Ministre des Affaires Étrangères": "🌍",
    "Ministre de la Culture": "🎭",
    "Ministère Principal": "⚖️",
    "Secrétaire": "📋"
}

# ========================================
# 🏛️ ORGANIGRAMME GOUVERNEMENTAL
# ========================================
CHANNEL_ORGANIGRAMME = 1462916585793786062  # Salon de l'organigramme
