// Create websocket connection.
const ws = new WebSocket("ws://localhost:8000/ws");

let room_id;
let sign;

ws.onopen = () => {
  get_open_rooms();
};

ws.onmessage = (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "update_open_rooms":
      update_open_rooms(data.open_rooms);

      break;

    case "connected":
      room_id = data.room_id;
      sign = data.sign;

      go_to_room();
  }
};

function go_to_room() {
  // This function sets the client ui to in-room state.

  // Set ui state.
  document.body.className = "in-room";

  // Set current room_id
  document.getElementById("current_room_id").innerHTML = room_id;
}

function leave_room() {
  // This function sets the client ui to not-in-room state.

  // Set ui state.
  document.body.className = "not-in-room";

  ws.send(
    JSON.stringify({
      type: "disconnect",
      room_id: room_id,
      sign: sign,
    })
  );

  get_open_rooms();
}

function create_room() {
  ws.send(
    JSON.stringify({
      type: "create_room",
    })
  );
}

function connect_to_room() {
  // This function connects client to the room with specified room_id.

  // Get room_id.
  const input_value = document.getElementById("room_id").value;
  const room_id = Number(input_value);

  if (input_value != "" && room_id >= 0) {
    ws.send(
      JSON.stringify({
        type: "connect",
        room_id: room_id,
      })
    );
  } else {
    alert("Wrong room id!");
  }
}

function get_open_rooms() {
  ws.send(
    JSON.stringify({
      type: "get_open_rooms",
    })
  );
}

function update_open_rooms(open_rooms) {
  const open_rooms_el = document.getElementById("open-rooms");
  open_rooms_el.innerHTML = "";

  open_rooms.forEach((room_id) => {
    const room_el = document.createElement("li");
    room_el.innerHTML = `<button onclick="set_room_id(${room_id})">${room_id}</button>`;
    open_rooms_el.appendChild(room_el);
  });
}

function set_room_id(room_id) {
  // This function sets the value of the room_id input to the given room_id.

  // Get room_id input element.
  const room_id_el = document.getElementById("room_id");

  // Set value to given room_id.
  room_id_el.value = room_id;
}
