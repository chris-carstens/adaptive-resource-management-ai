class MetricsCalculator:
    def calculate_error_rate(self, logs: list) -> float:
        if not logs:
            return 0.0
        error_count = sum(1 for log in logs if any('error' in value[1].lower() for value in log['values']))
        return (error_count / len(logs)) * 100

    def calculate_log_volume(self, logs: list) -> int:
        return sum(len(log['values']) for log in logs)
