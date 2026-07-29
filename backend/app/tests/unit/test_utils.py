from app.utils import sanitize_json_response


class TestSanitizeJsonResponse:
    def test_clean_json(self):
        text = '{"supermarket": "Test", "items": []}'
        assert sanitize_json_response(text) == text

    def test_markdown_code_block(self):
        text = '{"key": "value"}'
        wrapped = f"```json\n{text}\n```"
        assert sanitize_json_response(wrapped) == text

    def test_markdown_code_block_no_language(self):
        text = '{"key": "value"}'
        wrapped = f"```\n{text}\n```"
        assert sanitize_json_response(wrapped) == text

    def test_extra_text_before_and_after(self):
        text = '{"key": "value"}'
        dirty = f"Some text before\n{text}\nSome text after"
        assert sanitize_json_response(dirty) == text

    def test_markdown_with_extra_text(self):
        text = '{"key": "value"}'
        dirty = f"Here is the result:\n```json\n{text}\n```\nEnd of response"
        assert sanitize_json_response(dirty) == text

    def test_json_with_nested_braces(self):
        text = '{"a": {"b": ["c", "d"]}, "e": 1}'
        assert sanitize_json_response(text) == text

    def test_empty_braces(self):
        assert sanitize_json_response("{}") == "{}"

    def test_no_json_returns_original_text(self):
        assert sanitize_json_response("no braces here") == "no braces here"

    def test_json_with_trailing_garbage(self):
        result = sanitize_json_response('{"offers": []} extra_content_here')
        assert result == '{"offers": []}'

    def test_multiple_json_objects_returns_first_only(self):
        text1 = '{"a": 1}'
        text2 = '{"b": 2}'
        result = sanitize_json_response(f"{text1}\n{text2}")
        assert result == text1
