public enum PerformanceMetric
{
    Accuracy,
    ErrorRate,
    FeedbackScore,
    ResponseTime,
    DriftDetection
}

public class TriggerCondition
{
    public PerformanceMetric Metric { get; set; }
    public double Threshold { get; set; }
    public TimeSpan Window { get; set; }
    public ComparisonOperator Operator { get; set; }
}

public enum ComparisonOperator
{
    LessThan,
    GreaterThan,
    PercentageChange
}

public class MetricConfig
{
    public Dictionary<string, double> StyleWeights { get; set; } = new()
    {
        ["font"] = 0.3,
        ["line"] = 0.25,
        ["shape"] = 0.25,
        ["layout"] = 0.2
    };
    
    public Dictionary<string, int> PriorityLevels { get; set; } = new()
    {
        ["safety"] = 100,
        ["accessibility"] = 90,
        ["branding"] = 80,
        ["layout"] = 70
    };
} 