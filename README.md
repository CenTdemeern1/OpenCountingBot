![OpenCountingBot logo](https://raw.githubusercontent.com/CenTdemeern1/OpenCountingBot/main/assets/OpenCountingBot.png "OpenCountingBot logo")
# OpenCountingBot 
An open-source counting game bot for Discord
This README file is still a work in progress!

---
Setup instructions
---
### How to set up the bot without hosting it yourself:
 - [Invite the bot to your server](https://discord.com/api/oauth2/authorize?client_id=951659583078793216&permissions=137439475776&scope=bot) (Make sure you're an administrator, so you can follow the rest of the steps!)
 - In the channel(s) you want to use for counting, run `c#channel add`
 - You're done!
---
### How to set up the bot by hosting it yourself:
NOTE: You will need your own API keys for this, and since I'm not going to explain the basics of how to set up a Discord bot here, I recommend Googling stuff or getting in contact with me (@CenTdemeern1#3610)
 - Invite your bot to your server (Make sure you're an administrator, so you can follow the rest of the steps!)
 - Clone this repository, make sure you have Python 3 installed (tip: maybe set up a virtual environment!)
 - Create a file in the repository's root directory named `tokens.ini`
 - Make sure it looks like this, while replacing the fields you need to replace
 ![](https://raw.githubusercontent.com/CenTdemeern1/OpenCountingBot/main/assets/tokensfile.png)
 - Install the project requirements using pip (`python -m pip install -r requirements.txt`)
 - Run the bot! (`python bot.py`)
 - In the channel(s) you want to use for counting, run `c#channel add`
 - You're done!
---
Game rules & How to use the bot
---
### Rules
- A single person is not allowed to say 2 numbers in a row, doing so breaks the streak
- Any number said must follow the last one, or you break the streak
### How to play
Just start counting from 1!
Count as high as possible without losing your streak.
For a bit of extra fun, you can count with Python math expressions and Wolfram|Alpha queries.
Expressions shouldn't contain spaces!
For Wolfram|Alpha queries, use the `|` prefix. (These *can* contain spaces)
Example:
```
User 1: 1
User 2: 2
User 1: 3
User 2: 2+2
User 1: |Third prime number
User 2: 6
User 1: 7
User 3: 7
-> Bot: Oof, you failed! The next number was 8, but you said 7. If you feel this was unjustified, contact the mods. The next number is 1.
```
### For moderators: reviving dead streaks
Sometimes a streak might die due to unjust circumstances.
If you feel this way and want to revive a dead streak,  you can set the "last number".
You can set the "last number" by running `c#channel set [number]`

---
# /////////Under Construction/////////
Coming soon: Configuring the game rules
To use floating point numbers as your step value, disable ForceIntegerConversions.

