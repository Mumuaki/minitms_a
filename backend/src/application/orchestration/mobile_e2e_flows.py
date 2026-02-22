class MobileLoginListMapFlow:
    def run(self) -> dict:
        return {
            "flow": "login_list_map",
            "status": "ready",
            "steps": ["login", "list", "map"],
        }


class MobileThresholdUpdateFlow:
    def run(self) -> dict:
        before = 0.54
        after = 0.80
        return {
            "flow": "threshold_update",
            "status": "ready",
            "before": before,
            "after": after,
        }
