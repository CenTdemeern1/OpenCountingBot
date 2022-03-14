
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
 - In `bot.py`, change the value of bot_owner_id to your user ID
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
 - Just start counting from 1!
 - Count as high as possible without losing your streak.
 - For a bit of extra fun, you can count with Python math expressions and Wolfram|Alpha queries.
 - Expressions shouldn't contain spaces!
 - For Wolfram|Alpha queries, use the `|` prefix. (These *can* contain spaces)

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


Configuring the game rules
---
You can use `c#config <setting> <newvalue>` to configure the game rules for a channel. **(Changing a rule will reset your streak!)**


Configure game settings for this channel.

Available settings:

- `Step` - Sets by what number you count, your stepping value (ex. Step 0.1 = 0.1, 0.2, 0.3, 0.4, 0.5) (defaults to 1)
- `StartingNumber` - What number you start at (minus the Step value) (defaults to 0)
- `EnableWolframAlpha` - Whether to enable Wolfram|Alpha queries (defaults to true)
- `EnableExpressions` - Whether to enable (Python 3 supported) math expressions (defaults to true)
- `RoundAllGuesses` - Whether to round all guesses to the nearest integer (defaults to false)
- `AllowSingleUserCount` - Whether to disable the "A single person is not allowed to say 2 numbers in a row" rule (defaults to false)
- `ForceIntegerConversions` - An extra safeguard to ensure no internal rounding errors can happen by internally only using whole numbers. Disable this if your stepping value or starting number has a decimal point. (defaults to true)

### THIS IS IMPORTANT SO I'LL SAY IT AGAIN
**To use numbers with a decimal point as your step value, disable ForceIntegerConversions.**

---


Leaderboards
---
Global leaderboards are here!

They aren't hosted on a server though, they're only being stored locally. This means that you'll have your own leaderboard if you host the bot yourself.

To place a score on the leaderboard, you need to end your streak ***as long as it's rankable***.

This means:
- No cheating (so you can't `c#channel set` your way to victory)
- Use the default configuration (you can quickly reset your configuration to a rankable using `c#resetconfig`)

You can quickly check if your current streak is rankable using `c#rankable`

To check the current leaderboard, use `c#leaderboard`.

The leaderboard holds a maximum of 20 scores.

---