from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
import dotenv
import requests

dotenv.load_dotenv(override=True)

# 資策會維基百科、機器學習維基百科
web_pages=["https://zh.wikipedia.org/wiki/%E8%B3%87%E8%A8%8A%E5%B7%A5%E6%A5%AD%E7%AD%96%E9%80%B2%E6%9C%83",'https://zh.wikipedia.org/wiki/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0']
loader = WebBaseLoader(web_pages)
docs = loader.load()

def token_counter(text) -> int:
    """Count tokens in text using Meteron API

    Args:
        text (str): text to count tokens

    Returns:
        int: token count
    """
    return requests.post('https://app.meteron.ai/api/tokens',text).json()['tokens']

for i in docs:
    print('Docs token:',token_counter(i.page_content))


# GPT-4o-mini
# Our affordable and intelligent small model for fast, lightweight tasks. 
# GPT-4o mini is cheaper and more capable than GPT-3.5 Turbo. 
# Currently points to gpt-4o-mini-2024-07-18.

# Context Window : 128,000 tokens , Output Max tokens : 16,384
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.3)

prompt = ChatPromptTemplate.from_messages([("system", "Please write a summary for each document and respond in Traditional Chinese.\n\n{context}")])

chain = create_stuff_documents_chain(llm,prompt)

result = chain.invoke({"context": docs})
print(result)