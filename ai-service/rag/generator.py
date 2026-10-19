from llm.openai_client import get_model, get_client
from llm.prompts import SAFETY_PROMPT
from llm.response_parser import GroundedAnswer
from llm.safety import UNSAFE_OUTPUT, HINDI_UNSAFE_OUTPUT
from rag.citation_manager import evidence_sources
from rag.prompt_builder import build_prompt
from extraction.lab_parser import numeric_tokens

INSUFFICIENT = 'The retrieved evidence is insufficient to answer this part of your question.'

def generate_answer(question: str, retrieved_documents) -> dict:
    sources = evidence_sources(retrieved_documents)
    if not sources:
        return {'answer':'I could not find relevant evidence in your reports or the medical knowledge base. Upload a report or ask about information in an indexed source.', 'sources':[], 'sections':{'from_report':INSUFFICIENT,'general_information':INSUFFICIENT}}
    response = get_client().responses.parse(model=get_model(), instructions=SAFETY_PROMPT, input=build_prompt(question,sources), text_format=GroundedAnswer)
    parsed = response.output_parsed
    if parsed is None: raise ValueError('The model did not return a validated answer')
    result = GroundedAnswer.model_validate(parsed)
    by_id = {source['id']:source for source in sources}
    used = set()
    sections = {}
    for field, kind in [('from_report','personal'),('general_information','knowledge')]:
        claims = getattr(result,field)
        lines = []
        for claim in claims:
            if any(id not in by_id or by_id[id]['kind'] != kind for id in claim.source_ids):
                raise ValueError('The answer cited an invalid or mismatched source')
            evidence_numbers=set(number for source_id in claim.source_ids for number in numeric_tokens(by_id[source_id]['snippet']))
            if any(number not in evidence_numbers for number in numeric_tokens(claim.text)):
                raise ValueError('The answer included an unsupported numeric value')
            if UNSAFE_OUTPUT.search(claim.text) or HINDI_UNSAFE_OUTPUT.search(claim.text): raise ValueError('The answer did not pass safety validation')
            used.update(claim.source_ids)
            lines.append(claim.text + ' ' + ' '.join(f'[{id}]' for id in claim.source_ids))
        sections[field] = '\n'.join(lines) if lines else INSUFFICIENT
    answer = f"From your report\n{sections['from_report']}\n\nGeneral medical information\n{sections['general_information']}\n\nDiscuss your results with a qualified healthcare professional."
    return {'answer':answer,'sections':sections,'sources':[source for source in sources if source['id'] in used], 'urgent':False}
