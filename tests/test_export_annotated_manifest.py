from pathlib import Path

from scripts.export_annotated_manifest import default_output_path


class TestDefaultOutputPath:
    def test_adds_timestamped_suffix_before_extension(self) -> None:
        output = default_output_path("data/pair_manifest.jsonl")

        assert output.startswith("data/pair_manifest.annotated.")
        assert output.endswith(".jsonl")

    def test_handles_paths_without_extension(self) -> None:
        output = default_output_path("data/pair_manifest")

        assert Path(output).name.startswith("pair_manifest.annotated.")
        assert output.endswith(".jsonl")