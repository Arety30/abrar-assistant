from elevenlabs import ElevenLabs
import os

class VoiceService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.client = ElevenLabs(api_key=self.api_key)

    def generate_audio(self, text, output_filename="~/Workspace/AbrarAssistant/data/speech.mp3"):
        try:
            # Correct method for latest ElevenLabs SDK
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )
            
            # The convert method returns a generator of bytes
            with open(output_filename, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)
            
            return output_filename
        except Exception as e:
            return f"Audio Error: {str(e)}"
