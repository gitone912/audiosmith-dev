# Realtime_Audio_Transcriber

Brief description of your Django project.
![GIF](https://raw.githubusercontent.com/ananty1/Realtime_Audio_Transcriber/main/media/Building%20a%20Real-Time%20Transcription%20App%20with%20Django%20and%20DeepGram.gif)

## Table of Contents

- [Realtime\_Audio\_Transcriber](#realtime_audio_transcriber)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Development](#development)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ananty1/Realtime_Audio_Transcriber
   cd Realtime_Audio_Transcriber

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt

3. Apply the migrations 

    ```bash
   python manage.py migrate
    
## Usage

   ```bash
   python manage.py runserver
   ```

The server will start at port `localhost:8000`

## Configuration
If you are attempting to deploy, follow these steps:
Create a .env file in the project directory.
1. Update the PostgreSQL credentials in settings.py::

   ```bash
   DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'your_db_name',
            'USER': 'your_db_user',
            'PASSWORD': 'your_db_password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

2. Set the Deepgram API credentials in your .env file::

   ```bash
   DEEPGRAM_API_KEY=your_deepgram_api_key


## Development

1. Virtual Environment:

   ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows, use `venv\Scripts\activate`

