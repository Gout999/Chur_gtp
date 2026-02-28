from memory.shared import SharedMemoryClient


def test_memory_write_and_read() -> None:
    memory = SharedMemoryClient()

    memory.write(namespace="test", key="test-key", value={"data": "test"})
    result = memory.read("test", "test-key")

    assert result is not None
    assert result["value"]["data"] == "test"
