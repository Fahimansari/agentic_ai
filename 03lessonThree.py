from dotenv import load_dotenv
import os
from tavily import TavilyClient
import json
from pygments import highlight, lexers, formatters

_ = load_dotenv()

city = "San Francisco"

query = f"""
    what is the current weather in {city}?
    Should I travel there today?
    "weather.com"
"""

client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


result = client.search(query, 
                       max_results=5)


data =result["results"][0]["content"]


parsed_json = json.loads(data.replace("'", '"'))

formatted_json = json.dumps(parsed_json, indent=4)

colorful_json = highlight(formatted_json, 
                          lexers.JsonLexer(),
                          formatters.TerminalFormatter())

print(colorful_json)