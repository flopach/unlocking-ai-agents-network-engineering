from typing import Optional
from smolagents.agents import CodeAgent, ToolCallingAgent, ManagedAgent
from smolagents import tool, LiteLLMModel
import json

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

endpoint = "http://0.0.0.0:6006/v1/traces"
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))

SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)

model = LiteLLMModel(model_id="ollama/qwen2.5", #qwen2.5 #llama3.1 #command-r7b
                     num_ctx=8192,              
                    )

@tool
def get_username_password_for_device(ip_address:str) -> str:
    """
    Returns the username and password separated by a comma for the given ip address or hostname.

    Args:
        ip_address: The IP address or hostname of the device

    Returns:
        str: A string with the username and password separated by a comma.
    """
    with open("hosts.json", 'r') as file:
        devices = json.load(file)
        return f"{devices[ip_address]['username']},{devices[ip_address]['password']}"

@tool
def get_running_configuration(host:str,username:str,password:str,device_type:str = "cisco_ios",) -> str:
    """
    Returns the running configuration from the device with the given host, username, password, and device type.

    Args:
        host: The IP address or hostname of the device
        username: The username for the device
        password: The password for the device
        device_type: The device type for the device

    Returns:
        str: The running configuration of the device.
    """
    from netmiko import ConnectHandler    
                                                                                                          
    device = {                                                                                                                                                                 
        'ip': host,                                                                                                                                                   
        'username': username,                                                                                                                                                  
        'password': password,                                                                                                                                                  
        'device_type': device_type                                                                                        
    }                                                                                                                                                                          
                                                                                                                                                                                
    # Establish connection to the device                                                                                                                                       
    connection = ConnectHandler(**device)                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                
    # Execute command to retrieve running configuration                                                                                                                        
    running_config_output = connection.send_command('show running-config')                                                                                                     
                                                                                                                                                                                
    return running_config_output

agent = CodeAgent(tools=[get_username_password_for_device,get_running_configuration],
                  model=model,
                  additional_authorized_imports=['ncclient', 'netmiko','requests','paramiko'],         
                 )

agent.run("""
          Return the running configuration of the device with the IP address below.
          You will at first need the username and password for the device.

          ip-address: 10.10.20.48
          """)
