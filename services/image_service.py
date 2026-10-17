import ollama
import logging

class ImageAnalysisService:
    @staticmethod
    def analyze_image(image_path):
        logging.info(f"LLaVA: Analyzing image at {image_path}")
        # Using LLaVA/Llama 3.2 via local Ollama
        try:
            response = ollama.chat(model='llama3.2:1b', messages=[
                {
                    'role': 'user',
                    'content': 'Describe this image in detail',
                    'images': [image_path]
                }
            ])
            analysis = response['message']['content']
            logging.info(f"LLaVA response: {analysis}")
            return analysis
        except Exception as e:
            logging.error(f"LLaVA Error: {str(e)}")
            return "I had trouble reading that image."
