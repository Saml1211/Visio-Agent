class AIMonitor:
    def track_improvement(self, before_metrics, after_metrics):
        """Calculate AI optimization impact"""
        return {
            'crossing_reduction': self._calc_reduction(
                before_metrics.crossings,
                after_metrics.crossings
            ),
            'compactness_improvement': self._calc_improvement(
                before_metrics.area,
                after_metrics.area
            )
        } 