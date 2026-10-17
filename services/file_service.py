import os

class FileService:
    def __init__(self, base_dir="~/Workspace/AbrarAssistant/data"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def write_file(self, filename, content):
        try:
            # Ensure we don't escape the data folder for safety
            safe_name = os.path.basename(filename)
            path = os.path.join(self.base_dir, safe_name)
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"File Write Error: {str(e)}"

    def read_file(self, filename):
        try:
            safe_name = os.path.basename(filename)
            path = os.path.join(self.base_dir, safe_name)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
            else:
                return "Error: File not found."
        except Exception as e:
            return f"File Read Error: {str(e)}"
