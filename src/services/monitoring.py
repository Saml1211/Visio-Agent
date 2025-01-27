class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'deepseek': {'latency': [], 'success_rate': 0},
            'gemini': {'latency': [], 'success_rate': 0},
            'openai': {'latency': [], 'success_rate': 0}
        }
        
    def update_metrics(self, result: dict):
        model = result['model']
        if result['error']:
            self.metrics[model]['success_rate'] *= 0.95
        else:
            self.metrics[model]['latency'].append(result['latency'])
            self.metrics[model]['success_rate'] = 0.95 * self.metrics[model]['success_rate'] + 0.05
            
    def get_metrics(self):
        return {
            m: {
                'avg_latency': np.mean(data['latency']),
                'success_rate': data['success_rate']
            }
            for m, data in self.metrics.items()
        } 