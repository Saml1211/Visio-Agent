public interface ISimilarityCalculator
{
    float Calculate(float[] vector1, float[] vector2);
    bool RequiresNormalization { get; }
}

public enum SimilarityMetricType
{
    Cosine,
    Euclidean,
    DotProduct,
    Manhattan,
    Hybrid
} 