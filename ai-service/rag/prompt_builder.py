import json

def build_prompt(question, sources):
    return json.dumps({'question':question, 'retrieved_evidence':sources},ensure_ascii=False)
