import subprocess
import json
import shlex

class SearchService:
    def __init__(self):
        pass

    def search(self, query):
        try:
            # We must double-quote for the local shell and the remote shell
            inner_cmd = shlex.quote(f"python3 ~/remote_search.py {query}")
            cmd = f"gcloud cloud-shell ssh --command={inner_cmd} --quiet"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return f"Cloud Search Error: {result.stderr}"
            
            # Clean output (remove GCP warnings)
            output = result.stdout
            if "[" in output:
                json_part = output[output.find("[") : output.rfind("]") + 1]
                data = json.loads(json_part)
            else:
                return f"Google search returned no results (Remote). Raw: {output}"

            if isinstance(data, str) and data.startswith("Error"):
                return data

            if not data:
                return "Google search returned no results on Cloud VM."
            
            formatted_results = []
            for item in data:
                formatted_results.append(f"**{item['title']}**\n{item['link']}\n{item['snippet'][:200]}...\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Remote Google search failed: {str(e)}"
