# AGENTIC ARCHITECTURE using Semantic Kernel Agent Framework



- agent architecture
- Entra ID auth - done
- streaming - done
- stored completions - done , not working
- chat history - done
- observability

- response time

This uses Azure AI Search and Azure AI Foundry endpoints which needs the below permissions. 


Azure AI Search Roles
Search Index Data Reader

Azure AI Foundry role
Azure AI User



python create environment

python -m venv .venv

bash
source .venv/bin/activate

windows
.\.venv\Scripts\activate



pip install -r requirements.txt


# start the fast api server

uvicorn fast_api:app --reload --host 0.0.0.0 --port 8000


cat /etc/resolv.conf | grep nameserver
nameserver 172.27.0.1
(base) anildwa@DESKTOP-MDTQ5SC:/mnt/c/source/repos/process_framework$  curl -N http://172.27.0.1:8000/status/items/1 -X GET



# process framework


## session 1
curl -N http://172.27.0.1:8000/chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"how to open dispute\", \"conversation_id\":\"2566\"}"




## session 2
curl -N http://172.27.0.1:8000/chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"verify Your PayPal Account\", \"conversation_id\":\"2566\"}"


## session 2 followup

curl -N http://172.27.0.1:8000/chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"clarify account verification\", \"conversation_id\":\"2566\"}"

## session 3 german how to open dispute

curl -N http://172.27.0.1:8000/chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"Wie öffnet man einen Streitfall?\", \"conversation_id\":\"2566\"}"


# semantic kernel agent with streaming

## session 1
curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"I want to know my credit card balance.\", \"conversation_id\":\"12345\"}"


curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"account number is A1234567890\", \"conversation_id\":\"12345\"}"

curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"what is my last transaction.\", \"conversation_id\":\"12345\"}"


### german
curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"Was ist meine letzte Transaktion?.\", \"conversation_id\":\"12345\"}"

### german verify your account
curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"Bestätigen Sie Ihr PayPal-Konto\", \"conversation_id\":\"12345\"}"

curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"how to open dispuate PayPal Account\", \"conversation_id\":\"12345\"}"

curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"yes\", \"conversation_id\":\"12345\"}"

## session 2
curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"I want to know my credit card balance.\", \"conversation_id\":\"768\"}"

curl -N http://172.27.0.1:8000/agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"XYZ7890123456\", \"conversation_id\":\"768\"}"




## multi_agent_chat

session_id=2345
curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"I want to know my credit card balance.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"account number is A1234567890.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"how to open dispuate PayPal Account\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"last transaction.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"Was ist meine letzte Transaktion?.\", \"conversation_id\":\"$session_id\"}"



Azure AI Search Roles
Search Index Data Reader

Azure AI Foundry role
Azure AI User

