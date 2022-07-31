// Create websocket connection.
const WS_HOST =
  document.domain === "127.0.0.1"
    ? "127.0.0.1:8000"
    : "online-tic-tac-toe-test.herokuapp.com";
const ws = new WebSocket(`ws://${WS_HOST}/ws`);

// Declare global variables.
let current_room_id;
let your_sign;
let is_allowed_to_move;
let countdown;

// This function will be called after websocket connection is accepted by server.
ws.onopen = () => {
  // Send message with type "get_open_rooms" to get list of all open rooms.
  send_message({
    type: "get_open_rooms",
  });
};

// This function processes all incoming messages from server depending on message type.
ws.onmessage = (message) => {
  // Get message data.
  const data = JSON.parse(message.data);

  switch (data.type) {
    // If server sent "update_open_rooms" message.
    case "update_open_rooms":
      // Update list of open rooms in ui.
      set_open_rooms(data.open_rooms);

      break;

    // If server successfuly created a room.
    case "create_room":
      // Set global variables.
      current_room_id = data.room_id;
      your_sign = data.sign;

      set_ui_state("in-room");

      set_current_room_id(current_room_id);
      set_your_sign(your_sign);
      set_info("Waiting for second player...");

      break;

    case "join_room":
      // Set global variables.
      current_room_id = data.room_id;
      your_sign = data.sign;

      // Update ui to in-room state and set info.
      set_ui_state("in-room");
      set_current_room_id(current_room_id);
      set_your_sign(your_sign);

      break;

    case "join_room_error":
      alert(data.message);
      set_room_id_input("");

      break;

    case "start_countdown":
      show_board();
      show_game_info();

      is_allowed_to_move = false;

      set_current_round(data.round);

      countdown = 3;
      set_info(countdown);

      const interval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          set_info(countdown);
        } else {
          clearInterval(interval);
        }
      }, 1000);
      setTimeout(() => {
        is_allowed_to_move = true;
        reset_board();
        set_info("GO!");
      }, 3000);

      break;

    case "leave_room":
      hide_board();
      reset_board();

      set_ui_state("not-in-room");

      current_room_id = null;
      your_sign = null;

      set_room_id_input("");

      break;

    case "player_disconnected":
      set_info("Your opponent has disconnected.");

      hide_board();
      reset_board();
      hide_game_info();

      break;

    case "update_board":
      set_board(data.board);

      break;

    case "win_round":
      let cells_color;

      if (data.sign === your_sign) {
        set_info("You won!");
        cells_color = "green";
      } else {
        set_info("You lose(");
        cells_color = "red";
      }

      for (cellId of data.cells) {
        markCell(cellId, cells_color);
      }

      break;
  }
};

function send_message(message) {
  ws.send(JSON.stringify(message));
}
