from datetime import datetime

from src.models.message import Conversations, MessageDocument, SearchParameters


async def get_param(session_id: str):
    return await SearchParameters.find_many(
        {"session_id": session_id}, sort=[("timestamp", 1)]
    ).to_list()

# Helper function to create a new message document for an image
def create_image(content: str):
    return MessageDocument(
        content=content,
        role="user",
        timestamp=str(datetime.now()),
        type='image',
        content_type="image_url",
    )

# Helper function to create a new message document
async def create_message(
    content: str,
    role: str,
):
    return MessageDocument(
        content=content,
        role=role,
        timestamp=str(datetime.now()),
        type="text",
    )
