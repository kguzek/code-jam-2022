const NAME_ELEM = document.getElementById("name");
const DISPLAY_NAME_ELEM = document.getElementById("displayName");
const DISPLAY_ROOM_ELEM = document.getElementById("displayRoom");
const ROOM_ID_ELEM = document.getElementById("roomid");
const CLIENTS_ELEM = document.getElementById("clients");

const WEBSOCKET_URL = "ws://localhost:8000/ws";

let ws;

function addClientElem(clientText) {
  const elem = document.createElement("li");
  elem.textContent = clientText;
  CLIENTS_ELEM.appendChild(elem);
}

function connect() {
  const name = NAME_ELEM.value;
  ws = new WebSocket(WEBSOCKET_URL + (name ? `?name=${name}` : ""));

  ws.onmessage = (event) => {
    let data = JSON.parse(event.data);

    switch (data.type) {
      case "transferred":
        room = data.roomid;
        // Do something with the room transfer
        console.log("New room id: " + room);
        DISPLAY_ROOM_ELEM.textContent = room;

        CLIENTS_ELEM.innerHTML = "";
        console.log(data.clients);
        data.clients.forEach(addClientElem);
        break;

      case "new_connection":
        addClientElem(data.name);
        break;

      // TODO: Need to also make this in python
      case "client_disconnected":
        break;

      default:
        console.error("Unknown message type:", data.type);
        console.info(event);
    }
  };

  console.info("Connected as user:", name);
  DISPLAY_NAME_ELEM.textContent = name;
}

function transfer() {
  id = ROOM_ID_ELEM.value;
  if (!ws) return;
  ws.send(
    JSON.stringify({
      type: "transfer",
      roomid: id,
    })
  );
}
