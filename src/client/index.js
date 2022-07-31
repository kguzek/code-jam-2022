// Create websocket connection.
const WS_HOST = document.domain;

const ws = new WebSocket(`ws://${WS_HOST}/ws`);

// Declare global variables.
let room_id;
let sign;

// This function will be called after websocket connection is accepted by server.
ws.onopen = () => {
  // Send request to get list of all open rooms.
  get_open_rooms();
};

ws.onmessage = (message) => {
  // This function processes all incoming messages from server depending on message type.

  // Get message data.
  const data = JSON.parse(message.data);

  switch (data.type) {
    // If server has sent a list of open rooms.
    case "update_open_rooms":
      // Update open rooms in ui.
      update_open_rooms(data.open_rooms);

      break;

    // If server successfuly created a room.
    case "create_room":
      // Set global variables.
      room_id = data.room_id;
      sign = data.sign;

      // Update ui to in-room state and set info.
      go_to_room();
      set_info("Waiting for second player...");

      break;

    case "join_room_error":
      alert(data.message);
      set_room_id_input("");

      break;

    case "start_game":
      set_info("Game is ready!");
      show_board();

      break;

    case "leave_room":
      document.body.className = "not-in-room";
      hide_board();

      get_open_rooms();
      set_room_id_input("");

      reset_room_info();

      reset_board();
      hide_board();

      break;

    case "player_disconnected":
      set_info("Your opponent has disconnected.");
      hide_board();

      reset_board();
      hide_board();

      break;
    case "update_board":
      const board = data.board;

      update_board(board);

      break;

    case "win":
      let cells_color;

      if (data.sign === sign) {
        set_info("You won!");
        cells_color = "green";
      } else {
        set_info("You lose(");
        cells_color = "red";
      }

      console.log(data);

      for (cellId of data.cells) {
        markCell(cellId, cells_color);
      }

      break;
  }
};

function send_message(message) {
  ws.send(JSON.stringify(message));
}

function get_open_rooms() {
  // This function sends message with type "update_open_rooms" to get list of all open rooms.

  send_message({
    type: "update_open_rooms",
  });
}

function update_open_rooms(open_rooms) {
  // This function updates list of open rooms in ui.

  const open_rooms_el = document.getElementById("open-rooms");
  open_rooms_el.innerHTML = "";

  open_rooms.forEach((room_id) => {
    const room_el = document.createElement("li");
    room_el.innerHTML = `<button onclick="set_room_id_input(${room_id})">${room_id}</button>`;
    open_rooms_el.appendChild(room_el);
  });
}

function create_room() {
  // This function sends message with type "create_room" to create room.

  send_message({
    type: "create_room",
  });
}

function join_room() {
  // This function connects client to the room with specified room_id.

  // Get room_id.
  const input_value = document.getElementById("room_id").value;
  const room_id = Number(input_value);

  if (input_value != "" && room_id >= 0) {
    send_message({
      type: "join_room",
      room_id: room_id,
    });
  } else {
    alert("Wrong room id!");
  }
}

function go_to_room() {
  // This function sets the client ui to in-room state.

  // Set ui state.
  document.body.className = "in-room";

  // Update ui.
  set_current_room_id(room_id);
  set_your_sign(sign);
  set_info("Waiting for second player...");
}

function leave_room() {
  // This function sets the client ui to not-in-room state.

  send_message({
    type: "leave_room",
  });
}

function reset_room_info() {
  room_id = null;
  sign = null;
}

function set_room_id_input(room_id) {
  // This function sets the value of the room_id input to the given room_id.
  const room_id_el = document.getElementById("room_id");
  room_id_el.value = room_id;
}

function set_current_room_id(room_id) {
  // This function sets the value of the room_id input to the given room_id.
  const current_room_id_el = document.getElementById("current_room_id");
  current_room_id_el.innerText = room_id;
}

function set_your_sign(sign) {
  // This function sets the current sign ui to the given sign.
  const your_sign_el = document.getElementById("your_sign");
  your_sign_el.innerText = sign;
}

function set_info(message) {
  // This function sets the info ui to the given info message.
  const info_el = document.getElementById("info");
  info_el.innerText = message;
}

function show_board() {
  const board_el = document.getElementById("board");
  board_el.className = "show";
}

function hide_board() {
  const board_el = document.getElementById("board");
  board_el.className = "";
}

function reset_board() {
  for (let i = 0; i <= 8; i++) {
    const cell_el = document.getElementById(i);
    cell_el.innerText = "*";
    cell_el.style.backgroundColor = "white";
  }
}

function move(cell) {
  const cell_el = document.getElementById(cell);

  if (cell_el.innerText == "*") {
    console.log({
      type: "move",
      room_id: room_id,
      sign: sign,
      cell: cell,
    });
    send_message({
      type: "move",
      room_id: room_id,
      sign: sign,
      cell: cell,
    });
  }
}

function update_board(board) {
  for (let i = 0; i <= 8; i++) {
    const cell_row = Math.floor(i / 3);
    const cell_col = i % 3;

    const cell_el = document.getElementById(i);
    cell_el.innerText = board[cell_row][cell_col];
  }
}

function markCell(cellId, cells_color) {
  const cell = document.getElementById(cellId);
  cell.style.backgroundColor = cells_color;
}
