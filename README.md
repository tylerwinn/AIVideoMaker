# AI Video Maker App

AI Video Maker is a Python application that generates videos based on user input. It leverages the Google Text-to-Speech API for voiceover and a GPT model for script generation. This app also fetches trending topics and allows users to select from them.

## Examples/Results

[TikTok](https://www.tiktok.com/@tylerdoesthings2/video/7242107662530268459) </br>
[Youtube](https://www.youtube.com/watch?v=2ZVtaHbvU4I)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed Python 3.x
- You have a Windows/Linux/Mac machine with a compatible Python version.
- You have set up a Google Cloud account, enabled Text-to-Speech API, and generated an authentication JSON file (See [Setting up Google Cloud Account](#setting-up-google-cloud-account)).
- You have a proxy URL endpoint for the GPT model (See [Setting up GPT Proxy URL](#setting-up-gpt-proxy-url)).

## Setting Up Google Cloud Account

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. In the left sidebar, select APIs & Services > Dashboard.
4. Click on "+ ENABLE APIS AND SERVICES".
5. Search for "Text-to-Speech API" and enable it for your project.
6. In the left sidebar, select APIs & Services > Credentials.
7. Click on "Create credentials" and choose "Service account".
8. Follow the prompts to create a service account and save the generated JSON file.

## Setting Up GPT Proxy URL

[https://github.com/tylerwinn/chatgpt-proxy](https://github.com/tylerwinn/chatgpt-proxy)

## Installing AI Video Maker

To install AI Video Maker, follow these steps:

1. Clone the repository:
    ```
    git clone https://github.com/tylerwinn/AIVideoMaker.git
    ```
2. Navigate to the project directory:
    ```
    cd AIVideoMaker
    ```
3. Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```
4. Place your Google API JSON file in the project directory.

## Configuring the Application

Before running the app, you must configure it by setting the following:

1. In the file `video.py`, set the `credential_path` variable to the path of your Google API JSON file.
2. In the same file, update the `url` variable under the `generate_script` method with your GPT proxy URL.

## Running AI Video Maker

To run AI Video Maker, execute the following command:
```
python video.py
```

