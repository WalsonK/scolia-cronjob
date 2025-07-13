import json
from pathlib import Path
from collections import defaultdict
import statistics

def generate_all_user_params(log_directory: str = "datas/logs", stable_threshold: float = 0.01):
    user_data = defaultdict(lambda: {
        "retriever_top_k": [],
        "llm_params": defaultdict(list)
    })

    for log_file in Path(log_directory).glob("*.json"):
        try:
            with open(log_file, "r", encoding="utf-8") as file:
                log = json.load(file)
        except (json.JSONDecodeError, OSError):
            print(f"⚠️ Erreur de lecture du fichier : {log_file}")
            continue

        user_id = log.get("user_id")
        if not user_id:
            continue

        retriever = log.get("retriever_parameters", {})
        top_k = retriever.get("top_k")
        if isinstance(top_k, (int, float)):
            user_data[user_id]["retriever_top_k"].append(top_k)

        llm = log.get("llm_parameters", {})
        for param in ["temperature", "top_p", "frequency_penalty", "presence_penalty"]:
            value = llm.get(param)
            if isinstance(value, (int, float)):
                user_data[user_id]["llm_params"][param].append(value)

    with open("datas/params/default_params.json", "r", encoding="utf-8") as f:
        default_params = json.load(f)

    default_values = default_params.get("llm", {
        "temperature": 1.0,
        "top_p": 1.0,
        "presence_penalty": 0.0
    })

    for user, data in user_data.items():
        # Traitement retriever
        top_ks = data["retriever_top_k"]
        avg_top_k = round(sum(top_ks) / len(top_ks)) if top_ks else 5

        # Traitement LLM
        llm_params = {}

        for param in default_values:
            values = data["llm_params"][param]
            if not values:
                llm_params[param] = default_values[param]
                continue

            if len(values) == 1:
                llm_params[param] = round(values[0], 3)
                continue

            try:
                stddev = statistics.stdev(values)
            except statistics.StatisticsError:
                stddev = 0.0

            if stddev < stable_threshold:
                # Valeurs stables → moyenne
                mean_val = sum(values) / len(values)
                llm_params[param] = round(mean_val, 2)
            else:
                # Valeurs dispersées → médiane
                median_val = statistics.median(values)
                llm_params[param] = round(median_val, 2)

        # Génération du fichier
        optimized_params = {
            "llm": llm_params,
            "retriever": {
                "top_k": avg_top_k
            }
        }

        user_params_path = Path(f"models/params_{user}.json")
        user_params_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_params_path, "w", encoding="utf-8") as f:
            json.dump(optimized_params, f, indent=4, ensure_ascii=False)
        print(f"[✓] Généré : models/params_{user}.json")

