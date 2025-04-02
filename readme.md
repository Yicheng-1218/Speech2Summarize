# Speech2Summarize

**Speech2Summarize** is an AI-powered system that converts audio input into concise summaries.  
It leverages **Whisper** for speech-to-text transcription and utilizes **Celery + Redis** to handle summarization tasks asynchronously using GPT-based models.  
Designed with a focus on performance and scalability, the system is containerized via Docker for multi-platform deployment.

## Features

- Convert speech to text using Whisper
- Support for local audio file processing
- Asynchronous summarization powered by Celery & Redis
- RESTful API for audio upload and summary retrieval
- Dockerized deployment for ease of use and scalability

## Installation

### Prerequisites

- **Docker**: Ensure Docker and Docker Compose are installed on your local system.
- **Python 3.x**: Install Python version 3.x and the necessary packages.

### Speech to Text Module (speech_2_text)

If you are using a Windows system, you need to install `ffmpeg` in the `speech_2_text` directory. You can download `ffmpeg` from the following link: [ffmpeg download](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z)

### Directory Structure

After downloading and installing `ffmpeg`, ensure the directory structure is as follows:

<pre>
speech_2_text    
└── ffmpeg
    └── bin
        ├── ffmpeg.exe
        ├── ffplay.exe
        └── ffprobe.exe  
</pre>

## Running the Project

To deploy and run the project using Docker containers, run the following command:

```sh
$ docker-compose up -d --build
```

This will build and start the containers, running the project in the background.

Usage
Upload audio files to the speech_2_text module, ensuring ffmpeg is properly installed.
Run the application inside the Docker container and interact with the backend through the REST API.

## License
This project is licensed under the MIT License.
