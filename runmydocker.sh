BROKER=fyers FLASK_PORT=5005 WEBSOCKET_PORT=8765 docker compose -p fyers-app up --build -d
BROKER=fivepaisa FLASK_PORT=5006 WEBSOCKET_PORT=8766 docker compose -p fivepaisa-app up --build -d
BROKER=kotak FLASK_PORT=5007 WEBSOCKET_PORT=8767 docker compose -p kotak-app up --build -d
