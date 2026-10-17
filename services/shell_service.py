import subprocess
import os

import subprocess
import os
import shlex
import threading
import time

class CloudShellService:
    """Shell service that executes commands on the Google Cloud Shell VM with keep-alive logic."""
    def __init__(self):
        self.cwd = "~" 
        self.interactive_cmds = ['nano', 'vim', 'vi', 'top', 'htop', 'less', 'more', 'man', 'passwd', 'git log']
        # Start a heartbeat thread to keep the VM alive
        self.heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def _heartbeat(self):
        """Sends a small command every 45 seconds to prevent VM timeout."""
        while True:
            try:
                # Use a very light command to keep the session active
                subprocess.run("gcloud cloud-shell ssh --command='true' --quiet", shell=True, capture_output=True, timeout=30)
            except:
                pass
            time.sleep(45)

    def execute_command(self, command):
        try:
            cmd_strip = command.strip()
            
            if any(ic in cmd_strip for ic in self.interactive_cmds):
                return f"Error: '{cmd_strip.split(' ')[0]}' is interactive. Use non-interactive alternatives."

            if cmd_strip.startswith("cd "):
                parts = cmd_strip.split(" ", 1)
                new_dir = parts[1].strip() if len(parts) > 1 else "~"
                
                # Check directory on VM
                test_cmd = f"gcloud cloud-shell ssh --command=\"cd {self.cwd} && cd {new_dir} && pwd\" --quiet"
                result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    self.cwd = result.stdout.strip()
                    return f"Changed remote directory to: {self.cwd}"
                else:
                    return f"Error: Directory not found on Cloud VM: {new_dir}"

            # Run command with --authorize-session to keep session active
            remote_cmd = f"cd {self.cwd} && {cmd_strip}"
            gcloud_cmd = f"gcloud cloud-shell ssh --authorize-session --command={shlex.quote(remote_cmd)} --quiet"
            
            result = subprocess.run(
                gcloud_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300 # 5 minutes for heavy commands
            )
            
            output = result.stdout
            error = result.stderr
            
            response = ""
            if output:
                response += output
            if error:
                # Filter out standard SSH/GCP warnings
                noise = ["Warning: Permanently added", "Automatic authentication", "Rerun command with"]
                if not any(n in error for n in noise):
                    if response: response += "\n"
                    response += f"Stderr:\n{error}"
            
            return response if response.strip() else "[Command executed successfully on Cloud VM]"

        except subprocess.TimeoutExpired:
            return "Error: Command timed out. The Cloud Shell VM might have shut down or is under heavy load."
        except Exception as e:
            return f"Cloud Shell Error: {str(e)}"
