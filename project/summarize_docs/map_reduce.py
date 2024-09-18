from langchain import hub
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv(override=True)


map_prompt = hub.pull("rlm/map-prompt")
llm = ChatAnthropic(model=os.getenv("ANTHROPIC_LLM_MODEL"), temperature=0.3)

map_chain = map_prompt | llm | StrOutputParser()

