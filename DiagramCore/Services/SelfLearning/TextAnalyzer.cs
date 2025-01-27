using Microsoft.ML;
using Microsoft.ML.Data;
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using Microsoft.Extensions.Logging;

public class TextAnalyzer
{
    private readonly MLContext _mlContext;
    private ITransformer _textQualityModel;
    private readonly ILogger<TextAnalyzer> _logger;

    public TextAnalyzer(ILogger<TextAnalyzer> logger)
    {
        _mlContext = new MLContext();
        try
        {
            if (!File.Exists("Models/text_quality_model.zip"))
                throw new FileNotFoundException("Text quality model missing");
            
            _textQualityModel = _mlContext.Model.Load("Models/text_quality_model.zip", out _);
        }
        catch (Exception ex)
        {
            _logger.LogCritical($"Failed to load text model: {ex}");
            throw;
        }
    }

    public TextAnalysisResult Analyze(IEnumerable<string> textElements)
    {
        return new TextAnalysisResult
        {
            ConsistencyScore = CalculateConsistency(textElements),
            ReadabilityScore = CalculateReadability(textElements),
            TerminologyScore = CheckTerminology(textElements),
            SpellingErrors = DetectSpellingErrors(textElements)
        };
    }

    private float CalculateConsistency(IEnumerable<string> texts)
    {
        // Analyze font sizes, naming conventions, and labeling patterns
        var lengthVar = texts.Select(t => t.Length).Variance();
        var caseConsistency = texts.All(t => t == t.ToUpper()) ? 1 : 0;
        return 1 - (lengthVar * 0.1f + (1 - caseConsistency) * 0.9f);
    }

    private float CheckTerminology(IEnumerable<string> texts)
    {
        var predictionEngine = _mlContext.Model.CreatePredictionEngine<TextData, TextPrediction>(_textQualityModel);
        
        return texts.Average(t => 
        {
            var prediction = predictionEngine.Predict(new TextData { Content = t });
            return prediction.IsValid ? 1 : 0;
        });
    }
} 