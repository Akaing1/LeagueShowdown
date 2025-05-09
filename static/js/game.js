const { createApp } = Vue;

createApp({
    data() {
        return {
            contestants: [],
            currentGame: "",
            gameType: "",
            revealedHints: [],
            emojiSequence: "",
            currentGuess: "",
            lastResult: ""
        };
    },
    async mounted() {
        await this.fetchGameState();
        // Start with WhoAmI game (index 0)
        this.startGame(0);
    },
    methods: {
        async fetchGameState() {
            try {
                const response = await fetch('/state');
                const data = await response.json();
                if (data.status === "success") {
                    this.contestants = data.state.contestants;
                    this.currentGame = data.state.game;
                    this.gameType = this.currentGame.includes("Who") ? "WhoAmI" : "EmoGG";

                    if (data.state.game_specific) {
                        if (this.gameType === "WhoAmI") {
                            this.revealedHints = data.state.game_specific.revealed_hints || [];
                        } else if (this.gameType === "EmoGG") {
                            this.emojiSequence = data.state.game_specific.emoji_sequence || "";
                        }
                    }
                }
            } catch (error) {
                console.error("Error fetching game state:", error);
            }
        },
        async startGame(gameIndex) {
            try {
                const response = await fetch(`/start-game/${gameIndex}`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.status === "success") {
                    this.currentGame = data.data.theme || "EmoGG Game";
                    this.gameType = gameIndex === 0 ? "WhoAmI" : "EmoGG";

                    if (this.gameType === "EmoGG") {
                        this.emojiSequence = data.data.emoji_sequence;
                    }

                    this.revealedHints = [];
                    this.lastResult = "";
                    await this.fetchGameState();
                }
            } catch (error) {
                console.error("Error starting game:", error);
            }
        },
        async getHint() {
            try {
                const response = await fetch('/hint');
                const data = await response.json();
                if (data.status === "success" && data.hint) {
                    this.revealedHints.push(data.hint);
                }
            } catch (error) {
                console.error("Error getting hint:", error);
            }
        },
        async submitGuess() {
            if (!this.currentGuess.trim()) return;

            try {
                // For simplicity, we'll always use contestant 0 in this example
                // In a real app, you'd track the current player
                const response = await fetch('/guess', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        contestant_index: 0,
                        guess: this.currentGuess
                    })
                });

                const data = await response.json();
                if (data.status === "success") {
                    this.lastResult = `${data.data.contestant} guessed ${data.data.correct ? "correctly" : "wrongly"}! (${data.data.points} points)`;
                    this.currentGuess = "";
                    await this.fetchGameState();

                    // Auto-advance to next round after a delay
                    if (data.data.correct) {
                        setTimeout(async () => {
                            const stateResponse = await fetch('/state');
                            const stateData = await stateResponse.json();
                            if (stateData.status === "success") {
                                if (stateData.state.game_specific?.round_number === stateData.state.game_specific?.total_rounds) {
                                    // Move to next game
                                    this.startGame(1); // Move to EmoGG
                                }
                            }
                        }, 2000);
                    }
                }
            } catch (error) {
                console.error("Error submitting guess:", error);
            }
        }
    }
}).mount('.container');