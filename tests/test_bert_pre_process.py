# coding: utf-8

from bert.pre_process import extract_text_segments, preprocess_documents


def test_extract_text_segments_nested_structures_and_model_dump():
    class Obj:
        def model_dump(self):
            return {"k": ["hello", {"m": "world"}]}

    data = {
        "a": ["one", {"b": ["two", Obj()]}],
        "c": "three",
    }
    texts = extract_text_segments(data)
    assert set(texts) == {"one", "two", "three", "hello", "world"}


def test_preprocess_documents_filters_stopwords_and_punct():
    docs = ["The API, and its tokens... are GREAT!!!", "123 numbers & symbols"]
    processed = preprocess_documents(docs)
    # 'the' and 'and' filtered; letters only of len>=3, lowercased
    assert processed[0].split()[0] == "api"
    assert processed[1] == "numbers symbols" or processed[1] == "numbers"
