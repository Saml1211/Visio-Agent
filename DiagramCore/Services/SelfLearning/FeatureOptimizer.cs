using System.Linq;
using MathNet.Numerics.Statistics;
using System.Collections.Generic;

namespace DiagramCore.Services.SelfLearning
{
    public class FeatureOptimizer
    {
        private Dictionary<string, double> _featureImportance = new()
        {
            ["LayoutScore"] = 0.85,
            ["TextConsistencyScore"] = 0.78,
            // ... other features
        };

        public Dictionary<string, double> StyleWeights { get; } = new()
        {
            ["font_legibility"] = 0.25,
            ["color_contrast"] = 0.20,
            ["alignment_consistency"] = 0.18,
            ["spacing_uniformity"] = 0.15,
            ["brand_adherence"] = 0.12,
            ["accessibility"] = 0.10
        };

        public OptimizedFeatures Process(LldFeatureVector rawFeatures)
        {
            ValidateInput(rawFeatures);
            
            return new OptimizedFeatures {
                PrincipalComponents = ApplyPCA(NormalizeFeatures(rawFeatures)),
                ImportantFeatures = SelectImportantFeatures(rawFeatures)
            };
        }

        private void ValidateInput(LldFeatureVector features)
        {
            if (features.ShapeCount <= 0)
                throw new ArgumentException("Invalid shape count");
            
            if (features.ConnectorDensity < 0)
                throw new ArgumentException("Negative connector density");
        }

        private float[] ApplyPCA(LldFeatureVector features)
        {
            // Dimensionality reduction
            return _pcaModel.Transform(features);
        }

        private List<string> SelectImportantFeatures(LldFeatureVector features)
        {
            // Implementation using feature importance scores
            return _featureImportance
                .Where(kvp => kvp.Value > 0.1)
                .Select(kvp => kvp.Key)
                .ToList();
        }

        public StyleConfiguration Optimize(StyleMetrics metrics)
        {
            var score = CalculateCompositeScore(metrics);
            return new StyleConfiguration {
                FontScale = score > 0.8 ? 1.1 : 1.0,
                LineWeightBoost = score < 0.6 ? 1.15 : 1.0,
                ContrastEnhancement = metrics.AccessibilityScore < 4.5
            };
        }
        
        private double CalculateCompositeScore(StyleMetrics metrics) =>
            StyleWeights.Sum(kvp => kvp.Value * metrics.GetMetric(kvp.Key));
    }
}
