# Cisco Sample Code License 1.1
# flopach 2025

# ================== IMPORTS ==================
from smolagents.agents import CodeAgent, ToolCallingAgent, ManagedAgent
from smolagents import tool, LiteLLMModel, DuckDuckGoSearchTool

# ================== TELEMETRY ==================
from opentelemetry.sdk.trace import TracerProvider
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
endpoint = "http://0.0.0.0:6006/v1/traces"
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))
SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

# ================== DETERMINISTIC FUNCTIONS ==================
def get_last_logs(no_logs:int,host:str) -> str:
    """
    Returns the output of the provided show command from the device with the given host, username, password, and device type.

    Args:
        show_command: The show command to run on the device
        host: The IP address or hostname of the device
        device_type: The device type for the device

    Returns:
        str: Output of the provided show command
    """
    print("Getting the logs from the device...")

    from netmiko import ConnectHandler
    import json

    with open("hosts.json", 'r') as file:
        devices = json.load(file)
        username = devices[host]["username"]
        password = devices[host]["password"]

    device = {
        'ip': host,
        'username': username,
        'password': password,
        'device_type': "cisco_ios",
    }

    connection = ConnectHandler(**device)

    #returns the show command output
    log_output = connection.send_command("show logging last " + str(no_logs))
    lines = log_output.splitlines()
    last_lines = "\n".join(lines[-no_logs:])
    print(last_lines)

    return last_lines

def simulate_failed_ssh_login(host, username, password) -> None:
    """
    Returns the output of the provided show command from the device with the given host, username, password, and device type.

    Args:
        show_command: The show command to run on the device
        host: The IP address or hostname of the device
        device_type: The device type for the device

    Returns:
        str: Output of the provided show command
    """
    print("Trying to login via SSH...")

    import paramiko

    try:
        # Establish SSH connection attempt
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Attempt to connect with incorrect credentials
        ssh.connect(host, username=username, password=password, port=22)
        
    except paramiko.AuthenticationException:
        print("Failed SSH login attempt detected.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

# ================== AGENTS + MODELS ==================

# LLM model
model = LiteLLMModel(model_id="ollama/qwen2.5", #qwen2.5 #llama3.1
                     num_ctx=8192)

# Web Agent (= a managed agent)
# using the DuckDuckGo search tool
managed_web_agent = ManagedAgent(
    agent=ToolCallingAgent(tools=[DuckDuckGoSearchTool()],
                  model=model,
                  max_steps=2,
                 ),
    name="search",
    description="Runs web searches for you. Provide your query in the request argument.",
)

# Manager agent - manages the web agent
manager_agent = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[managed_web_agent],
    additional_authorized_imports=['ncclient', 'netmiko','requests','paramiko','io','subprocess'],
)

# ================== WORKFLOW ==================

host_ip = "10.10.20.48" # or use devnetsandboxiosxe.cisco.com

# 1. Simulate failed SSH login
simulate_failed_ssh_login(host_ip, "developer", "wrongpassword")

# 2. Get last 5 logs from the device
last_lines = get_last_logs(5, host_ip)

# 3. Run the agent
manager_agent.run(f"""Extract the error from the provided logs from the Cisco device below. Query the web-search tool about the error message in order to find a solution to the error. Return more information about the error and summarize the web-search output.
Received logs from the Cisco device: {last_lines}""")

# 4. Print the output or insert it into a ticketing system via REST API