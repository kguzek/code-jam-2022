// Create websocket connection.
const WS_HOST =
  document.domain === "127.0.0.1"
    ? "127.0.0.1:8000"
    : "online-tic-tac-toe-test.herokuapp.com";
const ws = new WebSocket(`ws://${WS_HOST}/ws`);

// Declare global variables.
let current_room_id;
let your_sign;

// This function will be called after websocket connection is accepted by server.
ws.onopen = () => {
  // Send message with type "get_open_rooms" to get list of all open rooms.
  get_open_rooms();
};

// This function processes all incoming messages from server depending on message type.
ws.onmessage = (message) => {
  // Get message data.
  const data = JSON.parse(message.data);

  switch (data.type) {
    // If server sent "update_open_rooms" message.
    case "update_open_rooms":
      // Update list of open rooms in ui.
      update_open_rooms(data.open_rooms);

      break;

    // If server successfuly created a room.
    case "create_room":
      // Set global variables.
      current_room_id = data.room_id;
      your_sign = data.sign;

      set_ui("in-room");

      set_current_room_id(current_room_id);
      set_your_sign(your_sign);
      set_info("Waiting for second player...");

      break;

    case "join_room":
      // Set global variables.
      current_room_id = data.room_id;
      your_sign = data.sign;

      // Update ui to in-room state and set info.
      set_ui("in-room");

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

      if (data.sign === your_sign) {
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
    type: "get_open_rooms",
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

function set_ui(ui_state) {
  document.body.className = ui_state;
}

function leave_room() {
  // This function sets the client ui to not-in-room state.

  send_message({
    type: "leave_room",
  });
}

function reset_room_info() {
  current_room_id = null;
  your_sign = null;
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
      room_id: current_room_id,
      sign: your_sign,
      cell: cell,
    });
    send_message({
      type: "move",
      room_id: current_room_id,
      sign: your_sign,
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
