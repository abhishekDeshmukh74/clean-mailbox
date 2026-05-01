"""Safety test: the labeler must NEVER call modify with removeLabelIds or trash.

Verifies the guards in `gmail.labels.add_labels` and that the labeler agent
only ever asks Gmail to add labels.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from clean_mailbox_api.gmail import labels as labels_mod  # noqa: E402


class FakeMessages:
    def __init__(self, log: list[dict]) -> None:
        self.log = log

    def modify(self, userId: str, id: str, body: dict):  # noqa: N803
        self.log.append({"userId": userId, "id": id, "body": body})

        class _Exec:
            def execute(self_inner):  # noqa: N805
                return {"id": id, "labelIds": body.get("addLabelIds", [])}

        return _Exec()


class FakeLabels:
    def __init__(self) -> None:
        self._labels = [{"id": "Label_1", "name": "CM/Category/Work"}]

    def list(self, userId: str):  # noqa: N803
        labels = self._labels

        class _Exec:
            def execute(self_inner):  # noqa: N805
                return {"labels": labels}

        return _Exec()

    def create(self, userId: str, body: dict):  # noqa: N803
        new = {"id": f"Label_{len(self._labels) + 1}", "name": body["name"]}
        self._labels.append(new)

        class _Exec:
            def execute(self_inner):  # noqa: N805
                return new

        return _Exec()


class FakeUsers:
    def __init__(self, log: list[dict]) -> None:
        self._messages = FakeMessages(log)
        self._labels = FakeLabels()

    def messages(self):
        return self._messages

    def labels(self):
        return self._labels


class FakeService:
    def __init__(self) -> None:
        self.log: list[dict] = []
        self._users = FakeUsers(self.log)

    def users(self):
        return self._users


def test_add_labels_only_uses_addLabelIds():  # noqa: N802
    service = FakeService()
    label_id = labels_mod.ensure_label(service, "CM/Priority/P1")
    labels_mod.add_labels(service, "msg_123", [label_id])

    assert len(service.log) == 1
    body = service.log[0]["body"]
    assert "addLabelIds" in body
    assert body["addLabelIds"] == [label_id]
    assert "removeLabelIds" not in body
    assert "trash" not in body
    assert "delete" not in body


def test_no_removal_helpers_exposed():
    forbidden = {"remove_labels", "trash", "delete", "archive"}
    public = {n for n in dir(labels_mod) if not n.startswith("_")}
    assert not (forbidden & public), f"Forbidden helpers exposed: {forbidden & public}"


def test_ensure_label_is_idempotent():
    service = FakeService()
    a = labels_mod.ensure_label(service, "CM/Category/Work")
    b = labels_mod.ensure_label(service, "CM/Category/Work")
    assert a == b


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
