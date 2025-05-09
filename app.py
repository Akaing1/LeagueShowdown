from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Add this temporary route for testing
@app.route('/')
def home():
    return """
    <h1>Game Show API</h1>
    <p>Endpoints:</p>
    <ul>
        <li>POST /start-game/&lt;int&gt;</li>
        <li>POST /guess</li>
        <li>GET /hint</li>
        <li>GET /state</li>
    </ul>
    """


try:
    from src.core.game import GameShow
except ImportError as e:
    print(f"Import error: {e}")

    class GameShow:
        def __init__(self, players):
            self.players = players

        def start_game(self, index):
            return {"game": "Test", "status": "running"}

        def process_guess(self, idx, guess):
            return True, 100, "Test Answer"

        def reveal_hint(self):
            return "Test Hint"

        def get_game_state(self):
            return {"players": self.players}

game_show = GameShow(["Player1", "Player2", "Player3"])


@app.route('/start-game/<int:game_index>', methods=['POST'])
def start_game(game_index):
    try:
        game_data = game_show.start_game(game_index)
        return jsonify({"status": "success", "data": game_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/guess', methods=['POST'])
def process_guess():
    try:
        data = request.get_json()
        result = game_show.process_guess(data['contestant_index'], data['guess'])
        return jsonify({
            "status": "success",
            "data": {
                "correct": result[0],
                "points": result[1],
                "answer": result[2] if len(result) > 2 else None
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/hint', methods=['GET'])
def reveal_hint():
    try:
        hint = game_show.reveal_hint()
        return jsonify({"status": "success", "hint": hint})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/state', methods=['GET'])
def get_state():
    try:
        state = game_show.get_game_state()
        return jsonify({"status": "success", "state": state})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)
