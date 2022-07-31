function set_ui_state(ui_state) {
  document.body.className = ui_state;
}

function show_board() {
  const board_el = document.getElementById("board");
  board_el.style.display = "table";
}

function hide_board() {
  const board_el = document.getElementById("board");
  board_el.style.display = "none";
}

function reset_board() {
  for (let i = 0; i <= 8; i++) {
    const cell_el = document.getElementById(i);
    cell_el.innerText = "*";
    cell_el.style.backgroundColor = "white";
  }
}

function set_board(board) {
  for (let i = 0; i <= 8; i++) {
    const cell_row = Math.floor(i / 3);
    const cell_col = i % 3;

    const cell_el = document.getElementById(i);
    cell_el.innerText = board[cell_row][cell_col];
  }
}

function set_open_rooms(open_rooms) {
  // This function updates list of open rooms in ui.

  const open_rooms_el = document.getElementById("open-rooms");
  open_rooms_el.innerHTML = "";

  open_rooms.forEach((room_id) => {
    const room_el = document.createElement("li");
    room_el.innerHTML = `<button onclick="set_room_id_input(${room_id})">${room_id}</button>`;
    open_rooms_el.appendChild(room_el);
  });
}

function markCell(cellId, cells_color) {
  const cell = document.getElementById(cellId);
  cell.style.backgroundColor = cells_color;
}

function set_countdown(countdown) {
  const countdown_el = document.getElementById("countdown");
  countdown_el.innerText = `Countdown: ${countdown}`;
}

function set_room_id_input(room_id) {
  // This function sets the value of the room_id input to the given room_id.
  const room_id_el = document.getElementById("room_id");
  room_id_el.value = room_id;
}

function set_current_room_id(current_room_id) {
  // This function sets the value of the room_id input to the given room_id.
  const current_room_id_el = document.getElementById("current_room_id");
  current_room_id_el.innerText = `You are in room ${current_room_id}`;
}

function set_your_sign(your_sign) {
  // This function sets the current sign ui to the given sign.
  const your_sign_el = document.getElementById("your_sign");
  your_sign_el.innerText = `Your sign: ${your_sign}`;
}

function set_info(info_message) {
  // This function sets the info ui to the given info message.
  const info_el = document.getElementById("info");
  info_el.innerText = `Info: ${info_message}`;
}

function set_current_round(current_round) {
  const current_round_el = document.getElementById("current_round");
  current_round_el.innerText = `Current round: ${current_round} / 6`;
}

function show_current_round() {
  const current_round_el = document.getElementById("current_round");
  current_round_el.style.display = "block";
}

function hide_current_round() {
  const current_round_el = document.getElementById("current_round");
  current_round_el.style.display = "none";
}
