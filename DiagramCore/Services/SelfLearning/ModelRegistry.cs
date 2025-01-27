using System;
using System.Collections.Concurrent;
using System.Linq;
using Microsoft.ML.Data;
using Microsoft.Extensions.Logging;

public class ModelRegistry : IModelRegistry
{
    private readonly ConcurrentDictionary<string, ModelVersion> _models = new();
    private readonly ILogger<ModelRegistry> _logger;
    
    public ModelRegistry(ILogger<ModelRegistry> logger)
    {
        _logger = logger;
    }
    
    public void RegisterModel(ITransformer model, string version, ModelMetrics metrics)
    {
        _models[version] = new ModelVersion(model, metrics, DateTime.UtcNow);
    }
    
    public ITransformer GetBestModel()
    {
        if (_models.IsEmpty)
            throw new InvalidOperationException("No models registered");
        
        return _models.Values
            .OrderByDescending(m => m.Metrics.F1Score)
            .ThenByDescending(m => m.DeploymentDate)
            .First().Model;
    }

    public void RollbackModel(string version)
    {
        if (_models.TryRemove(version, out _))
        {
            _logger.LogInformation($"Rolled back model version {version}");
        }
    }
} 