// Connect to the server through websocket connection.
const WEBSOCKET_URL = "ws://localhost:8000/ws";
const ws = new WebSocket(WEBSOCKET_URL);

const DEBUG = true;

get_rooms();

function update_rooms(room_ids) {
  const rooms_el = document.getElementById("rooms");

  rooms_el.innerHTML = "";

  room_ids.forEach((room_id) => {
    const room_el = document.createElement("li");

    room_el.innerHTML = `
    <button>${room_id}</button>
    `;

    rooms_el.appendChild(room_el);
  });
}

function get_rooms() {
  setTimeout(() => {
    ws.send(
      JSON.stringify({
        type: "get_rooms",
      })
    );
  }, 1000);
}

const INPUT_NAME_ELEM = document.getElementById("name");
const INPUT_ROOM_ELEM = document.getElementById("roomid");
const DISPLAY_NAME_ELEM = document.getElementById("displayName");
const DISPLAY_ROOM_ELEM = document.getElementById("displayRoom");
const CLIENTS_ELEM = document.getElementById("clients");

function debug(...args) {
  if (DEBUG) {
    console.warn(...args);
  }
}

function addClientElem(client) {
  const elem = document.createElement("li");
  elem.textContent = client.name;
  elem.id = `client-${client.uuid}`;
  CLIENTS_ELEM.appendChild(elem);
}

function createRoom() {
  debug("CLIENT:", "create_room");

  ws.send(
    JSON.stringify({
      type: "create_room",
    })
  );

  get_rooms();
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "debug") {
    debug("SERVER:", data.message);
  } else {
    console.log(event);
  }

  switch (data.type) {
    case "transferred":
      room = data.roomid;
      // Do something with the room transfer
      DISPLAY_ROOM_ELEM.textContent = room;

      CLIENTS_ELEM.innerHTML = "";
      data.clients.forEach(addClientElem);
      break;

    case "get_rooms":
      debug("CLIENT: rooms:", data.rooms);
      update_rooms(data.rooms);

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

    case "create_room":
      const room_id = data.room_id;

      debug("CLIENT:", `room_id: ${room_id}`);

      break;
  }
};

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
