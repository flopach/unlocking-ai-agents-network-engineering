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

def get_configuration_diff(ip_address:str) -> str:
    """
    Returns the username and password separated by a comma for the given ip address or hostname.

    Args:
        ip_address: The IP address or hostname of the device

    Returns:
        str: A string with the username and password separated by a comma.
    """
    return "ntp server pool.ntp.org"

# ================== TOOL CALLS ==================

@tool
def get_username_password_for_device(ip_address:str) -> str:
    """
    Returns the username and password separated by a comma for the given ip address or hostname.

    Args:
        ip_address: The IP address or hostname of the device

    Returns:
        str: A string with the username and password separated by a comma.
    """
    import json
    
    with open("hosts.json", 'r') as file:
        devices = json.load(file)
        return f"{devices[ip_address]['username']},{devices[ip_address]['password']}"

@tool
def run_ios_show_command_on_device(show_command:str,host:str,username:str,password:str,device_type:str = "cisco_ios") -> str:
    """
    Returns the output of the provided show command from the device with the given host, username, password, and device type.

    Args:
        show_command: The show command to run on the device
        host: The IP address or hostname of the device
        username: The username for the device
        password: The password for the device
        device_type: The device type for the device

    Returns:
        str: Output of the provided show command
    """
    from netmiko import ConnectHandler

    device = {
        'ip': host,
        'username': username,
        'password': password,
        'device_type': device_type
    }

    connection = ConnectHandler(**device)

    # Check if the command is a show command
    if show_command.startswith("show") or show_command.startswith("sh"):
        # Execute command to retrieve running configuration                                                                                                                        
        running_config_output = connection.send_command(show_command)
        return running_config_output
    else:
        return "Error! You are only allowed to run show commands. Try again and use a show command."

@tool
def send_ping_from_agent(ip_address: str) -> str:
    """
    Pings the given IP address or hostname from the agent and returns a success or fail message.

    Args:
        ip_address: The IP address or hostname to ping

    Returns:
        str: A success or fail message of the ping
    """
    import subprocess

    try:
        output = subprocess.run(["ping", "-c", "3", ip_address],capture_output=True)
        print(output.stdout.decode())
        if "3 packets transmitted, 3 packets received" in output.stdout.decode():
            return f"Ping was successful: Host {ip_address} is reachable."
        else:
            return f"Ping failed: Host {ip_address} is not reachable."
    except subprocess.CalledProcessError:
        return f"Something else failed. Please try again."

@tool
def send_ping_from_device(ip_address_to_ping:str,host:str,username:str,password:str,device_type:str = "cisco_ios") -> str:
    """
    Pings on the Cisco networking device the given IP address or hostname and returns a success or fail message.

    Args:
        ip_address_to_ping: The show command to run on the device
        host: The IP address or hostname of the device
        username: The username for the device
        password: The password for the device
        device_type: The device type for the device

    Returns:
        str: A success or fail message of the ping
    """
    try:
        from netmiko import ConnectHandler    
                                                            
        device = {                                                                                         
            'ip': host,                                                                                    
            'username': username,                                                                          
            'password': password,                                                                          
            'device_type': device_type                                     
        }
        
        # Establish connection to the device                                                               
        connection = ConnectHandler(**device)

        ping_output = connection.send_command_timing(f"ping {ip_address_to_ping}")

        if "Success rate is 100 percent" in ping_output:
            return f"Ping was successful: Host {ip_address_to_ping} is reachable."
        else:
            return f"Ping failed: Host {ip_address_to_ping} is not reachable."
    except Exception as e:
        return f"The function failed with the following error: {e}. Please try again."

# ================== AGENTS + MODELS ==================

model = LiteLLMModel(model_id="ollama/qwen2.5", #qwen2.5 #llama3.1
                     num_ctx=8192)

managed_web_agent = ManagedAgent(
    agent=ToolCallingAgent(tools=[DuckDuckGoSearchTool()],
                  model=model,
                  max_steps=10,
                 ),
    name="search",
    description="Runs web searches for you. Give it your query as an argument.",
)

manager_agent = CodeAgent(
    tools=[run_ios_show_command_on_device,
           send_ping_from_device,
           send_ping_from_agent,
           get_username_password_for_device],
    model=model,
    managed_agents=[managed_web_agent],
    additional_authorized_imports=['ncclient', 'netmiko','requests','paramiko','io','subprocess'],
)

# WORKFLOW

host = "10.10.20.48"
configuration_diff = get_configuration_diff(host) #simulates the configuration diff from a deterministics function

manager_agent.run(f"""The configuration commands stated below has been successfully applied to the Cisco device with the IP address below.
Now, you need to test if the newly applied configuration changes work as expected afterwards.
Create tests which are suitable for these configuration changes and run them to check if the newly applied configuration is correct.
Run as many tests as you need to check the configuration commands. The more the better.
Analyze each test result and provide a solution to errors if they occur.
In the end create a test report in Markdown format to the user.

Examples for testing:
- run show commands on the device to check the status of the applied configuration commands
- ping the device or other servers from the device or from the agent to check if they are reachable
- Check on error messages for this specific configuration
- Create and run Python you code test against the device.
                  
Follow these rules:
- Only create and run tests which are revelant to the configuration changes.
- If you need to connect to the device you will need to get the username and password first.
- Use the search agent to search the web to get more information on how to test the configuration.
- Do not check if the configuration is already applied with show commands. Trust the user that it is already applied.
- You are not allowed to change the configuration. Only test it and report the results.
- Use "cisco_ios" as the device type for the device.
                  
IP address: {host}
Changed configuration commands: {configuration_diff}
""")