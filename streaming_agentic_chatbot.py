import streamlit as st
import time
from typing import Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, HumanMessage


load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    history: Annotated[list, add_messages]


graph_builder = StateGraph(State)


tool = DuckDuckGoSearchRun()
tools = [tool]
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=300,
    max_retries=2,
)


llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    # Combine current messages with history
    all_messages = state["history"] + state["messages"]
    return {"messages": [llm_with_tools.invoke(all_messages)]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")




# Get the response for user queries
def get_response(user_input, chat_history, graph_builder=graph_builder):


    graph = graph_builder.compile()

    # Combine current messages with history
    events = graph.invoke(
        {"messages": chat_history + [("user", user_input)]}, stream_mode="values"
    )

    response_text = events["messages"][-1].content
    
    if not response_text:
        raise ValueError("No 'output_text' found in response")

    # Split the response into sentences or words.
    sentences = response_text.split(' ')
    
    # Yield each sentence as part of the generator
    for sentence in sentences:
        yield sentence + " "
        time.sleep(0.02)


def main():
    st.set_page_config(page_title="Agentic chatbot", page_icon="🤖")

    # Session State Management
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="Hello, how can I help you?")
        ]
 
    # Display chat history
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)

    if True:
        user_query = st.chat_input("Ask a question...")

        if user_query:
            st.session_state.chat_history.append(HumanMessage(content=user_query))

            with st.chat_message("Human"):
                st.markdown(user_query)

            with st.chat_message("AI"):
                response = st.write_stream(get_response(user_query, st.session_state.chat_history))
            st.session_state.chat_history.append(AIMessage(content=response))


    # Clear chat history button
    if st.button("Clear"):
        st.session_state.chat_history = [AIMessage(content="Hello, how can I help you?")]
        st.rerun()

if __name__ == "__main__":
    main()