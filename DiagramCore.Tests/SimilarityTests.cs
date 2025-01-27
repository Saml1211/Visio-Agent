using NUnit.Framework;
using DiagramCore.Services.VectorStore;

namespace DiagramCore.Tests
{
    [TestFixture]
    public class SimilarityTests
    {
        private float[] _vectorA = [0.5f, 0.5f];
        private float[] _vectorB = [0.5f, 0.5f];
        
        [Test]
        public void Cosine_IdenticalVectors_ReturnsOne()
        {
            var calculator = new CosineSimilarityCalculator();
            Assert.AreEqual(1.0f, calculator.Calculate(_vectorA, _vectorB), 0.001);
        }

        [Test]
        public void Euclidean_IdenticalVectors_ReturnsZero()
        {
            var calculator = new EuclideanDistanceCalculator();
            Assert.AreEqual(0.0f, calculator.Calculate(_vectorA, _vectorB), 0.001);
        }
    }
} 