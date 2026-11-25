FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# mcp_pipe 会连到 MCP_ENDPOINT，并拉起本地 stdio 服务
CMD ["python3", "mcp_pipe.py", "music_mcp_server.py"]
