import tempfile


def test_upload_document_preserves_original_filename_in_list(
    client, auth_headers, monkeypatch
):
    from app.config import settings
    from app.services.rag_service import RAGService

    tmp_dir = tempfile.mkdtemp(prefix="uploads_")
    monkeypatch.setattr(settings.file_storage, "upload_dir", tmp_dir, raising=False)

    async def _noop(self, document_id: int) -> None:
        return None

    monkeypatch.setattr(RAGService, "_process_document_background", _noop, raising=True)

    kb_resp = client.post(
        "/api/v1/knowledge-bases",
        headers=auth_headers,
        json={"name": "kb", "description": "d", "category": ""},
    )
    assert kb_resp.status_code == 201
    kb_id = kb_resp.json()["id"]

    filename = "文档一.docx"
    upload_resp = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        params={"knowledge_base_id": kb_id},
        files={
            "file": (
                filename,
                b"hello",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload_resp.status_code == 201
    assert upload_resp.json()["filename"] == filename

    list_resp = client.get(
        "/api/v1/documents",
        headers=auth_headers,
        params={"knowledge_base_id": kb_id, "skip": 0, "limit": 20},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["filename"] == filename

