"""Entry point: python -m agent"""

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from agent.config import load_config

config = load_config()
uvicorn.run(
    "agent.server.app:app",
    host=config.server.host,
    port=config.server.port,
    reload=True,
    log_level=config.logging.level.lower(),
)
