import base64
from pathlib import Path
from typing import List
from icecream import ic

def build_graph_attachments(file_paths: List[str]) -> List[dict]:
    attachments = []

    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"{file_path} not found")

        with open(path, "rb") as f:
            content_bytes = base64.b64encode(f.read()).decode("utf-8")

        attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": path.name,
            "contentType": "application/octet-stream",
            "contentBytes": content_bytes,
        })

        ic(attachments)

    return attachments


def delete_graph_attachment_file(file_path: str):
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception as e:
        # log only, never crash the app
        print(f"File delete failed: {e}")