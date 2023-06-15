import os
import re
import shutil
import requests
import textwrap
from pydub import AudioSegment
from moviepy.editor import (
    ImageSequenceClip,
    AudioFileClip,
    CompositeVideoClip,
    ColorClip,
    TextClip,
)
from nltk.tokenize import sent_tokenize
from google.cloud import texttospeech
from pytrends.request import TrendReq
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox  # Updated import statement
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import threading


class StoryGeneratorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Delete the contents of the "images" directory if it exists
        images_dir = "images"
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
        os.makedirs(images_dir)
        
        # Delete the contents of the "audio" directory if it exists
        audio_dir = "audio"
        if os.path.exists(audio_dir):
            shutil.rmtree(audio_dir)
        os.makedirs(audio_dir)

        # Specify your Google credentials JSON file here
        base_path = os.path.dirname(os.path.abspath(__file__))
        credential_path = os.path.join(base_path, "your_google_credentials.json")  # Change this to your credentials file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path


    def build(self):
        layout = BoxLayout(orientation="vertical")

        tone_label = Label(text="Enter a tone:")
        self.tone_input = TextInput(multiline=False)
        layout.add_widget(tone_label)
        layout.add_widget(self.tone_input)

        length_label = Label(text="Enter a story length:")
        self.length_input = TextInput(multiline=False)
        layout.add_widget(length_label)
        layout.add_widget(self.length_input)

        modifier_label = Label(text="Enter an image modifier:")
        self.modifier_input = TextInput(multiline=False)
        layout.add_widget(modifier_label)
        layout.add_widget(self.modifier_input)

        count_label = Label(text="Enter the number of images per sentence:")
        self.count_input = TextInput(multiline=False)
        layout.add_widget(count_label)
        layout.add_widget(self.count_input)

        trending_searches_label = Label(text="Select 5 trending searches:")
        layout.add_widget(trending_searches_label)

        trending_searches_grid = GridLayout(cols=1, spacing="5dp", size_hint=(0.8, None))
        trending_searches_grid.bind(minimum_height=trending_searches_grid.setter("height"))

        trending_searches_scrollview = ScrollView(size_hint=(1, 0.6))
        trending_searches_scrollview.add_widget(trending_searches_grid)

        self.trending_searches_layout = trending_searches_grid
        layout.add_widget(trending_searches_scrollview)

        self.retrieve_trending_searches(None)  # Call retrieve_trending_searches to populate the trending searches

        generate_button = Button(text="Generate Story", on_press=self.generate_story)
        layout.add_widget(generate_button)

        self.progress_bar = ProgressBar(max=100)
        layout.add_widget(self.progress_bar)

        return layout

    def retrieve_trending_searches(self, instance):
        threading.Thread(target=self.get_trending_searches).start()

    def get_trending_searches(self):
        trending_searches = self.top_trending_searches(20)
        Clock.schedule_once(lambda dt: self.show_trending_searches(trending_searches), 0)


    def show_trending_searches(self, trending_searches):
        for search in trending_searches:
            checkbox_layout = BoxLayout(orientation="horizontal", size_hint=(1, None), height="40dp")

            checkbox = CheckBox(
                size_hint=(None, None),
                size=("40dp", "40dp")
            )
            checkbox_layout.add_widget(checkbox)

            label = Label(
                text=search,
                font_size=12,
                color=get_color_from_hex('#FFFFFF'),
                size_hint=(1, None),
                height="30dp"
            )
            checkbox_layout.add_widget(label)

            self.trending_searches_layout.add_widget(checkbox_layout)

        # Set the background color of the window to black
        Window.clearcolor = get_color_from_hex('#000000')

    def generate_story(self, instance):
        tone = self.tone_input.text.strip()
        length = int(self.length_input.text.strip())
        modifier = self.modifier_input.text.strip()
        count = int(self.count_input.text.strip())

        if tone and length and modifier and count:
            #self.init()

            selected_searches = []
            for checkbox_layout in self.trending_searches_layout.children:
                checkbox = checkbox_layout.children[0].children[0]  # Access the CheckBox object
                if isinstance(checkbox, CheckBox) and checkbox.active:
                    selected_searches.append(checkbox_layout.children[1].text)

            if len(selected_searches) <= 5:
                sentences = self.generate_story_sentences(tone, length, selected_searches)
                media_paths = []

                shutil.rmtree("images")  # Delete the "images" directory and its contents
                os.makedirs("images")  # Recreate an empty "images" directory

                shutil.rmtree("audio")  # Delete the "audio" directory and its contents
                os.makedirs("audio")  # Recreate an empty "audio" directory

                # Start a new thread for image and audio generation
                threading.Thread(target=self.generate_media, args=(sentences, modifier, count, media_paths)).start()

            else:
                print("Please select up to 5 trending searches.")

        else:
            print("Please provide all required inputs.")

    def generate_media(self, sentences, modifier, count, media_paths):
        total_sentences = len(sentences)
        generated_sentences = 0

        for i, sentence in enumerate(sentences):
            print(sentence)

            image_paths = self.generate_image(sentence, modifier, count)
            audio_path = self.generate_audio(sentence)
            media_paths.append((image_paths, audio_path, sentence))

            generated_sentences += 1
            progress = generated_sentences / total_sentences * 100  # Calculate the progress percentage

            # Schedule a function to update the progress bar from the main thread
            Clock.schedule_once(lambda dt, val=progress: self.update_progress(val))

        # After all media is generated, continue with video creation
        Clock.schedule_once(lambda dt: self.create_video(media_paths))

    def update_progress(self, value):
        self.progress_bar.value = value

    def generate_story_sentences(self, tone, length, selected_searches):
        selected_searches_str = ", ".join(selected_searches)
        # Specify your API endpoint here
        url = "https://your-proxy-url.com/api/chat/completions"  # Change this URL to your endpoint
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": f"Make sure to use the following words in your story. Take their order into account, the first terms are most popular. {selected_searches_str}. Your story should only be {length} paragraphs long.",
                },
                {
                    "role": "user",
                    "content": f"Please write a {tone} {length}-paragraph story.",
                },
            ],
        }
        response = requests.post(url, json=payload)
        response_content = response.json()["choices"][0]["message"]["content"]
        sentences = sent_tokenize(response_content)
        return sentences

    def generate_image(self, sentence, modifier, count):
        image_prompt = sentence + " " + modifier
        # Specify your API endpoint here
        url = "https://your-proxy-url.com/api/images"  # Change this URL to your endpoint
        payload = {
            "prompt": image_prompt,
            "n": count,
            "size": "512x512",
        }
        response = requests.post(url, json=payload)

        image_paths = []
        for i, data in enumerate(response.json()["data"]):
            image_url = data["url"]
            filename = re.sub(r"\W+", "", image_prompt) + f"_version_{i}.png"

            # Download and save the image
            image_path = os.path.join("images", filename)
            resp = requests.get(image_url)
            with open(image_path, "wb") as f:
                f.write(resp.content)

            print("Image downloaded:", image_path)
            image_paths.append(image_path)

        return image_paths

    def generate_audio(self, sentence):
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=sentence)

        voice = texttospeech.VoiceSelectionParams(
            name="en-US-Standard-J", language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        filename = re.sub(r"\W+", "", sentence)
        filename += ".wav"

        audio_path = os.path.join("audio", filename)

        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
            print("Audio content written to file", audio_path)
        return audio_path

    def create_video(self, media_paths):
        audio_durations = []
        combined_audio = AudioSegment.empty()
        all_image_paths = []
        subtitle_clips = []
        current_time = 0

        for image_paths, audio_path, sentence in media_paths:
            print(audio_path)
            audio = AudioSegment.from_file(audio_path, format="wav")

            duration = len(audio) / 1000
            audio_durations.extend([duration / len(image_paths)] * len(image_paths))

            combined_audio += audio

            all_image_paths.extend(image_paths)

            start_time = current_time
            end_time = current_time + duration

            wrapped_sentence = "\n".join(textwrap.wrap(sentence, width=50))

            subtitle_clip = TextClip(wrapped_sentence, fontsize=36, color="white")
            subtitle_clip = subtitle_clip.set_position(("center", 1300))
            subtitle_clip = subtitle_clip.set_start(start_time).set_end(end_time)

            subtitle_clips.append(subtitle_clip)

            current_time = end_time

        combined_audio.export("audio/combined_audio.wav", format="wav")

        clip = ImageSequenceClip(all_image_paths, durations=audio_durations)
        clip = clip.set_audio(AudioFileClip("audio/combined_audio.wav"))
        clip = clip.resize(height=900)

        background = ColorClip((900, 1600), col=[0, 0, 0], duration=clip.duration)

        clips = [background, clip.set_position("center")] + subtitle_clips

        final_clip = CompositeVideoClip(clips)

        final_clip.write_videofile("output.mp4", codec="libx264", fps=24)

        os.remove("audio/combined_audio.wav")

    def top_trending_searches(self, n):
        pytrends = TrendReq(hl="en-US", tz=360)
        trending_searches_df = pytrends.trending_searches(pn="united_states")
        trending_searches_list = trending_searches_df[0].values.tolist()
        return trending_searches_list[:n]

    def play_video(self, video_path):
        os.startfile(video_path)  # Open the video file using the default player


if __name__ == "__main__":
    StoryGeneratorApp().run()
