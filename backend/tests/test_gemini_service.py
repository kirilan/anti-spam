"""Tests for the Gemini service"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini_service import GeminiService, GeminiServiceError, list_gemini_models


class TestGeminiServiceClassify:
    """Tests for classify_thread method"""

    @pytest.fixture
    def service(self):
        return GeminiService(api_key="test-api-key", model="gemini-1.5-flash")

    def test_classify_thread_success(self, service: GeminiService):
        """Test successful classification"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"model": "gemini-1.5-flash", "responses": [{"response_id": "123", "response_type": "confirmation", "confidence_score": 0.95, "rationale": "Clear deletion confirmation"}]}'
                            }
                        ]
                    }
                }
            ]
        }

        with patch("app.services.gemini_service.requests.post", return_value=mock_response):
            result = service.classify_thread(
                {"request_id": "req-1", "responses": [{"id": "123", "body": "Your data has been deleted."}]}
            )

        assert result["model"] == "gemini-1.5-flash"
        assert len(result["responses"]) == 1
        assert result["responses"][0]["response_type"] == "confirmation"
        assert result["responses"][0]["confidence_score"] == 0.95

    def test_classify_thread_api_error(self, service: GeminiService):
        """Test handling API error"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.gemini_service.requests.post", return_value=mock_response):
            with pytest.raises(GeminiServiceError, match="Gemini API error 500"):
                service.classify_thread({"request_id": "req-1", "responses": []})

    def test_classify_thread_invalid_response_structure(self, service: GeminiService):
        """Test handling unexpected response structure"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"invalid": "structure"}

        with patch("app.services.gemini_service.requests.post", return_value=mock_response):
            with pytest.raises(GeminiServiceError, match="unexpected response"):
                service.classify_thread({"request_id": "req-1", "responses": []})

    def test_classify_thread_strips_markdown(self, service: GeminiService):
        """Test that markdown code blocks are stripped from response"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '```json\n{"model": "gemini-1.5-flash", "responses": []}\n```'
                            }
                        ]
                    }
                }
            ]
        }

        with patch("app.services.gemini_service.requests.post", return_value=mock_response):
            result = service.classify_thread({"request_id": "req-1", "responses": []})

        assert result["model"] == "gemini-1.5-flash"


class TestGeminiServiceExtractJson:
    """Tests for _extract_json method"""

    @pytest.fixture
    def service(self):
        return GeminiService(api_key="test-api-key", model="gemini-1.5-flash")

    def test_extract_json_clean(self, service: GeminiService):
        """Test extracting clean JSON"""
        result = service._extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_extract_json_with_markdown(self, service: GeminiService):
        """Test extracting JSON from markdown code block"""
        result = service._extract_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_extract_json_with_surrounding_text(self, service: GeminiService):
        """Test extracting JSON with surrounding text"""
        result = service._extract_json('Here is the result: {"key": "value"} That was the JSON.')
        assert result == {"key": "value"}

    def test_extract_json_invalid(self, service: GeminiService):
        """Test handling invalid JSON"""
        with pytest.raises(GeminiServiceError, match="did not contain valid JSON"):
            service._extract_json("not json at all")

    def test_extract_json_empty(self, service: GeminiService):
        """Test handling empty input"""
        with pytest.raises(GeminiServiceError, match="did not contain valid JSON"):
            service._extract_json("")


class TestGeminiServiceBuildPrompt:
    """Tests for _build_prompt method"""

    @pytest.fixture
    def service(self):
        return GeminiService(api_key="test-api-key", model="gemini-1.5-flash")

    def test_build_prompt_contains_model(self, service: GeminiService):
        """Test that prompt contains model name"""
        prompt = service._build_prompt({"request_id": "123", "responses": []})
        assert "gemini-1.5-flash" in prompt

    def test_build_prompt_contains_response_types(self, service: GeminiService):
        """Test that prompt contains all response types"""
        prompt = service._build_prompt({"request_id": "123", "responses": []})
        assert "confirmation" in prompt
        assert "rejection" in prompt
        assert "acknowledgment" in prompt
        assert "action_required" in prompt
        assert "request_info" in prompt
        assert "unknown" in prompt

    def test_build_prompt_includes_thread_data(self, service: GeminiService):
        """Test that prompt includes thread data as JSON"""
        thread_data = {"request_id": "my-request-123", "responses": [{"body": "Test response"}]}
        prompt = service._build_prompt(thread_data)
        assert "my-request-123" in prompt
        assert "Test response" in prompt


class TestListGeminiModels:
    """Tests for list_gemini_models function"""

    def test_list_models_success(self):
        """Test successful model listing"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-1.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-1.5-pro",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/embedding-001",
                    "supportedGenerationMethods": ["embedContent"],
                },
            ]
        }

        with patch("app.services.gemini_service.requests.get", return_value=mock_response):
            models = list_gemini_models("test-api-key")

        assert "gemini-1.5-flash" in models
        assert "gemini-1.5-pro" in models
        assert "embedding-001" not in models  # Doesn't support generateContent

    def test_list_models_api_error(self):
        """Test handling API error"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("app.services.gemini_service.requests.get", return_value=mock_response):
            with pytest.raises(GeminiServiceError, match="Gemini API error 401"):
                list_gemini_models("invalid-api-key")

    def test_list_models_empty_response(self):
        """Test handling empty models response"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"models": []}

        with patch("app.services.gemini_service.requests.get", return_value=mock_response):
            models = list_gemini_models("test-api-key")

        assert models == []

    def test_list_models_deduplicates(self):
        """Test that duplicate models are deduplicated"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-1.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-1.5-flash",  # Duplicate
                    "supportedGenerationMethods": ["generateContent"],
                },
            ]
        }

        with patch("app.services.gemini_service.requests.get", return_value=mock_response):
            models = list_gemini_models("test-api-key")

        assert models.count("gemini-1.5-flash") == 1
