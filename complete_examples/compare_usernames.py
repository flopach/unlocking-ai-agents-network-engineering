# Cisco Sample Code License 1.1
# flopach 2025

# ================== IMPORTS ==================
from smolagents.agents import CodeAgent, ToolCallingAgent, ManagedAgent
from smolagents import tool, LiteLLMModel

# ================== TELEMETRY ==================
from opentelemetry.sdk.trace import TracerProvider
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
endpoint = "http://0.0.0.0:6006/v1/traces"
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))
SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

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
def get_all_users_cisco_device(host: str, username: str, password: str) -> str:
    """
    Returns the configuration of the users from the Cisco device.

    Args:
        host: The IP address or hostname of the device
        username: The username for the device
        password: The password for the device

    Returns:
        str: The configuration of the users.
    """
    from ncclient import manager
    import xmltodict

    with manager.connect(
        host=host,
        port=830,
        username=username,
        password=password,
        hostkey_verify=False
    ) as m:
        filter = '''
            <filter xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                    <username/>
                </native>
            </filter>
        '''
        netconf_reply = m.get_config(source='running', filter=filter)
        netconf_data = xmltodict.parse(netconf_reply.xml)
        return netconf_data["rpc-reply"]["data"]["native"]["username"]

# ================== AGENTS + MODELS ==================

model = LiteLLMModel(model_id="ollama/qwen2.5", #qwen2.5 #llama3.1
                     num_ctx=8192)

device_agent = CodeAgent(tools=[get_username_password_for_device,
                         get_all_users_cisco_device],
                  model=model,
                  additional_authorized_imports=['ncclient', 'netmiko','requests','paramiko','io'],
                 )
# give the sandboxed Python interpreter access to read/write files outside (use with caution!)
device_agent.python_executor.static_tools["open"] = open 

# ================== TASKS ==================

# Compare Usernames
device_agent.run("""
                 Compare the usernames which are configured on the Cisco device 10.10.20.48 against the host devnetsandboxiosxe.cisco.com.
                 You will at first need the username and password for each devices.
                 """)