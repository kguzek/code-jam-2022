# Docs for wsserver.py

## Class `Client`
### Args
    websocket: Websocket | The fastapi.WebSocket class.
    name: str | Name of the client. Needs to be alphanumeric and 3-20 characters long.
    room_id: int | ID of the room the client is connected to. Defaults to None.

### Methods
`await send_data(data) -> None`<br>

    data: dict | The json data that will be sent the the client

    Returns nothing.

`await accept() -> None`<br>

    Accepts the connection. Does not need to be used when using the connection manager.

    Returns nothing.

`await recieve_data() -> dict`<br>

    Returns the data that was sent by the client. Will be a dict.

<hr>

## Class `Room`
### Args
    id: int | The id of the room

### Methods
`add_client(client) -> None`<br>

    client: Client | The client to add to the room.

    Adds the client to the room.

`remove_client(client) -> None`<br>

    client: Client | The client to be removed from the room.

    Removes the client from the room.

`await broadcast(data) -> None`<br>

    data: dict | The data to be sent to all the clients.

    Sends the specified data to all the clients connected to the room.

<hr>

## Class `ConnectionManager`
### Methods
`await connect(websocket) -> Client`

    websocket: fastapi.WebSocket | The websocket of the client.

    Accepts the connection of the websocket and converts into Client.

`await disconnect(self, client) -> None`

    client: Client | Client to disconnect.

    Disconnects the client from the server.

`await transfer_client(client, room)`

    client: Client | The client to transfer
    room: Room | The room to transfer to

    Removes client from old room (if was connected), and connects to new room.

`get_room(id) -> Room`

    id: int | The id of the room

    Returns the Room with the id or creates it if it didn't exist.