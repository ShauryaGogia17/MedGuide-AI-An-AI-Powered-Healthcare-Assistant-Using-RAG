"""Public AI failure descriptions; never return raw provider exception messages."""
from dataclasses import dataclass

from openai import (
    APIConnectionError, APIError, APIStatusError, APITimeoutError,
    AuthenticationError, BadRequestError, NotFoundError,
    PermissionDeniedError, RateLimitError,
)


class AIConfigurationError(RuntimeError):
    def __init__(self, code='ai_not_configured'):
        self.code = code
        super().__init__('AI provider configuration is incomplete')


@dataclass(frozen=True)
class AIFailure:
    code: str
    message: str
    status: int = 503

    def detail(self):
        return {'code': self.code, 'message': self.message}


FAILURES = {
    'ai_not_configured': AIFailure('ai_not_configured', 'Add OPENAI_API_KEY to the project .env to enable report processing and answers.'),
    'ai_model_not_configured': AIFailure('ai_model_not_configured', 'Set OPENAI_MODEL and OPENAI_EMBEDDING_MODEL in the project .env.'),
    'ai_invalid_key': AIFailure('ai_invalid_key', 'The OpenAI API key was rejected. Update OPENAI_API_KEY in the project .env.'),
    'ai_permission_denied': AIFailure('ai_permission_denied', 'This OpenAI key does not have permission for the requested model. Check the key permissions and model settings.'),
    'ai_quota_exceeded': AIFailure('ai_quota_exceeded', 'This OpenAI account has no available API quota. Add API billing credits or use a key with available quota.'),
    'ai_rate_limited': AIFailure('ai_rate_limited', 'OpenAI is temporarily limiting requests. Wait a moment and try again.', 429),
    'ai_model_unavailable': AIFailure('ai_model_unavailable', 'The configured OpenAI model is unavailable for this key. Check OPENAI_MODEL and OPENAI_EMBEDDING_MODEL in the project .env.'),
    'ai_timeout': AIFailure('ai_timeout', 'OpenAI took too long to respond. Please try again.', 504),
    'ai_unavailable': AIFailure('ai_unavailable', 'The AI service could not be reached. Check the services and internet connection, then try again.'),
    'ai_request_rejected': AIFailure('ai_request_rejected', 'OpenAI could not process this request. Check the model settings or try again.', 502),
}


def provider_failure(error):
    """Classify only known configuration/provider failures, without exposing their body."""
    if isinstance(error, AIConfigurationError):
        return FAILURES.get(error.code, FAILURES['ai_not_configured'])
    if isinstance(error, APITimeoutError):
        return FAILURES['ai_timeout']
    if isinstance(error, AuthenticationError):
        return FAILURES['ai_invalid_key']
    if isinstance(error, PermissionDeniedError):
        return FAILURES['ai_permission_denied']
    if isinstance(error, RateLimitError):
        code = getattr(error, 'code', None)
        return FAILURES['ai_quota_exceeded' if code in {'insufficient_quota', 'billing_hard_limit_reached', 'billing_not_active'} else 'ai_rate_limited']
    if isinstance(error, NotFoundError) or getattr(error, 'code', None) == 'model_not_found':
        return FAILURES['ai_model_unavailable']
    if isinstance(error, APIConnectionError):
        return FAILURES['ai_unavailable']
    if isinstance(error, APIStatusError) and error.status_code >= 500:
        return FAILURES['ai_unavailable']
    if isinstance(error, (BadRequestError, APIError)):
        return FAILURES['ai_request_rejected']
    return None
