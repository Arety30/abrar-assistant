import os
import discord
import asyncio
import ollama
import logging
import re
from discord.ext import commands
from dotenv import load_dotenv

# Setup
load_dotenv(dotenv_path='~/Workspace/AbrarAssistant/.env', override=True)
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# OAuth Callback Server
import oauth_server

# Cogs
from cogs.oauth_cog import OAuthCog
from cogs.swarm_cog import SwarmCog

async def load_cogs():
    await bot.add_cog(OAuthCog(bot))
    await bot.add_cog(SwarmCog(bot))

@bot.event
async def on_ready():
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) with Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f'Logged in as {bot.user}')


# Services
from services.pdf_service import PDFService
from services.voice_service import VoiceService
from services.google_service import GoogleWorkspaceService
from services.image_service import ImageAnalysisService
from services.search_service import SearchService
from services.shell_service import CloudShellService
from services.memory_service import MemoryService
from services.file_service import FileService

pdf_service = PDFService()
voice_service = VoiceService()
google_service = GoogleWorkspaceService()
image_service = ImageAnalysisService()
search_service = SearchService()
shell_service = CloudShellService()
memory_service = MemoryService()
file_service = FileService()

async def ai_router(user_id, text):
    """Analyzes message and provides direct actionable output or response with memory."""
    history = memory_service.get_history(user_id)
    history_str = "\n".join([f"User: {h[0]}\nBot: {h[1]}" for h in history])
    
    prompt = f"""
    You are Abrar AI, an intelligent assistant.
    
    STRICT COMMUNICATION RULES:
    1. For normal chat, respond ONLY with plain text.
    2. USE ACTION: SPEAK ONLY if the user explicitly asks for a "voice note", "audio file", or says "say this out loud".
    3. NEVER use ACTION: SPEAK to just reply to a question.
    
    ACTION PROTOCOL:
    - ACTION: SEARCH [query] - If searching is needed.
    - ACTION: SPEAK [text] - ONLY IF EXPLICITLY ASKED FOR AUDIO.
    - ACTION: SPREADSHEET [title] | [data]
    - ACTION: PPT [title] | [content]
    - ACTION: WRITE_FILE filename | content
    - ACTION: READ_FILE filename
    - ACTION: ANALYZE - Analyze an image.
    
    CURRENT CONTEXT:
    {history_str}
    USER REQUEST: "{text}"
    
    (Normal response = TEXT ONLY. Audio response = ACTION: SPEAK)
    """
    resp = await asyncio.to_thread(ollama.chat, model='llama3.2:3b', messages=[{'role': 'user', 'content': prompt}])
    response = resp['message']['content'].strip()
    return response

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    user_id = str(message.author.id)
    text = message.content.strip()

    # Direct Shell Access
    if text.startswith('$'):
        command = text[1:].strip()
        msg = await message.channel.send(f"**cloud-shell@airecptionist3012:~$** `{command}` (Starting Cloud VM...)")
        
        # Use run_in_executor to avoid blocking the main event loop
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, shell_service.execute_command, command)
            memory_service.add_history(user_id, f"Direct Shell: {command}", result)
            await msg.edit(content=f"**cloud-shell@airecptionist3012:~$** `{command}`\n```\n{result}\n```")
        except Exception as e:
            await msg.edit(content=f"**cloud-shell@airecptionist3012:~$** `{command}`\n❌ Error: {str(e)}")
        return
    
    # Process conversational AI
    response = await ai_router(user_id, text)
    
    # Robust Action Parsing
    match = re.search(r'(?i)ACTION:\s*(\w+)\s*(.*)', response)
    
    if match:
        action_type = match.group(1).upper()
        details = match.group(2).strip()
        
        result_to_save = ""
        if "SPEAK" in action_type:
            await message.channel.send(f"🎙️ Generating voice note for: \"{details}\"...")
            filename = voice_service.generate_audio(details)
            if filename.startswith("Audio Error"):
                await message.channel.send(f"❌ {filename}")
                result_to_save = filename
            else:
                await message.channel.send(file=discord.File(filename))
                result_to_save = f"Generated voice note: {filename}"
        elif "SPREADSHEET" in action_type:
            parts = details.split("|", 1)
            title = parts[0].strip() if len(parts) > 1 else "New Sheet"
            data = parts[1].strip() if len(parts) > 1 else details
            try:
                result = google_service.create_spreadsheet(title, data)
                await message.channel.send(f"📊 Created Spreadsheet: {result}")
                result_to_save = result
            except Exception as e:
                await message.channel.send(f"❌ Spreadsheet Error: {str(e)}")
                result_to_save = str(e)
        elif "PPT" in action_type:
            parts = details.split("|", 1)
            title = parts[0].strip() if len(parts) > 1 else "New Presentation"
            content = parts[1].strip() if len(parts) > 1 else details
            try:
                result = google_service.create_presentation(title, content)
                await message.channel.send(f"📽️ Created Presentation: {result}")
                result_to_save = result
            except Exception as e:
                await message.channel.send(f"❌ PPT Error: {str(e)}")
                result_to_save = str(e)
        elif "SEARCH" in action_type:
            if "[query]" in details or "Search Google" in details:
                 await message.channel.send(response.replace("ACTION:", "").strip())
                 return
            await message.channel.send(f"🔍 Searching for: {details}...")
            results = search_service.search(details)
            await message.channel.send(f"Search Results:\n{results}")
            result_to_save = results
        elif "WRITE_FILE" in action_type:
            parts = details.split("|", 1)
            if len(parts) == 2:
                name, content = parts[0].strip(), parts[1].strip()
                result = file_service.write_file(name, content)
                await message.channel.send(f"💾 {result}")
                result_to_save = result
            else:
                await message.channel.send("Error: Use 'WRITE_FILE filename | content'")
        elif "READ_FILE" in action_type:
            result = file_service.read_file(details)
            await message.channel.send(f"📖 **Contents of {details}:**\n```\n{result}\n```")
            result_to_save = result
        elif "ANALYZE" in action_type:
            if message.attachments:
                attachment = message.attachments[0]
                file_path = f"~/Workspace/AbrarAssistant/data/{attachment.filename}"
                await attachment.save(file_path)
                analysis = image_service.analyze_image(file_path)
                await message.channel.send(f"👁️ Image Analysis:\n{analysis}")
                result_to_save = analysis
            else:
                await message.channel.send("Please attach an image to analyze.")
                result_to_save = "Failed: No image attached."
        
        memory_service.add_history(user_id, text, f"ACTION: {action_type} {details}\nResult: {result_to_save}")
    else:
        memory_service.add_history(user_id, text, response)
        await message.channel.send(response)
    
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

async def main():
    await bot.start(os.getenv('DISCORD_BOT_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())
