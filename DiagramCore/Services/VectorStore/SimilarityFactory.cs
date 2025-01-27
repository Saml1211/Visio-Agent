using System;
using System.Collections.Generic;

public class SimilarityFactory
{
    private readonly SimilarityConfig _config;

    public SimilarityFactory(SimilarityConfig config) => _config = config;

    public ISimilarityCalculator GetCalculator(string dataType, string queryType)
    {
        var metric = _config.DefaultMetric;
        
        if (_config.DataTypeOverrides.TryGetValue(dataType, out var dataMetric))
            metric = dataMetric;
        
        if (_config.QueryTypeOverrides.TryGetValue(queryType, out var queryMetric))
            metric = queryMetric;

        return metric switch
        {
            SimilarityMetricType.Cosine => new CosineSimilarityCalculator(),
            SimilarityMetricType.Euclidean => new EuclideanDistanceCalculator(),
            SimilarityMetricType.DotProduct => new DotProductCalculator(),
            SimilarityMetricType.Manhattan => new ManhattanDistanceCalculator(),
            SimilarityMetricType.Hybrid => new HybridSimilarityCalculator(),
            _ => throw new ArgumentOutOfRangeException()
        };
    }
    
    public float[] PreprocessVector(float[] vector, ISimilarityCalculator calculator)
    {
        if (calculator.RequiresNormalization && _config.AutoNormalize)
            return NormalizeVector(vector);
        return vector;
    }
} 