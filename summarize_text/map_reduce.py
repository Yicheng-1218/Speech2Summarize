from langchain import hub
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import dotenv
import os

map_prompt = hub.pull("rlm/map-prompt")

dotenv.load_dotenv(override=True)
llm = ChatAnthropic(model=os.getenv("ANTHROPIC_LLM_MODEL"), temperature=0.3)

map_chain = map_prompt | llm | StrOutputParser()

