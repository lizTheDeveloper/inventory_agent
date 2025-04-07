import asyncio
import os
import shutil
from openai import AsyncOpenAI
from agents import Agent, Runner, gen_trace_id, trace, OpenAIChatCompletionsModel
from agents.mcp import MCPServer, MCPServerStdio

from inventory import upload_images_to_openai, capture_frames_from_stream, get_camera_frame
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openai_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)


async def run(mcp_server: MCPServer):
    frames = capture_frames_from_stream()
    frame = get_camera_frame()  
    items_extracted = upload_images_to_openai([],[frame],"Please make a list of all objects in the image capture.")
    agent = Agent(
        name="Assistant",
        instructions="Given the list of items in this room, save them to your server memory using your available tools, along with their relationship to where they are. Please check the server to find existing, similar objects before you create them, so we don't end up with duplicates. If you see an object you've seen before, but there is new info, update the observations on the object.",
        mcp_servers=[mcp_server],
        model=OpenAIChatCompletionsModel(model='openrouter/auto', openai_client=openai_client)
    )

    # save the items to the server memory
    result = await Runner.run(starting_agent=agent, input=items_extracted, max_turns=50)
    print(result.final_output)


async def main():

    async with MCPServerStdio(
        name="Graph Knowledge Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"]
        },
    ) as server:
        # trace_id = gen_trace_id()
        # with trace(workflow_name="MCP Graph Memory", trace_id=trace_id):
        #     print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
        await run(server)


if __name__ == "__main__":
    # Let's make sure the user has npx installed
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")

    asyncio.run(main())