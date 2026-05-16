from ingest import sanitize_text


def test_sanitize_text_masks_id_card_phone_and_amount() -> None:
    raw_text = "张三身份证 110105199001011234，手机号 13800138000，行权价 12,345元，授予金额 88.5万元。"

    sanitized = sanitize_text(raw_text)

    assert "110105199001011234" not in sanitized
    assert "13800138000" not in sanitized
    assert "12,345元" not in sanitized
    assert "88.5万元" not in sanitized
    assert "【脱敏身份证】" in sanitized
    assert "【脱敏手机号】" in sanitized
    assert sanitized.count("【脱敏金额】") == 2


def test_sanitize_text_keeps_non_sensitive_content() -> None:
    raw_text = "员工期权分四年成熟，第一年 cliff 后成熟 25%。"

    sanitized = sanitize_text(raw_text)

    assert sanitized == raw_text
