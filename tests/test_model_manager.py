# coding: utf-8

import types
import sys

from bert.model_manager import ModelManager, _PlaceholderTopicModel


def test_model_manager_fallback_placeholder(monkeypatch):
    # Force import failure path
    def boom_import(name, *args, **kwargs):
        if name in ("bertopic", "bertopic.representation", "sentence_transformers"):
            raise ImportError("nope")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", boom_import)
    ModelManager._model = None
    ModelManager.initialize_model()
    assert isinstance(ModelManager.get_model(), _PlaceholderTopicModel)


def test_model_manager_success_initialization(monkeypatch):
    # Fake external modules and simulate successful model construction
    class FakeBERTopic:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeKeyBERTInspired:
        pass

    class FakeSentenceTransformer:
        def __init__(self, name):
            self.name = name

    fake_bertopic = types.ModuleType("bertopic")
    fake_bertopic.BERTopic = FakeBERTopic
    fake_repr = types.ModuleType("bertopic.representation")
    fake_repr.KeyBERTInspired = FakeKeyBERTInspired
    fake_st = types.ModuleType("sentence_transformers")
    fake_st.SentenceTransformer = FakeSentenceTransformer

    sys.modules["bertopic"] = fake_bertopic
    sys.modules["bertopic.representation"] = fake_repr
    sys.modules["sentence_transformers"] = fake_st

    ModelManager._model = None
    ModelManager.initialize_model()
    model = ModelManager.get_model()
    assert isinstance(model, FakeBERTopic)
    assert model.kwargs["verbose"] is False
