# Jasså Discord Bot

![Docker](https://github.com/Jorgen1040/jassa-bot/workflows/Docker/badge.svg)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/1907d94cadf24e928acca559afb4a5f2)](https://www.codacy.com/gh/Jorgen1040/jassa-bot/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Jorgen1040/jassa-bot&amp;utm_campaign=Badge_Grade)

Just a super simple bot for generating a gif meme.

##### Example of gif using `+jasså GitHub`

<img src="https://user-images.githubusercontent.com/26395020/102714145-fff5ea00-42cc-11eb-9093-78ac57135fbc.gif" height="300">

Also serves as a replacement for [kawaiibot](https://github.com/KawaiiBot/KawaiiBot)'s rule34 command.

###### God, please forgive me 🙏

## To use on your own server

To use the bot just invite the bot that I'm hosting with this [Invite Link](https://discord.com/api/oauth2/authorize?client_id=751534353401512088&permissions=8&scope=bot)

Or you could run the bot yourself with Docker. Simply replace the placeholders and run the command:

```
docker run -d --name jassa-bot \
-e BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN \
-e OWNER_ID=YOUR_DISCORD_ID \
-v /path/for/bot:/jassa-bot \
jorgen1040/jassa-bot:latest
```

The volume mount is not necessary, but is extremely useful for caching gifs cutting down quite drastically on how long it takes to make one.

## Want to add something?

Feel free to fork this repo and make a pull request, I'll also gladly take suggestions for either new features, or code cleanup as this is my first proper Python project.

When forking with intent of making a PR, please make a new branch and give it an approriate name.
