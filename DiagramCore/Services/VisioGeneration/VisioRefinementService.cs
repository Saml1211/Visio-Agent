using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using DiagramCore.Services.SelfLearning;

public class VisioRefinementService
{
    private readonly LldQualityPredictor _qualityPredictor;
    private readonly LldFeatureExtractor _featureExtractor;
    
    public async Task<VisioRefinementResult> RefineDiagram(Stream vsdxFile)
    {
        var features = _featureExtractor.ExtractFeatures(vsdxFile);
        var prediction = _qualityPredictor.Predict(features);
        
        if (!prediction.IsGoodQuality)
        {
            var feedback = GenerateImprovementFeedback(features, prediction);
            return new VisioRefinementResult
            {
                QualityScore = prediction.Probability,
                NeedsImprovement = true,
                Feedback = feedback
            };
        }
        
        return new VisioRefinementResult { QualityScore = prediction.Probability };
    }
    
    private List<string> GenerateImprovementFeedback(LldFeatureVector features, QualityPrediction prediction)
    {
        var feedback = new List<string>();
        
        if (features.ConnectorDensity > 0.3)
            feedback.Add("Reduce connector density by grouping related components");
            
        if (features.TextConsistencyScore < 0.5)
            feedback.Add("Improve labeling consistency across diagram elements");
            
        return feedback;
    }
} 