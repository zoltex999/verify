# Verify 🔐

Bot Discord de sécurité par captcha — protège ton serveur contre les raids, bots et comptes indésirables.

## Fonctionnement

Lorsqu'un membre rejoint le serveur, Verify lui envoie un captcha à résoudre avant d'accéder aux salons. En cas d'échec, il est automatiquement expulsé.

## Fonctionnalités

- Captcha automatique à l'arrivée d'un membre
- Expulsion automatique en cas d'échec
- Rôle attribué après vérification réussie
- Protection contre les raids et bots

## Installation

```bash
git clone https://github.com/zoltex999/verify
cd verify
pip install -r requirements.txt
python bot.py
```

## Configuration

```env
TOKEN=ton_token_discord
ROLE_ID=id_du_role_a_attribuer
```

## Prérequis

- Python 3.10+
- discord.py
- Un bot Discord avec les intents activés

## Licence

MIT
