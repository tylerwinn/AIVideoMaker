import os
import re
import sys
import requests
import openai
import textwrap
from pydub import AudioSegment
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip, ColorClip, TextClip
from nltk.tokenize import sent_tokenize
from google.cloud import texttospeech

global client

def init():
    # Create the "images" folder if it doesn't exist
    if not os.path.exists("images"):
        os.makedirs("images")

    # Ensure the 'audio' directory exists
    if not os.path.exists('audio'):
        os.makedirs('audio')

    base_path = os.path.dirname(os.path.abspath(__file__))
    credential_path = os.path.join(base_path, "bin", "analog-daylight-387914-be5cfb00ab87.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
    openai.api_key = "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"

def generate_story(story_prompt, story_length):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=float(.7),
        messages=[
            {"role": "system", "content": f"You are an award-winning short story writer. Your works remind the reader of the works of Ernest Hemingway, Stephen King, and Ray Bradbury. Your story should only be {story_length} paragraphs long."},
            {"role": "user", "content": f"Please write a {story_prompt} story. Ensure that the tension constantly rises throughout, and concludes with the climax. Exclude a resolution paragrah/sentence."}
        ]
    )

    response_content = response['choices'][0]['message']['content']
    sentences = sent_tokenize(response_content)
    return sentences

def generate_image(image_prompt, tone, modifier, count):
    image_prompt += ' ' + tone + ' ' + modifier
    response = openai.Image.create(
        prompt=image_prompt,
        n=count,
        size="512x512"
    )

    image_paths = []
    for i, data in enumerate(response['data']):
        image_url = data['url']
        filename = re.sub(r'\W+', '', image_prompt) + f"_version_{i}.png"

        # Download and save the image
        image_path = os.path.join("images", filename)
        resp = requests.get(image_url)
        with open(image_path, "wb") as f:
            f.write(resp.content)

        print("Image downloaded:", image_path)
        image_paths.append(image_path)

    return image_paths

def generate_audio(audio_prompt):
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=audio_prompt)

    voice = texttospeech.VoiceSelectionParams(
        name="en-US-Standard-J", language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    filename = re.sub(r'\W+', '', audio_prompt)
    filename += ".wav"

    # Save the audio to the 'audio' directory
    audio_path = os.path.join("audio", filename)

    # The response's audio_content is binary.
    with open(audio_path, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file', audio_path)
    return audio_path

def generate_video(media_paths, output_filename):
    # Initialize a list to store the duration of each audio file (in seconds)
    audio_durations = []

    # Initialize an empty audio track
    combined_audio = AudioSegment.empty()

    # Initialize an empty list to store all the image paths
    all_image_paths = []

    # Initialize an empty list to store all subtitle clips
    subtitle_clips = []

    # Initialize a variable to track the current time in the video
    current_time = 0

    # Loop through each tuple in media_paths
    for image_paths, audio_path, sentence in media_paths:
        # Load the audio file
        print(audio_path)
        audio = AudioSegment.from_file(audio_path, format="wav")

        # Get the duration of the audio file in seconds
        duration = len(audio) / 1000  # Convert from milliseconds to seconds

        # Append the duration divided by the number of image variations
        # This will make each image variation appear for an equal amount of time
        audio_durations.extend([duration / len(image_paths)] * len(image_paths))

        # Concatenate the audio file to the end of the combined audio track
        combined_audio += audio

        # Extend the all_image_paths list with the image paths
        all_image_paths.extend(image_paths)

        # Calculate the start time and end time for this sentence
        start_time = current_time
        end_time = current_time + duration

        # Wrap long sentences
        wrapped_sentence = "\n".join(textwrap.wrap(sentence, width=50))

        # Create a subtitle clip for this sentence
        subtitle_clip = TextClip(wrapped_sentence, fontsize=36, color='white')

        # Position the subtitle off the bottom of the screen
        subtitle_clip = subtitle_clip.set_position(('center', 1300))  # You can adjust the y-value as needed

        # Set the start and end times for this subtitle
        subtitle_clip = subtitle_clip.set_start(start_time).set_end(end_time)

        # Add this subtitle clip to the list
        subtitle_clips.append(subtitle_clip)

        # Update the current time
        current_time = end_time

    # Save the combined audio track to a file
    combined_audio.export("audio/combined_audio.wav", format='wav')

    # Create an image sequence clip with the durations specified
    clip = ImageSequenceClip(all_image_paths, durations=audio_durations)

    # Set the audio of the video clip to the combined audio track
    clip = clip.set_audio(AudioFileClip("audio/combined_audio.wav"))  # Use AudioFileClip instead of a string

    # Resize the clip to a fixed height while maintaining aspect ratio
    clip = clip.resize(height=900)  # You can choose a suitable height based on the original image size

    # Create a black background clip with a 9:16 aspect ratio
    background = ColorClip((900, 1600), col=[0, 0, 0], duration=clip.duration)  # 900 (width) and 1600 (height) for a 9:16 aspect ratio

    # Prepare list of all clips (background, main content, and subtitles)
    clips = [background, clip.set_position("center")] + subtitle_clips

    # Generate the final composite clip
    final_clip = CompositeVideoClip(clips)

    # Write the result to a file
    final_clip.write_videofile(output_filename, codec='libx264', fps=24)

    # Delete the temporary combined audio file
    os.remove("combined_audio.mp3")

if __name__ == "__main__":
    # Check if a story prompt argument is provided
    if len(sys.argv) > 4:
        tone = sys.argv[1]
        length = int(sys.argv[2])
        modifier = sys.argv[3]
        count = int(sys.argv[4])
        init()
        sentences = generate_story(tone, length)
        media_paths = []
        os.makedirs("images", exist_ok=True)  # Ensure the 'images' directory exists
        for sentence in sentences:
            print(sentence)
            image_paths = generate_image(sentence, tone, modifier, count)  # Now, image_paths is a list
            audio_path = generate_audio(sentence)
            media_paths.append((image_paths, audio_path, sentence))  # Here, image_paths is a list
      
        generate_video(media_paths, "output.mp4") 
    else:
        print("Please provide a story modifier. (Scary, Cool, etc)")
