from openai.types.responses import ResponseTextDeltaEvent

async def handle_stream_events(result):
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            # # raw text generations of model
            # print(event.data.delta, end="", flush=True)
            pass
        elif event.type == "agent_updated_stream_event":
            print("-- Agent Updated.")
            print(event.new_agent.name)
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool Called.")
                print(f"Tool name: {event.item.raw_item.name}")
                print(f"Arguments: {event.item.raw_item.arguments}")
            elif event.item.type == "tool_call_output_item":
                # # raw tool call outputs
                # print("-- Tool Output:")
                # print(event.item.output)
                pass
            elif event.item.type == "message_output_item":
                pass
            else:
                pass  # Ignore other event types