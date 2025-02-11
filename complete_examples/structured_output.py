# Cisco Sample Code License 1.1
# flopach 2025

# ================== IMPORTS ==================
from ollama import chat
from pydantic import BaseModel

# ================== REQUEST DATA FROM DEVICE ==================
def run_ios_show_command_on_device_trusted(show_command:str,host:str) -> str:
    """
    Returns the output of the provided show command from the device with the given host, username, password, and device type.

    Args:
        show_command: The show command to run on the device
        host: The IP address or hostname of the device
        device_type: The device type for the device

    Returns:
        str: Output of the provided show command
    """
    print("Running show command on device...")

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
                                                                                                                                                                                
    # Establish connection to the device                                                                                                                                       
    connection = ConnectHandler(**device)

    if show_command.startswith("show") or show_command.startswith("sh"):
        # Execute command to retrieve running configuration                                                                                                                        
        running_config_output = connection.send_command(show_command)
        print(running_config_output)
        return running_config_output
    else:
        return "Error! You are only allowed to run show commands. Try again and use a show command."

if __name__ == "__main__":
    # ================== PYDANTIC DATA MODEL ==================
    class Cat8000(BaseModel):
        ios_version: str
        configuration_register: str

    # ================== OLLAMA LLM INTERACTION ==================

    # define your parameters
    ios_show_command = "show version"
    device_host = "10.10.20.48" # or "devnetsandboxiosxe.cisco.com"

    response = chat(
        messages=[
            {
            'role': 'system',
            'content': 'You are a helpful networking assistant.',
        },
        {
            'role': 'user',
            'content': f'''What can you say about my Cisco switch?
                        Here is the output of the "show version" command:
                        {run_ios_show_command_on_device_trusted(ios_show_command,device_host)}''',
        }
        ],
        model='llama3.1',
        format=Cat8000.model_json_schema(),
    )

    # ================== OUTPUT ==================

    cat8000_instance = Cat8000.model_validate_json(response.message.content)

    print("LLM response output according to your schema:")
    print(f"IOS Version: {cat8000_instance.ios_version}")
    print(f"Config Register: {cat8000_instance.configuration_register}")