import asyncio
import ormsgpack
import requests
from discord.ext import commands
import discord
from io import BytesIO
from dotenv import load_dotenv
import os

from fish_speech.utils.file import audio_to_bytes, read_ref_text
from fish_speech.utils.schema import ServeTTSRequest

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
url = "http://localhost:8080/v1/tts"

# Initialize the bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def connect_to_voice(ctx):
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None

    if not voice_channel:
        await ctx.send("You are not connected to a voice channel.")
        #react with a red x to the message we failed on
        await ctx.message.add_reaction('\u274C')
        return None

    attempt = 0
    max_retries = 100
    while attempt < max_retries:
        try:
            vc = await voice_channel.connect()
            return vc
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            await asyncio.sleep(5)  # Wait for a short period before retrying

    #react with a red x to the message we failed on
    await ctx.message.add_reaction('\u274C')
    raise Exception("Failed to connect to voice channel after several attempts")

async def play_audio(ctx, audio_stream):

    vc = await connect_to_voice(ctx)
    if vc == None: 
        return

    # Convert the stream to a BytesIO object
    audio_data = BytesIO()
    while True:
        chunk = audio_stream.read(1024)
        if not chunk:
            break
        audio_data.write(chunk)

    audio_data.seek(0)  # Reset the position of the BytesIO object

    vc.play(discord.FFmpegPCMAudio(audio_data, pipe=True))
    while vc.is_playing():
        await asyncio.sleep(1)
    
    await vc.disconnect()

async def fish_request(ctx, prompt, audio_file, ref_text, model_path):
    #react with a green checkmark to the message we are working on
    await ctx.message.add_reaction('\u2705')

    idstr: str | None = model_path
    if idstr is None:
        ref_audios = audio_file
        ref_texts = ref_text
        if ref_audios is None:
            byte_audios = []
        else:
            byte_audios = [audio_to_bytes(ref_audio) for ref_audio in ref_audios]
        if ref_texts is None:
            ref_texts = []
        else:
            ref_texts = [read_ref_text(ref_text) for ref_text in ref_texts]
    else:
        byte_audios = []
        ref_texts = []
        pass  # in api.py


    data = {
        "text": prompt,
        "references": [
            {"audio": ref_audio if ref_audio is not None else b"", "text": ref_text}
            for ref_text, ref_audio in zip(ref_texts, byte_audios)
        ],
        "reference_id": model_path,
        "normalize": True,
        "format": "wav",
        "max_new_tokens": 2048,
        "chunk_length": 200,
        "top_p": 0.7,
        "repetition_penalty": 1.2,
        "temperature": 0.7,
        "streaming": False,
        "use_memory_cache": "on",
        "seed": None,
    }

    pydantic_data = ServeTTSRequest(**data)
    api_key = "YOUR_API_KEY" #this is the fish-speech api key, if you're running the api server locally you don't need anything here
    response = requests.post(
        url,
        data=ormsgpack.packb(pydantic_data, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
        stream=False,
        headers={
            "authorization": f"Bearer {api_key}",
            "content-type": "application/msgpack",
        },
    )
    stream_stopped_flag = False

    if response.status_code == 200:
        audio_stream = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                audio_stream.write(chunk)
   
        audio_stream.seek(0)  # Reset the position of the BytesIO object
        await play_audio(ctx, audio_stream)


    else:
        await ctx.send("Failed to fetch audio.")

#copy this section and configure for as many loras as you have
@bot.command(name='lora')
async def lora(ctx):
    prompt = ' '.join(ctx.message.content.split()[1:])
    audio_file = [""]
    ref_text = [""]
    idstr = "./fish-speech/checkpoints/fish-speech-1.5-custom-lora" # model path
    await fish_request(ctx, prompt, audio_file, ref_text, idstr)

#copy this section and configure for as many zero shot options you want the bot to have
@bot.command(name='zeroshot')
async def zeroshot(ctx):
    prompt = ' '.join(ctx.message.content.split()[1:])
    audio_file = ["./supersmall.mp3"]
    ref_text = ["./supersmall.mp3.txt"]
    idstr = None # model path
    await fish_request(ctx, prompt, audio_file, ref_text, idstr)

# random is awesome and I don't fully understand how it works
@bot.command(name='random')
async def random(ctx):
    prompt = ' '.join(ctx.message.content.split()[1:])
    audio_file = [""]
    ref_text = [""]
    idstr = "./fish-speech/checkpoints/fish-speech-1.5/" # model path
    await fish_request(ctx, prompt, audio_file, ref_text, idstr)

@bot.command(name='voices')
async def voices(ctx):
    await ctx.send("```Usable voices from this bot:\n  !random  \n  !lora  \n  !zeroshot```")

bot.run(DISCORD_TOKEN)
