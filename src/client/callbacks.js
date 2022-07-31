function move(cell) {
  if (!is_allowed_to_move) return;

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

function leave_room() {
  // This function sets the client ui to not-in-room state.

  send_message({
    type: "leave_room",
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
