using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using DiagramCore.Services.VectorStore;

public class SimilarityBenchmark
{
    public record BenchmarkResult(
        string MetricName,
        float AverageScore,
        double QueryTimeMs,
        float RelevanceScore);
    
    public List<BenchmarkResult> RunBenchmarks(
        IEnumerable<float[]> queries,
        IEnumerable<float[]> documents,
        IEnumerable<ISimilarityCalculator> calculators)
    {
        var results = new List<BenchmarkResult>();
        
        foreach (var calculator in calculators)
        {
            var sw = Stopwatch.StartNew();
            var totalScore = 0f;
            var relevantMatches = 0;
            
            foreach (var query in queries)
            {
                foreach (var doc in documents)
                {
                    var score = calculator.Calculate(query, doc);
                    totalScore += score;
                    if (score > 0.8) relevantMatches++;
                }
            }
            
            sw.Stop();
            results.Add(new BenchmarkResult(
                calculator.GetType().Name,
                totalScore / (queries.Count() * documents.Count()),
                sw.Elapsed.TotalMilliseconds,
                relevantMatches / (float)documents.Count()
            ));
        }
        
        return results;
    }
} 