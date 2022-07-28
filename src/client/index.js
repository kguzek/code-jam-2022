const INPUT_ROOM_ELEM = document.getElementById("roomid");
const DISPLAY_ROOM_ELEM = document.getElementById("displayRoom");
const CLIENTS_ELEM = document.getElementById("clients");

const WEBSOCKET_URL = "ws://localhost:8000/ws";

const ws = new WebSocket(WEBSOCKET_URL);

DEBUG_MODE = true;

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "transferred":
      // Do something with the room transfer
      DISPLAY_ROOM_ELEM.textContent = data.roomid;

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

const sendData = (data) => ws.send(JSON.stringify(data));

function debug(...msg) {
  if (!DEBUG_MODE) return;
  console.debug("CLIENT:", ...msg);
}

function addClientElem(client) {
  const elem = document.createElement("li");
  elem.textContent = client.name;
  elem.id = `client-${client.uuid}`;
  CLIENTS_ELEM.appendChild(elem);
}

function joinRoom() {
  const roomid = INPUT_ROOM_ELEM.value;
  sendData({ type: "transfer", roomid });
}

function createRoom() {
  sendData({ type: "join_room" });
}
