WEBSOCKET_CLIENTS = []

def subscribe_websocket_client(websocket_client, thread):
    ws_client_founded = False
    for ws_client in WEBSOCKET_CLIENTS:
        if websocket_client.client_id == ws_client[0].client_id:
            ws_client[1].append(thread)
            ws_client_founded = True
            break
    if not ws_client_founded:
        WEBSOCKET_CLIENTS.append([websocket_client, [thread]])
    print('%s subscribe websocket client' % (websocket_client.wss_route))

def unsubscribe_websocket_client(websocket_client, thread):
    for ws_client in WEBSOCKET_CLIENTS[:]:
        if not hasattr(websocket_client, 'client_id'):
            continue
        if ws_client[0].client_id == websocket_client.client_id:
            if thread is None:
                WEBSOCKET_CLIENTS.remove(ws_client)
            else:
                i = 0
                while i < len(ws_client[1]):
                    if ws_client[1][i]['operation'] == thread['operation'] and ws_client[1][i]['params'] == thread['params']:
                        ws_client[1].pop(i)
                        break
                    i = i + 1
            break
    print('%s unsusbcribe websocket client' % (websocket_client.wss_route))

