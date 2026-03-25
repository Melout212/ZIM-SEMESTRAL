from flask import Flask, render_template, request, jsonify
from abc import ABC, abstractmethod
from datetime import datetime
import json
import os


class GameObserver(ABC):

    @abstractmethod
    def on_event(self, event, data):
        pass


class ScoreObserver(GameObserver):

    SCORE_FILE = "scores.json"

    def __init__(self):
        self.scores = self._load()

    def on_event(self, event, data):
        if event == "game_over":
            entry = {
                "name": data.get("name", "Anonym"),
                "score": data.get("score", 0),
                "level": data.get("level", 1),
                "asteroids": data.get("asteroids", 0),
                "date": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            self.scores.append(entry)
            self.scores.sort(key=lambda x: x["score"], reverse=True)
            self.scores = self.scores[:10]
            self._save()

    def get_top_scores(self):
        return self.scores

    def _load(self):
        if os.path.exists(self.SCORE_FILE):
            with open(self.SCORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)


class StatsObserver(GameObserver):

    STATS_FILE = "stats.json"

    def __init__(self):
        self.stats = self._load()

    def on_event(self, event, data):
        if event == "game_over":
            self.stats["total_games"] += 1
            self.stats["total_asteroids"] += data.get("asteroids", 0)
            self.stats["total_score"] += data.get("score", 0)
            if data.get("score", 0) > self.stats["best_score"]:
                self.stats["best_score"] = data.get("score", 0)
                self.stats["best_player"] = data.get("name", "Anonym")
            self._save()

    def get_stats(self):
        return self.stats

    def _load(self):
        if os.path.exists(self.STATS_FILE):
            with open(self.STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "total_games": 0,
            "total_asteroids": 0,
            "total_score": 0,
            "best_score": 0,
            "best_player": "-"
        }

    def _save(self):
        with open(self.STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)


class EventSystem:

    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        self._observers.append(observer)

    def notify(self, event, data={}):
        for observer in self._observers:
            observer.on_event(event, data)


class SpaceShooterApp:

    def __init__(self):
        self.app = Flask(__name__)
        self.events = EventSystem()
        self.score_observer = ScoreObserver()
        self.stats_observer = StatsObserver()
        self.events.subscribe(self.score_observer)
        self.events.subscribe(self.stats_observer)
        self._register_routes()

    def _register_routes(self):

        @self.app.route("/")
        def index():
            stats = self.stats_observer.get_stats()
            scores = self.score_observer.get_top_scores()
            return render_template("index.html", stats=stats, scores=scores)

        @self.app.route("/game")
        def game():
            name = request.args.get("name", "Hráč").strip() or "Hráč"
            return render_template("game.html", player_name=name)

        @self.app.route("/api/score", methods=["POST"])
        def save_score():
            data = request.get_json()
            if not data:
                return jsonify({"error": "Chybí data"}), 400
            self.events.notify("game_over", data)
            return jsonify({"status": "ok", "message": "Skóre uloženo!"})

        @self.app.route("/scores")
        def scores():
            top = self.score_observer.get_top_scores()
            stats = self.stats_observer.get_stats()
            return render_template("scores.html", scores=top, stats=stats)

    def run(self):
        print("=" * 45)
        print("  Space Shooter server běží!")
        print("  Otevři: http://localhost:5000")
        print("=" * 45)
        self.app.run(debug=True)


if __name__ == "__main__":
    server = SpaceShooterApp()
    server.run()
