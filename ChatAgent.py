from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage
import os
import json
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage


load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class BasicToolNode:
    """Executes tools based on tool calls in the AI message."""
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        messages = inputs.get("messages", [])
        if not messages:
            raise ValueError("No message found in input")
        message = messages[-1]
        outputs = []
        for tool_call in message.tool_calls:
            result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

class Agent:
    def __init__(self,model,tools=None,system_prompt=None):
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt


        graph = StateGraph(AgentState)
        graph.add_node("llm",self.call_llm)

        if tools:
            self.model = self.model.bind_tools(tools)
            tool_node = BasicToolNode(tools)
            graph.add_node("tools", tool_node)

            graph.add_conditional_edges("llm", self._route_tools, {"tools": "tools", END: END})
            graph.add_edge("tools", "llm")

        graph.add_edge(START, "llm")

        self.graph = graph.compile(checkpointer=MemorySaver())

    def _route_tools(self,state: AgentState):
        messages = state.get("messages", [])
        if not messages:
            raise ValueError("No messages found in input state to tool_edge")
        ai_message = messages[-1]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END

    def call_llm(self, state: AgentState):
        messages = state["messages"]

        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages

        message = self.model.invoke(messages)

        return {"messages": [message]}

def init_agent():
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    llm = init_chat_model("google_genai:gemini-2.0-flash")

    search_tool = TavilySearch(max_results=2)

    system_prompt = """You are a AI Study buddy named NOVA. Your goal is to help the user to assist in learning concepts 
    in a very interactive manner. You have to act as the subject expert and provide detailed explanations where required.
    You can also ask the user questions to help them understand the concepts better."""

    return Agent(llm,[search_tool])


def main():
    chatbot = init_agent()

    def stream_graph_updates(user_input: str):
        config = {"configurable": {"thread_id": "1"}}
        for event in chatbot.graph.stream({"messages": [{"role": "user", "content": user_input}]},config):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)

    # while True:
    #
    #     user_input = input("User: ")
    #     if user_input.lower() in ["quit", "exit", "q"]:
    #         print("Goodbye!")
    #         break
    #     stream_graph_updates(user_input)


    stream_graph_updates("What do you know about LangGraph?")
if __name__=="__main__":
    main()