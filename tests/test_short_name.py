from utils.short_name import sanitize_short_name, generate_unique_short_name


def test_sanitize_short_name():
    res = sanitize_short_name("Hello World!", bot_username="MyTestBot")
    assert res.endswith("_by_MyTestBot")
    assert " " not in res
    assert "!" not in res
    assert len(res) <= 64


def test_generate_unique_short_name():
    name1 = generate_unique_short_name("Cool Pack Title", bot_username="StickerBot")
    name2 = generate_unique_short_name("Cool Pack Title", bot_username="StickerBot")

    assert name1.endswith("_by_StickerBot")
    assert name2.endswith("_by_StickerBot")
    assert name1 != name2  # Guaranteed unique via UUID snippet
