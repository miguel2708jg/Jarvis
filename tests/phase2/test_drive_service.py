"""Unit tests for the Google Drive service adapter."""
import pytest

from backend.services import drive_service


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeFiles:
    def __init__(self):
        self.calls = []
        self.file = {
            "id": "file-1",
            "name": "Plan.txt",
            "mimeType": "text/plain",
            "webViewLink": "https://drive.google.com/file-1",
            "createdTime": "2035-01-01T00:00:00Z",
            "modifiedTime": "2035-01-02T00:00:00Z",
            "parents": ["root"],
        }

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return FakeRequest({"files": [self.file]})

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return FakeRequest(self.file)

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        body = kwargs["body"]
        return FakeRequest({**self.file, "name": body["name"], "mimeType": body["mimeType"], "parents": body.get("parents", [])})


class FakeDriveService:
    def __init__(self):
        self.files_resource = FakeFiles()

    def files(self):
        return self.files_resource


def test_search_drive_files(monkeypatch):
    fake = FakeDriveService()
    monkeypatch.setattr(drive_service, "_service", lambda: fake)

    files = drive_service.search_drive_files("Plan", max_results=5)

    assert files[0]["id"] == "file-1"
    assert files[0]["mime_type"] == "text/plain"
    _, call = fake.files_resource.calls[0]
    assert "name contains 'Plan'" in call["q"]
    assert call["pageSize"] == 5


def test_get_drive_file_metadata_only(monkeypatch):
    fake = FakeDriveService()
    monkeypatch.setattr(drive_service, "_service", lambda: fake)

    file = drive_service.get_drive_file("file-1", include_content=False)

    assert file["name"] == "Plan.txt"
    assert "content" not in file


def test_create_drive_text_file_and_folder(monkeypatch):
    fake = FakeDriveService()
    monkeypatch.setattr(drive_service, "_service", lambda: fake)

    text_file = drive_service.create_drive_text_file("Notes.txt", "hello", parent_id="folder-1")
    folder = drive_service.create_drive_folder("Projects")

    assert text_file["name"] == "Notes.txt"
    assert text_file["parents"] == ["folder-1"]
    assert folder["mime_type"] == drive_service.FOLDER_MIME_TYPE
    assert [name for name, _ in fake.files_resource.calls] == ["create", "create"]


def test_drive_rejects_empty_query():
    with pytest.raises(drive_service.DriveValidationError):
        drive_service.search_drive_files(" ")
