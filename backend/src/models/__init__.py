from .message import Conversations, Participant, SearchParameters
from .models import CustomSystemMessage, LlmCall, Project
from .settings import get_settings

# All models to instantiate on load
__beanie_models__ = [SearchParameters,Participant, Conversations, Project, LlmCall, CustomSystemMessage]
