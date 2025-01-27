public class SimilarityConfig
{
    public SimilarityMetricType DefaultMetric { get; set; } = SimilarityMetricType.Cosine;
    public Dictionary<string, SimilarityMetricType> DataTypeOverrides { get; } = new();
    public Dictionary<string, SimilarityMetricType> QueryTypeOverrides { get; } = new();
    public bool AutoNormalize { get; set; } = true;
} 