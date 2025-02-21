# fish-speech-discord

Kind of a manual thing right now, I will pretty this up if even a single person wants it.
It is probably possible to use the official fish-speech api, you'll need to change the url and api key, not tested.

# Instructions

0. You will need to run a fish-speech api server separate from this repo

    ```bash
    python3 -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path "checkpoints/fish-speech-1.5" --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" --decoder-config-name firefly_gan_vq --compile
    ```

1. Clone the repo
2. Create a `.env` with your discord bot token

    ```bash
    DISCORD_TOKEN="<your discord token>"
    ```

3. Install python dependencies

    ```bash
    python3 -m venv venv
    source ./venv/bin/activate
    pip3 install -r requirements.txt
    ```

   There are probably some unnecessary reqs in there that carried over from fish-speech's main repo.

4. The `pyproject.toml` file is messed up or I am too ignorant, you need to copy `fish-speech/fish-speech` to the same directory you have `fish-discord.py`

5. Modify the python to point to your checkpoints and mp3s (for any zeroshot's you want to do)

    ```python
    # Copy this section and configure for as many zero shot options you want the bot to have
    @bot.command(name='zeroshot')
    async def zeroshot(ctx):
        prompt = ' '.join(ctx.message.content.split()[1:])
        audio_file = ["./supersmall.mp3"]
        ref_text = ["./supersmall.mp3.txt"]
        idstr = None  # model path
        await fish_request(ctx, prompt, audio_file, ref_text, idstr)
    ```

6. If your API server is not at `localhost`, you'll need to change the URL in the script.

7. Run the python script.

    ```bash
    python3 fish-discord.py
    ```

