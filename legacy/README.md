# Legacy prototype reference

These six files were moved unchanged from the repository root on 30 September
2026. They are not the Gather backend and are not maintained runnable examples.

| File | Reference value |
| --- | --- |
| main1.py | Original PyQt document library, format extraction and chat experiment. |
| main.py | Original document processing, local model and indexing experiment. |
| chroma.py | Original Chroma embedding/search experiment. |
| code_reader.py | Original agent file-reading tool. |
| prompts.py | Original agent prompts. |
| requirements.txt | Historical dependency snapshot, not current installation instructions. |

Do not run or import these modules against personal documents. Some execute work
at import time and use paths relative to the working directory. Their imports
and paths have deliberately not been adapted to the new application.

Current app: ../apps/desktop. Current processing: ../services/worker.
The current worker tests use Python's standard library; do not install the old
dependency snapshot to run them. Historical docs refer to the original root paths.
