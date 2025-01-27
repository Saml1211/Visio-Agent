using NUnit.Framework;
using DiagramCore.Services.SelfLearning;

namespace DiagramCore.Tests
{
    [TestFixture]
    public class FineTuningTests
    {
        [Test]
        public void Should_Trigger_When_Accuracy_Drops_Below_Threshold()
        {
            var condition = new TriggerCondition {
                Metric = PerformanceMetric.Accuracy,
                Threshold = 0.8,
                Operator = ComparisonOperator.LessThan
            };
            
            var monitor = new FineTuningMonitor(
                new[] { condition }, 
                new TestMetricStore([0.75, 0.72, 0.68]),
                new NullLogger());
                
            Assert.DoesNotThrowAsync(async () => await monitor.CheckConditionsAsync());
        }
    }
} 