import discord
from discord.ext import commands
import os
import re
import sys
import asyncio
import subprocess

class SwarmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.register_swarm_commands()

    def register_swarm_commands(self):
        agents_dir = "~/Workspace/Documents/openmanus/Abraraiv2"
        if not os.path.exists(agents_dir):
            print(f"[SwarmCog] Swarm directory not found: {agents_dir}")
            return

        # Find folders that start with digits followed by underscore
        folders = [
            d for d in os.listdir(agents_dir)
            if os.path.isdir(os.path.join(agents_dir, d)) and d[0].isdigit() and "_" in d
        ]
        
        # Sort folders numerically to maintain order
        folders.sort(key=lambda x: int(x.split("_")[0]))

        for folder in folders:
            # Extract name and clean it up for Discord's application command rules
            # Rules: lowercase, alphanumeric and dashes only, 1-32 chars
            parts = folder.split("_", 1)
            if len(parts) > 1 and parts[0].isdigit():
                clean_name = parts[1].lower().replace("_", "-")
            else:
                clean_name = folder.lower().replace("_", "-")

            clean_name = re.sub(r'[^a-z0-9-]', '', clean_name)
            # Discord commands limit is 32 chars, truncate if needed
            clean_name = clean_name[:32]
            
            if not clean_name:
                continue

            # Closure wrapper to capture the specific folder and clean_name
            def make_callback(f_name=folder, c_name=clean_name):
                async def callback(interaction: discord.Interaction, task: str):
                    await interaction.response.defer()

                    loop = asyncio.get_running_loop()
                    def run_cmd():
                        # Run run_swarm.py passing the task and the direct agent folder
                        res = subprocess.run(
                            [sys.executable, "run_swarm.py", task, f_name],
                            cwd=agents_dir,
                            capture_output=True,
                            text=True
                        )
                        return res

                    try:
                        res = await loop.run_in_executor(None, run_cmd)
                        output = res.stdout
                        if res.returncode != 0:
                            output = f"Error: {res.stderr}"

                        if not output.strip():
                            output = "(No output returned from agent)"

                        # Handle Discord's 2000-character limit
                        if len(output) > 1900:
                            file_path = f"/tmp/{c_name}_output.txt"
                            with open(file_path, "w") as f:
                                f.write(output)
                            await interaction.followup.send(
                                content=f"🤖 **{c_name}** output is too long. File attached:",
                                file=discord.File(file_path)
                            )
                        else:
                            await interaction.followup.send(content=f"🤖 **{c_name}** Output:\n```\n{output}\n```")
                    except Exception as e:
                        await interaction.followup.send(content=f"❌ Error running {c_name}: {str(e)}")

                return callback

            # Create dynamic app command
            cmd = discord.app_commands.Command(
                name=clean_name,
                description=f"Directly execute a task using the {clean_name} agent",
                callback=make_callback(folder, clean_name)
            )
            
            # Add to command tree
            try:
                self.bot.tree.add_command(cmd)
            except Exception as e:
                print(f"[SwarmCog] Failed to register dynamic slash command /{clean_name}: {e}")

async def setup(bot):
    await bot.add_cog(SwarmCog(bot))
