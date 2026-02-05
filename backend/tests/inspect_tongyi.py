from langchain_community.llms import Tongyi
import inspect

print("Has _stream:", hasattr(Tongyi, "_stream"))
print("Has _astream:", hasattr(Tongyi, "_astream"))
print("Has _generate:", hasattr(Tongyi, "_generate"))
print("Has _agenerate:", hasattr(Tongyi, "_agenerate"))
print("Has _call:", hasattr(Tongyi, "_call"))
print("Has _acall:", hasattr(Tongyi, "_acall"))
