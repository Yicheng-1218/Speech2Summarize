# DocsAgent

DocsAgent is an application based on speech-to-text technology, designed to assist with document processing through audio handling and text generation. This project uses Docker containerization for deployment and supports multi-platform environments.

### Features

- Speech to text functionality
- Support for local audio file processing
- REST API for data processing
- Docker containerized deployment

### Installation

#### Prerequisites

- **Docker**: Ensure Docker and Docker Compose are installed on your local system.
- **Python 3.x**: Install Python version 3.x and the necessary packages.

#### Speech to Text Module (speech_2_text)

If you are using a Windows system, you need to install `ffmpeg` in the `speech_2_text` directory. You can download `ffmpeg` from the following link:  
[ffmpeg download](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z)

#### Directory Structure

After downloading and installing `ffmpeg`, ensure the directory structure is as follows:

<pre>
speech_2_text    
└── ffmpeg
    └── bin
        ├── ffmpeg.exe
        ├── ffplay.exe
        └── ffprobe.exe  
</pre>

### Running the Project

To deploy and run the project using Docker containers, run the following command:

```sh
$ docker-compose up -d --build
```

This will build and start the containers, running the project in the background.

Usage
Upload audio files to the speech_2_text module, ensuring ffmpeg is properly installed.
Run the application inside the Docker container and interact with the backend through the REST API.
