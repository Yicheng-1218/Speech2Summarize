# DocsAgent

## speech_2_text

If you are using Windows system, you need to install ffmpeg in the following directory: speech_2_text  
[ffmpeg download](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z)  

Make sure the directory structure should be as follows:  
<pre>
speech_2_text    
└── ffmpeg
    └── bin
        ├── ffmpeg.exe
        ├── ffplay.exe
        └── ffprobe.exe  
</pre>

Spin up the containers:

```sh
$ docker-compose up -d --build
```

