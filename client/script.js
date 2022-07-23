function debug(obj) {
    if (DEBUG) {
        console.log(obj);
    }
}

const DEBUG = true;

const ws = new WebSocket(`ws://rocky-hollows-30262.herokuapp.com/ws`);

let client_player;

function setPlayer(player) {
    const playerRow = document.getElementById('player');
    playerRow.innerText = player;
}

function setInfo(infoText) {
    const infoRow = document.getElementById("info");
    infoRow.innerText = infoText;
}

function cellClick(cellId) {
    ws.send(JSON.stringify({
        'player': client_player,
        'cell': cellId
    }));
}

function markCell(cellId, cells_color) {
    const cell = document.getElementById(cellId);
    cell.style.backgroundColor = cells_color;
}

function updateCell(cellId, player) {
    const cell = document.getElementById(cellId);
    cell.innerText = player;
}

ws.onmessage = function(e) {
    debug(e);

    const data = JSON.parse(e.data);
    
    if (data.type == 'connection') {
        client_player = data.player;
        setPlayer(client_player);
        
        if (client_player == 'x') {
            setInfo('Waiting for another player.');
        } else {
            setInfo('Opponent turn.');
        }
    } else if (data.type == 'start') {
        setInfo('Your turn.'); 
    } else if (data.type == 'turn') {
        updateCell(data.cell, data.player);
    } else if (data.type == 'win') {
        let cells_color;

        if (data.winner === client_player) {
            setInfo('You won!');
            alert('You won!');
            cells_color = 'green';
        } else {
            setInfo('You lose(');
            alert('You lose(');
            cells_color = 'red';
        }

        for (cellId of data.cells) {
            markCell(cellId, cells_color);
        }
    } else if (data.type == 'draw') {

    } else if (data.type == 'denied' && data.player == client_player) {
        setInfo(data.message);
    }
}

ws.onclose = function(e) {
    if (e.code == 4000) {
        setInfo('Game is already started.')
    }
}
