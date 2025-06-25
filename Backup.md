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


rename and update .env.example to .env and provide the values for the  variables


prequisites:


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


testing


## multi_agent_chat

session_id=2345
curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"I want to know my credit card balance.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"account number is A1234567890.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"how to open dispuate PayPal Account\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"last transaction.\", \"conversation_id\":\"$session_id\"}"

curl -N http://172.27.0.1:8000/multi_agent_chat/ -X POST -H "Content-Type: application/json" -d "{\"user_message\":\"Was ist meine letzte Transaktion?.\", \"conversation_id\":\"$session_id\"}"