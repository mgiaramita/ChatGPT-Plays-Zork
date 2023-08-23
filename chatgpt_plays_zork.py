import argparse
import configparser
import openai
import os
import pexpect
import time


MODEL = "gpt-3.5-turbo"
EXIT_STR = "EXIT"


PROC_READ_MAX = 1000000
PROC_READ_TIMEOUT = 5
PROC_RSP_WAIT = 1.5


LOGO = """
   ____ _           _    ____ ____ _____ 
  / ___| |__   __ _| |_ / ___|  _ \_   _|
 | |   | '_ \ / _` | __| |  _| |_) || |  
 | |___| | | | (_| | |_| |_| |  __/ | |  
  \____|_| |_|\__,_|\__|\____|_|    |_|  
 |  _ \| | __ _ _   _ ___                
 | |_) | |/ _` | | | / __|               
 |  __/| | (_| | |_| \__ \               
 |_|   |_|\__,_|\__, |___/               
  ________  ____|___/__                  
 |__  / _ \|  _ \| |/ /                  
   / / | | | |_) | ' /                   
  / /| |_| |  _ <| . \                   
 /____\___/|_| \_\_|\_\                  
                                         
"""

tokens_input = 0
tokens_output = 0


def print_tokens():
    print(f"Tokens In: {tokens_input}, Tokens Out: {tokens_output}\n")


def gen_chat_rsp(message, message_history, role="user", model=MODEL):
    global tokens_input, tokens_output

    # Generate response to message + history
    message_history.append({"role": role, "content": f"{message}"})
    try:
        completion = openai.ChatCompletion.create(model=model, messages=message_history)
        reply = completion.choices[0].message.content

        # Keep track of usage ($$$)
        tokens_input = completion.usage.prompt_tokens
        tokens_output = completion.usage.completion_tokens
    except Exception as e:
        # Response failed, give default (error) response
        reply = "An Error occurred. Please try again."

    # Update message history
    message_history.append({"role": "assistant", "content": f"{reply}"})

    return reply


def chatgpt_zork_loop(command, model):
    message_history = [
        {
            "role": "user",
            "content": "You are playing the classic text adventure game Zork. I will provide you with the output from the game and you will respond with the move you would like to make. Your output should be in the format of valid Zork game commands. Try to make progress through the map and beat the game. ONLY answer the prompts like someone playing the computer game Zork, do not use full sentences, do not apologize for misunderstandings, only use vaild Zork game commands to communicate. Use the command LOOK if you get stuck and need to know what the current room is. If you get stuck on a door or lock or anything try N, E, S, or W to go somewhere else. Say OK if you understand.",
        },
        {"role": "assistant", "content": "OK"},
    ]

    zork_proc = pexpect.spawn(command)
    print("ChatGPT and Zork are ready to begin.")

    while True:
        # Allow user to moderate
        userin = input("\nUSER: Type EXIT to stop. Enter to continue.\n> ")
        if userin == EXIT_STR:
            break

        # Ensure Zork has responded and then read all the current output
        time.sleep(PROC_RSP_WAIT)
        zork_output = zork_proc.read_nonblocking(
            size=PROC_READ_MAX, timeout=PROC_READ_TIMEOUT
        ).decode("utf-8")
        print(f"\n{zork_output}")

        # Send Zork prompt to ChatGPT
        rsp = gen_chat_rsp(zork_output, message_history, model=model)
        print(f"> {rsp}")
        print_tokens()

        # Send ChatGPT generated command to Zork
        zork_proc.sendline(rsp)

    zork_proc.terminate(force=True)


def main():
    # Load dev key, init openai
    config = configparser.ConfigParser()
    config.read("config.ini")
    openai.api_key = config["DEFAULT"]["API_KEY"]

    # Set up and read command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default=MODEL)
    args = parser.parse_args()
    print(f"M: {args.model}")

    print(LOGO)
    chatgpt_zork_loop(config["DEFAULT"]["CMD"], args.model)


if __name__ == "__main__":
    main()
