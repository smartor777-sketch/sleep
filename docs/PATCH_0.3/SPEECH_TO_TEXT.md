# Create transcription

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/audio/transcriptions:
    post:
      summary: Create transcription
      deprecated: false
      description: >-
        The `audio/transcriptions` interface is used to transcribe audio into
        the input language.  

        You can view the official documentation
        [here](https://platform.openai.com/docs/api-reference/audio/createTranscription)
        to learn more.
      tags:
        - 🔊 Audio Models
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: true
          example: Bearer {{api-key}}
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  format: binary
                  type: string
                  description: >-
                    The audio file object (not file name) to transcribe, in one
                    of these formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav,
                    or webm.
                  example: ''
                model:
                  description: >-
                    ID of the model to use. Only whisper-1 (which is powered by
                    our open source Whisper V2 model) is currently available.
                  example: whisper-1
                  type: string
                prompt:
                  description: >-
                    An optional text to guide the model's style or continue a
                    previous audio segment. The prompt should match the audio
                    language.
                  example: eiusmod nulla
                  type: string
                response_format:
                  description: >-
                    The format of the output, in one of these options: json,
                    text, srt, verbose_json, or vtt.
                  example: json
                  type: string
                temperature:
                  description: >-
                    The sampling temperature, between 0 and 1. Higher values
                    like 0.8 will make the output more random, while lower
                    values like 0.2 will make it more focused and deterministic.
                    If set to 0, the model will use log probability to
                    automatically increase the temperature until certain
                    thresholds are hit.
                  example: '0'
                  type: string
                language:
                  description: >-
                    The language of the input audio. Supplying the input
                    language in ISO-639-1 format will improve accuracy and
                    latency.
                  example: ''
                  type: string
              required:
                - file
                - model
            examples: {}
      responses:
        '200':
          description: ''
          content:
            '*/*':
              schema:
                type: object
                properties:
                  text:
                    type: string
                required:
                  - text
                x-apidog-orders:
                  - text
          headers: {}
          x-apidog-name: Successful Response
      security: []
      x-apidog-folder: 🔊 Audio Models
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/810968/apis/api-13851476-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://api.cometapi.com
    description: Prod Env
security: []

```