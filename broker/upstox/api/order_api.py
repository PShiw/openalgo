import http.client
import json
import os
from database.auth_db import get_auth_token
from database.token_db import get_token
from mapping.transform_data import transform_data , map_product_type, reverse_map_product_type, transform_modify_order_data



def get_api_response(endpoint, method="GET", payload=''):
    login_username = os.getenv('LOGIN_USERNAME')
    AUTH_TOKEN = get_auth_token(login_username)
    api_key = os.getenv('BROKER_API_KEY')

    conn = http.client.HTTPSConnection("api.upstox.com")
    headers = {
      'Authorization': f'Bearer {AUTH_TOKEN}',
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
    conn.request(method, endpoint, payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def get_order_book():
    return get_api_response("/v2/order/retrieve-all")

def get_trade_book():
    return get_api_response("/v2/order/trades/get-trades-for-day")

def get_positions():
    return get_api_response("/v2/portfolio/short-term-positions")

def get_holdings():
    return get_api_response("/v2/portfolio/long-term-holdings")

def get_open_position(tradingsymbol, exchange, product):
    positions_data = get_positions()
    net_qty = '0'

    if positions_data and positions_data.get('status') and positions_data.get('data'):
        for position in positions_data['data']:
            if position.get('tradingsymbol') == tradingsymbol and position.get('exchange') == exchange and position.get('product') == product:
                net_qty = position.get('quantity', '0')
                break  # Assuming you need the first match

    return net_qty

def place_order_api(data):
    login_username = os.getenv('LOGIN_USERNAME')
    AUTH_TOKEN = get_auth_token(login_username)
    BROKER_API_KEY = os.getenv('BROKER_API_KEY')
    data['apikey'] = BROKER_API_KEY
    token = get_token(data['symbol'], data['exchange'])
    newdata = transform_data(data, token)  
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = json.dumps({
        "quantity": newdata['quantity'],
        "product": newdata.get('product', 'I'),
        "validity": newdata.get('validity', 'DAY'),
        "price": newdata.get('price', '0'),
        "tag": newdata.get('tag', 'string'),
        "instrument_token": newdata['instrument_token'],
        "order_type": newdata.get('order_type', 'MARKET'),
        "transaction_type": newdata['transaction_type'],
        "disclosed_quantity": newdata.get('disclosed_quantity', '0'),
        "trigger_price": newdata.get('trigger_price', '0'),
        "is_amo": newdata.get('is_amo', 'false')
    })

    print(payload)

    conn = http.client.HTTPSConnection("api.upstox.com")
    conn.request("POST", "/v2/order/place", payload, headers)
    res = conn.getresponse()
    response_data = json.loads(res.read().decode("utf-8"))
    if response_data['status'] == 'success':
        orderid = response_data['data']['order_id']
    else:
        orderid = None
    return res, response_data, orderid

def place_smartorder_api(data):

    #If no API call is made in this function then res will return None
    res = None

    # Extract necessary info from data
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")
    position_size = int(data.get("position_size", "0"))

    

    # Get current open position for the symbol
    current_position = int(get_open_position(symbol, exchange, map_product_type(product)))


    #print(f"position_size : {position_size}") 
    #print(f"Open Position : {current_position}") 
    
    # Determine action based on position_size and current_position
    action = None
    quantity = 0


    # If both position_size and current_position are 0, do nothing
    if position_size == 0 and current_position == 0:
        action = data['action']
        quantity = data['quantity']
        #print(f"action : {action}")
        #print(f"Quantity : {quantity}")
        res, response, orderid = place_order_api(data)
        #print(res)
        #print(response)
        
        return res , response, orderid
        
    elif position_size == current_position:
        response = {"status": "success", "message": "No action needed. Position size matches current position."}
        orderid = None
        return res, response, orderid  # res remains None as no API call was mad
   
   

    if position_size == 0 and current_position>0 :
        action = "SELL"
        quantity = abs(current_position)
    elif position_size == 0 and current_position<0 :
        action = "BUY"
        quantity = abs(current_position)
    elif current_position == 0:
        action = "BUY" if position_size > 0 else "SELL"
        quantity = abs(position_size)
    else:
        if position_size > current_position:
            action = "BUY"
            quantity = position_size - current_position
            #print(f"smart buy quantity : {quantity}")
        elif position_size < current_position:
            action = "SELL"
            quantity = current_position - position_size
            #print(f"smart sell quantity : {quantity}")




    if action:
        # Prepare data for placing the order
        order_data = data.copy()
        order_data["action"] = action
        order_data["quantity"] = str(quantity)

        #print(order_data)
        # Place the order
        res, response, orderid = place_order_api(order_data)
        #print(res)
        #print(response)
        
        return res , response, orderid
    



def close_all_positions(current_api_key):
    # Fetch the current open positions
    positions_response = get_positions()

    
    # Check if the positions data is null or empty
    if positions_response['data'] is None or not positions_response['data']:
        return {"message": "No Open Positions Found"}, 200

    if positions_response['status']:
        # Loop through each position to close
        for position in positions_response['data']:
            # Skip if net quantity is zero
            if int(position['quantity']) == 0:
                continue

            # Determine action based on net quantity
            action = 'SELL' if int(position['quantity']) > 0 else 'BUY'
            quantity = abs(int(position['quantity']))

            
            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": position['tradingsymbol'],
                "action": action,
                "exchange": position['exchange'],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position['exchange'],position['product']),
                "quantity": str(quantity)
            }

            print(place_order_payload)

            # Place the order to close the position
            _, api_response, _ =   place_order_api(place_order_payload)

            print(api_response)
            
            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {'status': 'success', "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid):
    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = get_auth_token(os.getenv('LOGIN_USERNAME'))
    api_key = os.getenv('BROKER_API_KEY')
    
    # Set up the request headers
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
       
    }
    
    # Prepare the payload
    payload = json.dumps({
        "variety": "NORMAL",
        "order_id": orderid,
    })
    
    # Establish the connection and send the request
    conn = http.client.HTTPSConnection("api.upstox.com")  # Adjust the URL as necessary
    conn.request("DELETE", "/v2/order/cancel", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    
    # Check if the request was successful
    if data.get("status"):
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {"status": "error", "message": data.get("message", "Failed to cancel order")}, res.status


def modify_order(data):

    

    # Assuming you have a function to get the authentication token
    AUTH_TOKEN = get_auth_token(os.getenv('LOGIN_USERNAME'))
    api_key = os.getenv('BROKER_API_KEY')

    
    transformed_order_data = transform_modify_order_data(data)  # You need to implement this function
    
  
    # Set up the request headers
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = json.dumps(transformed_order_data)

    print(payload)

    conn = http.client.HTTPSConnection("api.upstox.com")
    conn.request("PUT", "/v2/order/modify", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    if data.get("status") == "success" or data.get("message") == "SUCCESS":
        return {"status": "success", "orderid": data["data"]["order_id"]}, 200
    else:
        return {"status": "error", "message": data.get("message", "Failed to modify order")}, res.status
    

def cancel_all_orders_api(data):
    # Get the order book
    order_book_response = get_order_book()
    print(order_book_response)
    if order_book_response['status'] != 'success':
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [order for order in order_book_response.get('data', [])
                        if order['status'] in ['open', 'trigger pending']]
    print(orders_to_cancel)
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order['order_id']
        cancel_response, status_code = cancel_order(orderid)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)
    
    return canceled_orders, failed_cancellations

