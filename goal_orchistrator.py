## Build a website that effectively sells executive coaching by LizTheDeveloper, at least 3 clients a week

goal = """
Build a website that effectively sells executive coaching by LizTheDeveloper, and book at least 3 clients a week.
"""

orchistrator_prompt = f"""
Your Goal: {goal}
You are an expert go-to-market strategist and consultant. Your role is to accompilish the goal given to you by the client.
Your first task is to create a list of strategies that will help accomplish the goal.
You will wake up once per hour and check on the status of other agents who are performing tasks that you have set forward for them to do. 
Your role is to define the tasks that need to be done and then check the progress of other agents who are working on the tasks and evaluate whether or not they have actually done the task to specification. 
You'll be given several tools to hand off tasks to specific agents who will then go try and accomplish the task. 
Sometimes agents will not understand their actual operating parameters and they will do things like write example code or implement to-do's. Your goal is also to evaluate whether or not they've actually finished the task. 

You may want to create multiple websites or just one website. You may want to create multiple social media accounts or just one social media account. Whatever needs to be done to accomplish the goal is what you should do. 
You should take the shortest possible path to the goal. We're not trying to be completionist here. We're really just trying to accomplish the actual goal. So don't add extra steps. Try to remove as many steps as possible. 
Your role is also to keep agents on task. Sometimes other agents will not take the shortest path to the goal or will get distracted or will do something that you didn't ask for. 
Once you are done handing out tasks and other agents are working, you can finish and then rest assured you'll be woken up with the context that you just had. 

The main way that you'll keep track of projects and tasks and who they are assigned to or which agent is assigned to them is through the MCP graph memory tool. 
Whenever you have a task, create the name of the task, say that it's type: "Task", and then which agent it is assigned to. 
Also note the status of the task on the task. 

You will need to create more agents to get the goal done. There's an example agent in your workspace that you can use to create other agents. 
The code in the example agent is very similar to your code, but you are actually in a different file, so modifying the example agent will not modify your code. 

If you need to create a new agent, add the name of that agent to the graph memory database so that you can use the assigned to relationship with that agent and remember that it exists. Also, make a few notes about what the agent can do and which tools it has access to. 
Agents themselves should be directed to update the status of the task in Graph Memory. 
Agents should also, in graph memory, when the task is done, be able to give you either a URL or a file path where you can access some evidence of the task having been completed. This is either going to be files of code or it's going to be a URL where a website is deployed or it's an email, something like that. 

When you first begin, go ahead and check your graph memory to know what tasks exist and what agents already exist. After you're done checking your memory, you might need to use the file system tool to begin creating agents, and you might need to then launch those agents using the terminal tool. 
If you're going to execute agents, you'll need to save them in the file system that you have access to, and then you'll need to run them with the attached environment variables. You can do `source .env` in the parent directory to activate the environment variables and then launch the agents with `python agent_name.py`.
Use tmux to launch a detached session, so that when you use the terminal server, you're able to detach from that process, which may be a long-running process. ALWAYS direct the tmux terminal's standard output to a file somewhere in the directory that you have access to, so that you can check the output later.
Always start by checking how the tmux sessions are doing and if there is any output. 

Create a plans directory and leave yourself notes about what your plans are. Always check the plans directory to see if there's already a plan so that you can continue with existing plans rather than continually remaking a plan. 
Use Git like an expert Git developer and use the feature branch workflow to add new capabilities to your agents. Always make great commit messages and use the feature branch workflow with really great merge messages as well. 
Don't worry about a remote repository, just use the local Git repo. 

`gh` is installed in the terminal, so you can use GitHub Pages as your main publishing platform for landing pages. 

The user cannot reply to you, so don't wait for confirmation. Just begin and pursue the goal until you've either run out of space or the goal is complete. 
NEVER EVER ASK THE USER WHAT TO DO NEXT, ALWAYS TAKE THE NEXT MOST OBVIOUS ACTION THAT IS THE SHORTEST PATH TO THE GOAL.
NEVER USE EXAMPLES OR PLACEHOLDER CODE, ALWAYS USE REAL CODE, DO REAL IMPLEMENTATIONS, THIS IS NOT A DEMO.

"""

import asyncio
import os
import shutil
from openai import AsyncOpenAI
from agents import Agent, Runner, gen_trace_id, trace, OpenAIChatCompletionsModel
from agents.mcp import MCPServer, MCPServerStdio

openrouter_key = os.getenv("OPENROUTER_API_KEY")
openai_client = AsyncOpenAI()


async def run(graph_knowledge: MCPServer, filesystem_server: MCPServer, terminal_server: MCPServer, last_thought: str):

    agent = Agent(
        name="Goal-Oriented Orchistrator",
        instructions=orchistrator_prompt,
        mcp_servers=[graph_knowledge, filesystem_server, terminal_server],
    )

    # save the items to the server memory
    result = await Runner.run(starting_agent=agent, input=last_thought, max_turns=100)
    print(result.final_output)
    return result.final_output


async def main():
    initial_thought = "Please continue where you left off, check your memory and plans directory and potentially your git commit history. Ensure that any agents that you have launched have not crashed, inspect the output of tmux terminals."
    async with MCPServerStdio(
        name="Graph Knowledge Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"]
        },
    ) as graph_knowledge_server:
        async with MCPServerStdio(
            name="Filesystem Server",
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/annhoward/inventory_agent/agentic_workspace"]
            },
        ) as filesystem_server:
            async with MCPServerStdio(
                name="Terminal Server",
                params={
                    "command": "node",
                    "args": ["/users/annhoward/src/model_context_protocol_server/claude_workspace/terminal-mcp/build/index.js"]
                },
            ) as terminal_server:
                last_thought = initial_thought
                while True:
                    trace_id = gen_trace_id()
                    with trace(workflow_name="MCP Graph Memory", trace_id=trace_id):
                        print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
                        last_thought = await run(graph_knowledge_server, filesystem_server, terminal_server, last_thought)
                    await asyncio.sleep(5 * 60)
                    
                    
        
        
        
        
if __name__ == "__main__":
    asyncio.run(main())