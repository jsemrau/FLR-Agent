import openai
import os, re
from typing import Dict, Union, Any, List
from langchain import LLMChain
from langchain.agents import AgentExecutor,AgentOutputParser,ZeroShotAgent
from langchain.agents import load_tools , initialize_agent

from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks import StreamlitCallbackHandler

from langchain.schema import AgentAction, AgentFinish
import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)

import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from uuid import UUID


# Initialize Langchain components

#******  Custom   *********
class _OutputParser(AgentOutputParser):

    def parse_text_to_json(self,input_text):
    # Split the input text based on ": " and "\n"
        segments = input_text.strip().split('\n')
        data = {}
        error={}
        try:
            for segment in segments:
                key, value = segment.split(": ", 1)  # Split at the first occurrence of ": "
                data[key] = value
        except Exception as e:
            error={'Error': f"Segment: {segment} , Error: {str(e)}"}

        # Create the desired JSON structure
        json_data = {
            "Question": data.get("Question", ""),
            "Thought": data.get("Thought", ""),
            "Action": data.get("Action", ""),
            "Action Input": data.get("Action Input", ""),
            "Error" : error,
        }

        return json_data

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        
        print(f" **** DEBUG **** {llm_output} ****")
        #json_data={'output':self.parse_text_to_json(llm_output)}
        action_match=None 
        final_match=None
        thought_match=None
        question_match=None 

        thought_substring=""
        action_substring=""
        question_substring=""
        final_substring=""

        pattern_thought = "Thought:(.*?)(?=\\n)"
        thought_match = re.search(pattern_thought, llm_output)

        if thought_match:
            thought_substring = thought_match.group(1)
            print("Substring between 'Thought:' and '\\n':", thought_substring)

        pattern_action = "Action:(.*?)(?=\\n)"
        action_match = re.search(pattern_action, llm_output)

        if action_match:
            action_substring = action_match.group(1)
            print("Substring between 'Action:' and '\\n':", action_substring)

        pattern_question = "Question:(.*?)(?=\\n)"
        question_match = re.search(pattern_question, llm_output)

        if question_match:
            question_substring = question_match.group(1)
            print("Substring between 'Question:' and '\\n':", question_substring)

        pattern_final = "Final Answer:(.*?)(?=\\n)"
        final_match = re.search(pattern_final, llm_output)

        if final_match:
            final_substring = final_match.group(1)
            print("Substring between 'Question:' and '\\n':", final_substring)


        #if "Final Answer:" in llm_output:
        if final_match:
            print("Final - Agent should finish")
            logger.debug(llm_output)
            #st.markdown(llm_output.split("Final Answer:")[-1].strip())
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                #return_values={"output":llm_output.split("Final Answer:")[-1].strip()},
                return_values={"output":final_substring},
                log=llm_output,
                )
        
        if question_match:
        #if "Question:" in llm_output:
            print("Agent should finish - Question")
            logger.debug(llm_output)
            #t.markdown(llm_output.split("Question:")[-1].strip())
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                #return_values={"output": llm_output.split("Question:")[-1].strip()},
                return_values={"output":question_substring},
                log=llm_output,
            )
        
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:

            print("Parsing Action Input")
            logger.debug(llm_output)
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                #return_values={"output":llm_output.split("Action Input:")[-1].strip()},
                return_values={"output":question_substring},
                log=llm_output,
            )
            # raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)

        #This can't be agent finish because otherwise the agent stops working.
        print(" Not finished yet")
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
#******  Agent   *********

class Agent():

    def get_input(self) -> str:
        print(f" Inside input function ")
        has_feedback=False
        feedback=st.chat_message(" Please reply")
        
        return feedback

    def __init__(self, candidate_name:str, position_name:str,openai_api_key:str ) -> None:

        model_version="gpt-3.5-turbo"
        #model_version="gpt-4"
        
        openai.api_key=openai_api_key
        self.candidate_name=candidate_name
        self.position_name=position_name

        self.agent_name="Lisa"
        self.company_name="Google" #whitelabel

        self.output_parser = _OutputParser()

        self.llm = ChatOpenAI(temperature=0, model_name=model_version, streaming=True)
        self.tools = load_tools(["human", "serpapi", "llm-math"], llm=self.llm)

        fmt_instructions= """Output the following json format: [{'Thought':'string','Question':'string','Action':'string','Action Input':'string', 
        Final Answer: 'string'}] """

        prefix = f"You are a Front Line Recruiter at {self.company_name} named {self.agent_name}.\
                    You are hiring for the role of {self.position_name}. \
                    Roleplay a job interview with the candidate.\
                    Ask appropriate questions. \
                    You have access to the following tools:"
                    
        suffix = """{chat_history}
                    Input: {input}
                    {agent_scratchpad}"""


        self.prompt = ZeroShotAgent.create_prompt(
            self.tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad"],
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        #,returnMessages=True, input_key='input', output_key="output")

        llm_chain = LLMChain(llm=self.llm, prompt=self.prompt)
        brain=ZeroShotAgent(llm_chain=llm_chain,
                            tools=self.tools,
                            verbose=True, 
                            return_intermediate_steps=True,
                            output_parser=self.output_parser,
                            )

        self.agent= AgentExecutor.from_agent_and_tools(agent=brain, 
                                    tools=self.tools, 
                                    verbose=True, 
                                    memory=self.memory,
                                    )


        
    def get_agent_response(self,prompt_text):
        
        callback_handler=StreamingStdOutCallbackHandler()
        response = self.agent({"input": prompt_text},callbacks=[callback_handler] ,return_only_outputs=True)
        return response

    def ask(self,input: str) -> str:

        #callback_handler = StreamlitCallbackHandler(st.container())
        callback_handler=StreamingStdOutCallbackHandler()
        
        try:
            response = self.agent({"input": input},callbacks=[callback_handler],return_only_outputs=True)
        except Exception as e:
            response = str(e)
            if response.startswith("Could not parse LLM output: `"):
                response = response.removeprefix("Could not parse LLM output: `").removesuffix("`")
                return response
            else:
                raise Exception(str(e))
          