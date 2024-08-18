
import discord
from discord.ext import commands
import requests
from dhooks import Webhook, Embed
import blockcypher 



COINGECKO_API_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd'

WEBHOOK_URL  = ""

numanxd = '' # your account token
PRIVATE_KEY = '' # your private key of litecoin wallet
ADDRESS = '' # your ltc address
API_TOKEN = '506b172c977c49f4b85383e56b497d19'


bot = commands.Bot(command_prefix=".", self_bot=True) # , help_command=None


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command()
async def hello(ctx):
    await ctx.send('Hi!')

@bot.command(help="Check Litecoin balance for a specified address.")
async def balance(ctx, litecoin_address: str):
    await ctx.message.delete()
    try:
        # Get Litecoin balance from BlockCypher API
        blockcypher_url = f'https://api.blockcypher.com/v1/ltc/main/addrs/{litecoin_address}'
        blockcypher_response = requests.get(blockcypher_url)
        blockcypher_data = blockcypher_response.json()

        if 'balance' in blockcypher_data:
            balance_ltc = blockcypher_data['balance'] / 1e8
            unconfirmed_balance_ltc = blockcypher_data['unconfirmed_balance'] / 1e8
            
            # Fetch LTC to USD conversion rate from CoinGecko API
            coingecko_response = requests.get(COINGECKO_API_URL)
            coingecko_data = coingecko_response.json()
            ltc_to_usd_rate = coingecko_data['litecoin']['usd']
            
            # Calculate balance in USD
            balance_usd = balance_ltc * ltc_to_usd_rate
            unconfirmed_balance_usd = unconfirmed_balance_ltc * ltc_to_usd_rate

            await ctx.send(f"```Litecoin Address: {litecoin_address}\n\n"
                           f"- Confirmed Balance: {balance_ltc:.8f} LTC | {balance_usd:.2f} USD\n"
                           f"- Unconfirmed Balance: {unconfirmed_balance_ltc:.8f} LTC | {unconfirmed_balance_usd:.2f} USD```")
        else:
            await ctx.send(f"Failed to retrieve balance for Litecoin address `{litecoin_address}`.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(help="Send LTC to a specified address.")

async def send(ctx, ltc_address: str, amount_usd: float):
    await ctx.message.delete()

    try:
        # Fetch Litecoin price from CryptoCompare API
        response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD')
        response.raise_for_status()  # Raise an exception for non-200 status codes
        ltc_price_usd = response.json().get('USD')

        if ltc_price_usd is None:
            raise ValueError("Failed to retrieve the Litecoin price.")

        # Calculate LTC amount to send
        ltc_amount = amount_usd / ltc_price_usd

        # Check if the balance is sufficient
        total_balance = blockcypher.get_total_balance(address=ADDRESS, coin_symbol="ltc", api_key=API_TOKEN)
        if total_balance < ltc_amount:
            return await ctx.send("You do not have enough balance to send LTC.")

        # Create the transaction
        transaction = blockcypher.simple_spend(from_privkey=PRIVATE_KEY, to_address=ltc_address, to_satoshis=int(ltc_amount * 1e8), coin_symbol="ltc", api_key=API_TOKEN)

        # Send a regular message with the transaction details
        transaction_url = f"https://live.blockcypher.com/ltc/tx/{transaction}"
        message = (
            f"LTC Transaction\n"
            f"From: {ADDRESS}\n"
            f"To: {ltc_address}\n"
            f"Amount: {amount_usd:.2f} USD | {ltc_amount:.8f} LTC\n"
            f"Transaction ID: [{transaction}]({transaction_url})"
        )
        await ctx.send(message)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


if numanxd:
    print("Starting the bot...")
    bot.run(numanxd, reconnect=True)  # `reconnect=True` is fine, `bot=False` is not needed
else:
    print("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
