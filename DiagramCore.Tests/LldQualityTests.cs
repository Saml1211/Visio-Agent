using NUnit.Framework;
using System.IO;
using DiagramCore.Services.SelfLearning;
using System.Text;
using Microsoft.Extensions.Logging;

namespace DiagramCore.Tests
{
    [TestFixture]
    public class LldQualityTests
    {
        [Test]
        public void FeatureExtractor_Should_Calculate_Valid_Metrics()
        {
            var extractor = new LldFeatureExtractor();
            using var stream = File.OpenRead("test.vsdx");
            
            var features = extractor.ExtractFeatures(stream);
            
            Assert.Greater(features.ShapeCount, 0);
            Assert.Greater(features.ConnectorDensity, 0);
        }

        [Test]
        public void QualityModel_Should_Learn_From_Examples()
        {
            var examples = LoadTrainingData();
            var predictor = new LldQualityPredictor();
            predictor.Train(examples);
            
            var testFeatures = new LldFeatureVector { /*...*/ };
            var prediction = predictor.Predict(testFeatures);
            
            Assert.IsNotNull(prediction);
        }

        [Test]
        public void FeatureExtractor_InvalidFile_ReturnsInvalidVector()
        {
            var extractor = new LldFeatureExtractor(Mock.Of<ILogger<LldFeatureExtractor>>());
            using var stream = new MemoryStream(Encoding.UTF8.GetBytes("invalid"));
            
            var result = extractor.ExtractFeatures(stream);
            
            Assert.IsFalse(result.IsValid);
        }

        [Test]
        public void Model_HandlesInvalidFeatures_Gracefully()
        {
            var predictor = new LldQualityPredictor();
            var ex = Assert.Throws<ModelException>(() => 
                predictor.Predict(new LldFeatureVector { IsValid = false }));
            Assert.AreEqual("Invalid input features", ex.Message);
        }
    }
} 