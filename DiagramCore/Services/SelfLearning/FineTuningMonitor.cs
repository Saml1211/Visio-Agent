using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

public class FineTuningMonitor
{
    private readonly List<TriggerCondition> _conditions;
    private readonly IMetricStore _metricStore;
    private readonly ILogger _logger;
    
    public FineTuningMonitor(
        IEnumerable<TriggerCondition> conditions, 
        IMetricStore metricStore,
        ILogger logger)
    {
        _conditions = conditions.ToList();
        _metricStore = metricStore;
        _logger = logger;
    }
    
    public async Task CheckConditionsAsync()
    {
        foreach (var condition in _conditions)
        {
            var metricValues = await _metricStore.GetMetricsAsync(
                condition.Metric, 
                condition.Window);
                
            if (EvaluateCondition(metricValues, condition))
            {
                _logger.LogTriggerActivation(condition, metricValues);
                await ExecuteFineTuningAsync(condition);
            }
        }
    }
    
    private bool EvaluateCondition(IEnumerable<double> values, TriggerCondition condition)
    {
        return condition.Operator switch
        {
            ComparisonOperator.LessThan => values.Average() < condition.Threshold,
            ComparisonOperator.GreaterThan => values.Average() > condition.Threshold,
            ComparisonOperator.PercentageChange => 
                CalculatePercentageChange(values) > condition.Threshold,
            _ => false
        };
    }
} 