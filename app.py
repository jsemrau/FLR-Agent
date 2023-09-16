import streamlit as st
import os, re
from typing import Dict, Union, Any, List
from agent import Agent
import time, json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from uuid import UUID

st.title="Interview Helper"

openai_api_key = st.sidebar.text_input('OpenAI API Key')
candidate_name = st.sidebar.text_area('Your name:', 'Please enter your name')
company_name = st.sidebar.text_area('Company:', 'Please enter the company you are applying for')
position_name = st.sidebar.text_area('Position:', 'Please enter the position you are applying for')

#******  Secrets   *********
os.environ["OPENAI_API_KEY"] =st.secrets["OPENAI_API_KEY"]
os.environ["SERPAPI_API_KEY"] = st.secrets["SERPAPI_API_KEY"]

agent=Agent(candidate_name, position_name, openai_api_key)

candidate_name="John"
agent_name="Lisa"
position_name="Credit Risk Officer"
company_name="JP Morgan"
model_version="gpt-3.5-turbo"
#model_version="gpt-4"


st.session_state.human_feedback=False

#******************* EXPLORE ************

#if st.button("Start Interview"):  
    
st.write(f"Interview with {candidate_name}:")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = model_version

if "messages" not in st.session_state:
    st.session_state.messages = []
    prt=f"Hi, {candidate_name}, nice to meet you. My name is {agent_name}. \
        Thank you for coming here today for interviewing for the role of {position_name}\
        at {company_name}.\
        Please tell me about yourself"
    st.session_state.messages.append({"role": "assistant", "content": prt})
    st.chat_message("assistant").markdown(prt)

else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

#if len(st.session_state.messages)==0:
#    print(" No Messages. Let's start the Interview")

if prompt := st.chat_input("Please input your feedback to the questions here"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    
    response={}
    with st.chat_message("assistant"):
        
        full_response = ""
        response=agent.get_agent_response(prompt)
        #print("RESPONSE"+ json.dumps(response))
        t=""
        q=""
        if 'Question' in response:
            
            q=response['output']
            st.markdown(q)

        else:
            st.markdown(response['output'])

        if 'Thought' in response:
            print(" Thought in Response")
            t=response['output']
            print(f" THOUGHT-> {t}")


    st.session_state.messages.append({"role": "assistant", "content": response['output']})
            