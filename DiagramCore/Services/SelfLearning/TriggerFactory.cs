using System;
using System.Collections.Generic;
using DiagramCore.Services.SelfLearning;

public class TriggerFactory
{
    private readonly FineTuningConfig _config;
    
    public TriggerFactory(FineTuningConfig config) => _config = config;
    
    public FineTuningMonitor CreateMonitor(string taskType, IMetricStore store, ILogger logger)
    {
        var conditions = new List<TriggerCondition>(_config.GlobalTriggers);
        
        if (_config.TaskTriggers.TryGetValue(taskType, out var taskConditions))
            conditions.AddRange(taskConditions);
            
        return new FineTuningMonitor(conditions, store, logger);
    }
} 