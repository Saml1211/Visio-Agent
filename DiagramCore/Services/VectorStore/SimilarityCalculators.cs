using System;

public class CosineSimilarityCalculator : ISimilarityCalculator
{
    public bool RequiresNormalization => true;
    
    public float Calculate(float[] a, float[] b)
    {
        float dot = 0, mag1 = 0, mag2 = 0;
        for (int i = 0; i < a.Length; i++)
        {
            dot += a[i] * b[i];
            mag1 += a[i] * a[i];
            mag2 += b[i] * b[i];
        }
        return dot / (MathF.Sqrt(mag1) * MathF.Sqrt(mag2));
    }
}

public class EuclideanDistanceCalculator : ISimilarityCalculator
{
    public bool RequiresNormalization => false;
    
    public float Calculate(float[] a, float[] b)
    {
        float sum = 0;
        for (int i = 0; i < a.Length; i++)
        {
            float diff = a[i] - b[i];
            sum += diff * diff;
        }
        return MathF.Sqrt(sum);
    }
} 