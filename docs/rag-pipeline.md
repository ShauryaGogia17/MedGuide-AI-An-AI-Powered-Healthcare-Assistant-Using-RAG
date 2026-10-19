# RAG pipeline

PDF pages retain their original numbering. Pages without selectable text are OCRed locally. Chunks use 800 characters with 100-character overlap, independently per page. Embeddings are requested in batches of at most 64 inputs.

Personal IDs contain `user_id:report_id:chunk_index`. Metadata includes user, report, filename, page, report date, chunk index, evidence category, and extraction method. An existing user/report ID is not embedded again. Knowledge source fingerprints include file contents and attribution metadata; unchanged sources are skipped by the explicit ingestion command.

Personal retrieval filters on the authenticated user before querying. Knowledge retrieval uses a separate collection. Each side contributes at most five passages, with a conservative cosine-distance cutoff to avoid clearly unrelated matches. The cutoff is an engineering heuristic rather than proof of relevance.

The LLM returns separate personal and general claim arrays through a strict Pydantic schema. Every claim cites supplied evidence IDs from the corresponding category. Invalid citations and numeric values absent from the cited snippets reject the answer. Returned sources include the exact retrieved passages. Instructions in report text and questions are explicitly treated as untrusted data.

When there is no evidence, no generation call is made. Emergency and diagnosis/prescription/dosage request rules run before retrieval. These guards and grounding checks reduce unsupported responses but cannot establish clinical correctness; users must review source passages and consult a qualified professional.
