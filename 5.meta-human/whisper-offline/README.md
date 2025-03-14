# whisper-onnx-cpu
PyTorch free.

This repository has been reimplemented with ONNX using [zhuzilin/whisper-openvino](https://github.com/zhuzilin/whisper-openvino) as a reference.

No need to install PyTorch or TensorFlow. All backend logic using PyTorch was rewritten to a Numpy implementation from scratch.

Click here for GPU version: https://github.com/PINTO0309/whisper-onnx-tensorrt

## 1. Environment
Although it can run directly on the host PC, I strongly recommend the use of Docker to avoid breaking the environment.

1. Docker
2. onnx 1.16.1
3. onnxruntime 1.18.1
4. etc (See Dockerfile.xxx)

## 2. Converted Models
https://github.com/PINTO0309/PINTO_model_zoo/tree/main/381_Whisper

## 3. Docker run
Do not use this Docker container in its raw, unprocessed form for operations. It is intended for simple testing only, so administrative privileges have been effectively disabled.
```bash
git clone https://github.com/PINTO0309/whisper-onnx-cpu.git && cd whisper-onnx-cpu

docker run --rm -it \
-v `pwd`:/workdir \
--device /dev/snd:/dev/snd \
pinto0309/whisper-onnx-cpu
```

## 4. Docker build
If you do not need to build the docker image by yourself, you do not need to perform this step.
### 4-1. CPU ver
```bash
docker build -t whisper-onnx-cpu -f Dockerfile.cpu .
```
### 4-2. docker run
```bash
docker run --rm -it \
-v `pwd`:/workdir \
--device /dev/snd:/dev/snd \
whisper-onnx-cpu
```

## 5. Transcribe
- `--mode` option
    ```
    mic  : Microphone
    audio: Audito File
    ```
- `--language` option

    Fixes the language to be recognized to the specified language. See: [6. Languages](#6-languages)

- `--model` option

  I have a Large size model committed [here](https://github.com/PINTO0309/PINTO_model_zoo/tree/main/381_Whisper), but I was too lazy to provide it to you guys, so I excluded it as an option.
    ```
    tiny.en
    tiny
    base.en
    base
    small.en
    small
    medium.en
    medium
    ```
- command

    The onnx file is automatically downloaded when the sample is run. If `--language` is not specified, the tokenizer will auto-detect the language. If you are using a CPU with Hyper-Threading enabled, the code is written so that onnxruntime will infer in parallel with `(number of physical CPU cores * 2 - 1)` to maximize performance. I don't have a high-end CPU, so please try it with a wealthy CPU with about 128 threads.
    ![image](https://github.com/PINTO0309/whisper-onnx-cpu/assets/33194443/7e9c972b-24c6-4b45-9dc7-a06564ce976e)
    If you are using a CPU with Hyper-Threading disabled, you may need to comment out the `sess_options` line below.
    1. https://github.com/PINTO0309/whisper-onnx-cpu/blob/94535cb1ea78ff78c3b8e4cad8dc4e9363f591dc/whisper/model.py#L103-L112
    2. https://github.com/PINTO0309/whisper-onnx-cpu/blob/94535cb1ea78ff78c3b8e4cad8dc4e9363f591dc/whisper/model.py#L141-L150

    e.g.
    ```python
    # From:
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = psutil.cpu_count(logical=True) - 1

    # To:
    # sess_options = ort.SessionOptions()
    # sess_options.intra_op_num_threads = psutil.cpu_count(logical=True) - 1
    ```
    ```python
    # From:
    sess_options=sess_options,

    # To:
    # sess_options=sess_options,
    ```
    Run.
    ```bash
    python whisper/transcribe.py --audio xxxx.mp4 --model medium --beam_size 3
    ```
- results
    ```
    [00:00.000 --> 00:07.240] ステレオ振動推定モデルの最適化 としまして 後半のパート2は 実践
    [00:07.240 --> 00:11.600] のデモを交えまして 普段 私がどのようにモデルを最適化して 様々な
    [00:11.600 --> 00:15.040] フレームワークの環境へデプロイ してるかというのを 実際に操作
    [00:15.040 --> 00:18.280] をこの画面上で見ていただきながら ご理解いただけるように努めたい
    [00:18.280 --> 00:23.640] と思います それでは早速ですが こちらのGitHubの方に 本日の講演
    [00:23.640 --> 00:27.120] 内容については 全てチュートリアル をまとめてコミットしております
    [00:27.120 --> 00:33.880] 2021.0.28 Intel Deep Learning Day HITNET DEMO というちょっと長い名前なんですけ
    [00:33.880 --> 00:39.120] れども 現状はプライベートになって ますが この講演のタイミングでパブリック
    [00:39.120 --> 00:43.280] の方に変更したいと思っております 基本的にはこちらの上から順番
    [00:43.280 --> 00:49.240] にチュートリアルをなぞっていく という形になります まず 本日
    [00:49.240 --> 00:53.480] 対象にするモデルの内容なんですけ れども Google Researchが公開している
    [00:53.480 --> 00:58.240] ヒットネットというステレオ振動 推定モデルになります ステレオ
    [00:58.240 --> 01:01.600] 振動推定って何だよっていう話 なんですけれども こういう一つ
    [01:01.600 --> 01:09.480] のカメラに二つのRGBのカメラが ついてるタイプの撮影機器を使って
    [01:09.480 --> 01:13.600] 左目と右目の両方から画像を同時に 取得して記録していくと そういう
    [01:13.600 --> 01:18.240] シチュエーションにおいて2枚の 画像を同時にモデルに入力する
    ```
- parameters
    ```
    usage: transcribe.py
        [-h]
        [--mode {audio,mic}]
        [--audio [AUDIO [AUDIO ...]]]
        [--model {tiny.en,tiny,base.en,base,small.en,small,medium.en,medium}]
        [--output_dir OUTPUT_DIR]
        [--verbose VERBOSE]
        [--task {transcribe,translate}]
        [--language {af, am, ...}]
        [--temperature TEMPERATURE]
        [--best_of BEST_OF]
        [--beam_size BEAM_SIZE]
        [--patience PATIENCE]
        [--length_penalty LENGTH_PENALTY]
        [--suppress_tokens SUPPRESS_TOKENS]
        [--initial_prompt INITIAL_PROMPT]
        [--condition_on_previous_text CONDITION_ON_PREVIOUS_TEXT]
        [--temperature_increment_on_fallback TEMPERATURE_INCREMENT_ON_FALLBACK]
        [--compression_ratio_threshold COMPRESSION_RATIO_THRESHOLD]
        [--logprob_threshold LOGPROB_THRESHOLD]
        [--no_speech_threshold NO_SPEECH_THRESHOLD]

    optional arguments:
      -h, --help
        show this help message and exit
      --mode {audio,mic}
        audio: Audio file, mic: Microphone
        (default: audio)
      --audio [AUDIO [AUDIO ...]]
        Specify the path to at least one or more audio files (mp4, mp3, etc.).
        e.g. --audio aaa.mp4 bbb.mp3 ccc.mp4
        (default: None)
      --model {tiny.en,tiny,base.en,base,small.en,small,medium.en,medium}
        name of the Whisper model to use
        (default: small)
      --output_dir OUTPUT_DIR, -o OUTPUT_DIR
        directory to save the outputs
        (default: .)
      --verbose VERBOSE
        whether to print out the progress and debug messages
        (default: True)
      --task {transcribe,translate}
        whether to perform X->X speech recognition ('transcribe') or
        X->English translation ('translate')
        (default: transcribe)
      --language {af, am, ...}
        language spoken in the audio, specify None to perform language detection
        See: [6. Languages](#6-languages)
        (default: None)
      --temperature TEMPERATURE
        temperature to use for sampling
        (default: 0)
      --best_of BEST_OF
        number of candidates when sampling with non-zero temperature
        (default: 5)
      --beam_size BEAM_SIZE
        number of beams in beam search, only applicable when temperature is zero
        (default: 5)
      --patience PATIENCE
        optional patience value to use in beam decoding,
        as in https://arxiv.org/abs/2204.05424,
        the default (1.0) is equivalent to conventional beam search
        (default: None)
      --length_penalty LENGTH_PENALTY
        optional token length penalty coefficient (alpha) as in
        https://arxiv.org/abs/1609.08144, uses simple lengt normalization by default
        (default: None)
      --suppress_tokens SUPPRESS_TOKENS
        comma-separated list of token ids to suppress during sampling;
        '-1' will suppress most special characters except common punctuations
        (default: -1)
      --initial_prompt INITIAL_PROMPT
        optional text to provide as a prompt for the first window.
        (default: None)
      --condition_on_previous_text CONDITION_ON_PREVIOUS_TEXT
        if True, provide the previous output of the model as a prompt for the next window;
        disabling may make the text inconsistent across windows, but the model becomes
        less prone to getting stuck in a failure loop
        (default: True)
      --temperature_increment_on_fallback TEMPERATURE_INCREMENT_ON_FALLBACK
        temperature to increase when falling back when the decoding fails to meet either of
        the thresholds below
        (default: 0.2)
      --compression_ratio_threshold COMPRESSION_RATIO_THRESHOLD
        if the gzip compression ratio is higher than this value, treat the decoding as failed
        (default: 2.4)
      --logprob_threshold LOGPROB_THRESHOLD
        if the average log probability is lower than this value, treat the decoding as failed
        (default: -1.0)
      --no_speech_threshold NO_SPEECH_THRESHOLD
        if the probability of the <|nospeech|> token is higher than this value AND
        the decoding has failed due to `logprob_threshold`, consider the segment as silence
        (default: 0.6)
    ```
## 6. Languages
https://github.com/PINTO0309/whisper-onnx-tensorrt/blob/main/whisper/tokenizer.py

<details><summary>Languages List</summary><div>

```
LANGUAGES = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "iw": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
}
```

</div></details>

## 7. Benchmark
- Intel(R) Core(TM) i9-10900K CPU @ 3.70GHz
- [youtube](https://www.youtube.com/watch?v=P6UKhR0T6cs)
  ```
  python whisper/transcribe.py --audio carmack.mp3 --model tiny.en --beam_size 3
  ```
  |audio length|whisper onnx cpu|
  |:-:|:-:|
  |92 min|16.43 min|
  ```
  Hello, everybody
  we have a good crowd for John's second talk. It's very exciting. This is the first year that
  John will be talking twice. A couple things to know. John will talk for about an hour or so
  and then we'll have 30 minutes for questions. The mic is right there. That's actually just right there.
  And so just line up when we get to the questions. Try to keep your questions on what John talked about.
  If you get up and ask them and do them for us coming out, I'm going to kick you in the knee. So right there.
  So I will not waste any more time but you guys in the back because John's going to write
  in the board and we have plenty empty seats here. You can file in. Don't worry that there's
  reserved seats there. Just go ahead and sit in them. All right, I will give you guys Mr. Carmack.
  Okay, so I guess this is sort of going to be like a schoolroom session. I diluted myself for a little
  while that this would be the first talk where I ever actually made slides to present but it didn't
  actually come to pass. So it's going to be notes and talking and some scribbling on the board again.
  So almost all of what we do in game development is really more about artistry. It's about trying
  to appeal to people but there's the small section of the small section of what goes into the
  games that's drawing the pictures on the screen that you can at least make some ties to the
  you know the hardest of hard sciences and while you know it's great that people are
  researching the psychology in the different ways that people think about
    :
    :
  ```
  ```
  python whisper/transcribe.py --audio carmack.mp3 --model tiny.en --beam_size 2
  ```
  |audio length|whisper onnx cpu|
  |:-:|:-:|
  |92 min|11.61 min|
  ```
  Hello, everybody
  we have a good crowd for John's second talk. It's very exciting. This is the first year that
  John will be talking twice. A couple things to know. John will talk for about an hour or so
  and then we'll have 30 minutes for questions. The mic is right there. That's actually just right there.
  And so just line up when we get to the questions. Try to keep your questions on what John talked about.
  If you get up and ask Lynn Doom for us coming out, I'm going to kick you in the knee. So right there.
  So I will not waste any more time but you guys in the back because John's going to write
  in the board and we have plenty empty seats here. You can file in. Don't worry that there's
  reserved seats there. Just go ahead and sit in them. All right, I will give you guys Mr. Carmack.
  Okay, so I guess this is sort of going to be like a school room session. I diluted myself for a little
  while that this would be the first talk where I ever actually made slides to present but it didn't
  actually come to pass. So it's going to be notes and talking and some scribbling on the board again.
  So almost all of what we do in game development is really more about artistry. It's about trying
  to appeal to people but there's the small section of the small section of what goes into the
  games that's drawing the pictures on the screen that you can at least make some ties to the
  you know the hardest of hard sciences and while you know it's great that people are
  researching the psychology in the different ways that people think about
    :
    :
  ```
  ```
  python whisper/transcribe.py --audio carmack.mp3 --model tiny.en --beam_size 5
  ```
  |audio length|whisper onnx cpu|
  |:-:|:-:|
  |92 min|28.45 min|
  ```
  Hello, everybody
  we have a good crowd for John's second talk. It's very exciting. This is the first year that
  John will be talking twice. A couple things to know. John will talk for about an hour or so
  and then we'll have 30 minutes for questions. The mic is right there. That's actually just right there.
  And so just line up when we get to the questions. Try to keep your questions on what John talked about.
  If you get up and ask them and do them for us coming out, I'm going to kick you in the knee. So right there.
  So I will not waste any more time but you guys in the back because John's going to write
  in the board and we have plenty empty seats here. You can file in. Don't worry that there's
  reserved seats there. Just go ahead and sit in them. All right, I will give you guys Mr. Carmack.
  Okay, so I guess this is sort of going to be like a schoolroom session. I diluted myself for a little
  while that this would be the first talk where I ever actually made slides to present but it didn't
  actually come to pass. So it's going to be notes and talking and some scribbling on the board again.
  So almost all of what we do in game development is really more about artistry. It's about trying
  to appeal to people but there's the small section of the small section of what goes into the
  games that's drawing the pictures on the screen that you can at least make some ties to the
  you know the hardest of hard sciences and while you know it's great that people are
  researching the psychology in the different ways that people think about
    :
    :
  ```
  ```
  python whisper/transcribe.py --audio carmack.mp3 --model base.en --beam_size 3
  ```
  |audio length|whisper onnx cpu|
  |:-:|:-:|
  |92 min|40.51 min|
  ```
  Hello everybody.
  We have a good crowd for John's second talk.
  It's very exciting.
  This is the first year that John will be talking twice.
  A couple of things to know.
  John will talk for about an hour or so,
  and then we'll have 30 minutes for questions.
  The mic is right there.
  So just line up when we get to the questions.
  Try to keep your questions on what John talked about.
  If you get up and ask when Doom 4 is coming out,
  I'm going to kick you in the knee.
  So right there.
  So I will not waste any more time,
  but you guys in the back,
  because John's going to write in the board,
  and we have plenty empty seats here, you can file in.
  Don't worry that there's reserved seats there.
  Just go ahead and sit in them.
  Alright, I will give you guys Mr. Carmack.
  APPLAUSE
  OK, so I guess this is sort of going to be like a school room session.
  I deluded myself for a little while that this would be the first talk
  where I ever actually made slides to present,
  but it didn't actually come to pass,
  so it's going to be notes and talking and some scribbling on the board again.
  So almost all of what we do in game development
  is really more about artistry.
  It's about trying to appeal to people,
  but there's the small section of the small section of what goes into the game
  that's drawing the pictures on the screen
  that you can at least make some ties to the hardest of hard sciences.
  And while it's great that people are researching the psychology
    :
    :
  ```
  ```
  python whisper/transcribe.py --audio carmack.mp3 --model base.en --beam_size 2
  ```
  |audio length|whisper onnx cpu|
  |:-:|:-:|
  |92 min|27.68 min|
  ```
  Hello everybody.
  We have a good crowd for John's second talk.
  It's very exciting.
  This is the first year that John will be talking twice.
  A couple of things to know.
  John will talk for about an hour or so,
  and then we'll have 30 minutes for questions.
  The mic is right there.
  So just line up when we get to the questions.
  Try to keep your questions on what John talked about.
  If you get up and ask when Doom 4 is coming out,
  I'm going to kick you in the knee.
  So right there.
  So I will not waste any more time,
  but you guys in the back,
  because John's going to write in the board,
  and we have plenty empty seats here, you can file in.
  Don't worry that there's reserved seats there.
  Just go ahead and sit in them.
  Alright, I will give you guys Mr. Carmack.
  APPLAUSE
  OK, so I guess this is sort of going to be like a school room session.
  I deluded myself for a little while that this would be the first talk
  where I ever actually made slides to present,
  but it didn't actually come to pass,
  so it's going to be notes and talking and some scribbling on the board again.
  So almost all of what we do in game development
  is really more about artistry.
  It's about trying to appeal to people,
  but there's the small section of the small section of what goes into the game
  that's drawing the pictures on the screen
  that you can at least make some ties to the hardest of hard sciences.
  And while it's great that people are researching the psychology
    :
    :
  ```
