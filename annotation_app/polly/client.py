"""Amazon Polly クライアントラッパー."""

from __future__ import annotations

import boto3
from tenacity import retry, stop_after_attempt, wait_exponential

from annotation_app.polly.ssml import prosody_to_ssml


class PollyClient:
    """Amazon Polly を使って音声合成するクライアント."""

    def __init__(self, region_name: str = "ap-northeast-1") -> None:
        self._client = boto3.client("polly", region_name=region_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def synthesize(
        self,
        prosody_kana: str,
        prosody_pattern: str,
        voice_id: str = "Mizuki",
    ) -> bytes:
        """prosody フィールドから MP3 音声バイト列を生成する."""
        ssml = prosody_to_ssml(prosody_kana, prosody_pattern)
        response = self._client.synthesize_speech(
            Engine="standard",
            LanguageCode="ja-JP",
            OutputFormat="mp3",
            Text=ssml,
            TextType="ssml",
            VoiceId=voice_id,
        )
        return response["AudioStream"].read()  # type: ignore[no-any-return]
