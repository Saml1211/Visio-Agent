export interface ModelMetrics {
    success_rate: number;
    avg_latency: number;
    name: string;
}

export interface PerformanceData {
    [key: string]: ModelMetrics;
} 