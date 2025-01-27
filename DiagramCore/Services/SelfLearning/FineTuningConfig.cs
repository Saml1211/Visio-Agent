public class FineTuningConfig
{
    public List<TriggerCondition> GlobalTriggers { get; } = new();
    public Dictionary<string, List<TriggerCondition>> TaskTriggers { get; } = new();
    public int MinimumSamples { get; set; } = 100;
    public TimeSpan CheckInterval { get; set; } = TimeSpan.FromHours(1);
} 