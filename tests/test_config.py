from app.config import Settings

def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram-key")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "test_dermtrack")

    settings = Settings(_env_file=None)

    assert settings.groq_api_key == "test-groq-key"
    assert settings.google_api_key == "test-google-key"
    assert settings.deepgram_api_key == "test-deepgram-key"
    assert settings.mongodb_uri == "mongodb://localhost:27017"
    assert settings.mongodb_database == "test_dermtrack"

def test_settings_use_safe_defaults(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram-key")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "test_dermtrack")

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.store_media_files is False
    assert settings.gemini_model == "gemini-2.5-flash"

def test_settings_reject_missing_required_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram-key")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "test_dermtrack")

    try:
        Settings(_env_file=None)
    except Exception as error:
        assert "groq_api_key" in str(error)
    else:
        raise AssertionError("Settings should reject a missing GROQ_API_KEY")