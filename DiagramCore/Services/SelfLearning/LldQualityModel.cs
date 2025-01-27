using Microsoft.ML;
using Microsoft.ML.Data;
using System;
using System.Collections.Generic;
using System.Linq;

public class LldQualityPredictor
{
    private readonly MLContext _mlContext;
    private ITransformer _model;
    
    public LldQualityPredictor()
    {
        _mlContext = new MLContext();
    }
    
    public void Train(IEnumerable<LldQualityExample> examples)
    {
        var dataView = _mlContext.Data.LoadFromEnumerable(examples);
        var pipeline = _mlContext.Transforms.Concatenate("Features", nameof(LldFeatureVector))
            .Append(_mlContext.BinaryClassification.Trainers.SdcaLogisticRegression());
            
        _model = pipeline.Fit(dataView);
    }
    
    public QualityPrediction Predict(LldFeatureVector features)
    {
        var predictionEngine = _mlContext.Model.CreatePredictionEngine<LldFeatureVector, QualityPrediction>(_model);
        return predictionEngine.Predict(features);
    }
}

public class QualityPrediction
{
    [ColumnName("PredictedLabel")]
    public bool IsGoodQuality { get; set; }
    
    public float Probability { get; set; }
    public float Score { get; set; }
} 