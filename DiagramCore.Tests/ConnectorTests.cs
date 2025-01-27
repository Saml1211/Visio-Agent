using NUnit.Framework;
using DiagramCore.Connectors;
using DiagramCore.Shapes;

namespace DiagramCore.Tests
{
    [TestFixture]
    public class ConnectorTests
    {
        [Test]
        public void OrthogonalRouter_ShouldAvoidObstacles()
        {
            // Arrange
            var obstacles = new[] { new Shape(new Rect(50, 50, 100, 100)) };
            var router = new OrthogonalRouter();
            
            // Act
            var route = router.CalculateRoute(new Point(0, 0), new Point(200, 200), obstacles);
            
            // Assert
            Assert.That(route.Segments, Has.Count.GreaterThan(3));
            Assert.IsFalse(PathIntersectsShapes(route.GetFullPath(), obstacles));
        }
    }
} 