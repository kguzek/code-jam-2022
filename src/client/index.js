const INPUT_NAME_ELEM = document.getElementById("name");
const INPUT_ROOM_ELEM = document.getElementById("roomid");
const DISPLAY_NAME_ELEM = document.getElementById("displayName");
const DISPLAY_ROOM_ELEM = document.getElementById("displayRoom");
const CLIENTS_ELEM = document.getElementById("clients");

const WEBSOCKET_URL = "ws://localhost:8000/ws";

let ws;

function addClientElem(client) {
  const elem = document.createElement("li");
  elem.textContent = client.name;
  elem.id = `client-${client.uuid}`;
  CLIENTS_ELEM.appendChild(elem);
}

function connect() {
  const name = INPUT_NAME_ELEM.value;
  ws = new WebSocket(WEBSOCKET_URL + (name ? `?name=${name}` : ""));

  ws.onmessage = (event) => {
    let data = JSON.parse(event.data);

    switch (data.type) {
      case "transferred":
        room = data.roomid;
        // Do something with the room transfer
        DISPLAY_ROOM_ELEM.textContent = room;

        CLIENTS_ELEM.innerHTML = "";
        data.clients.forEach(addClientElem);
        break;

      case "new_connection":
        addClientElem(data.client);
        break;

      case "client_disconnected":
        const child = document.getElementById(`client-${data.uuid}`);
        try {
          CLIENTS_ELEM.removeChild(child);
        } catch (error) {
          console.error("Could not remove client from room.", data, error);
        }
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
  id = INPUT_ROOM_ELEM.value;
  if (!ws) return;
  ws.send(
    JSON.stringify({
      type: "transfer",
      roomid: id,
    })
  );
}
