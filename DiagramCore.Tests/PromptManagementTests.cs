using NUnit.Framework;
using System.IO;

namespace DiagramCore.Tests
{
    [TestFixture]
    public class PromptManagementTests
    {
        private PromptManager _promptManager;

        [SetUp]
        public void Setup()
        {
            _promptManager = new PromptManager();
            _promptManager.LoadPrompts(Path.Combine("config", "prompts"));
        }

        [Test]
        public void Should_Load_Prompts_From_Directory()
        {
            Assert.That(_promptManager.GetPromptNames(), Contains.Item("code_generation"));
        }

        [Test]
        public void Should_Get_Latest_Version_By_Default()
        {
            var prompt = _promptManager.GetPrompt("code_generation");
            StringAssert.Contains("SOLID principles", prompt);
        }

        [Test]
        public void Should_Apply_Parameters_To_Template()
        {
            var result = _promptManager.RenderPrompt("code_generation", new()
            {
                ["language"] = "C#",
                ["requirements"] = "Implement repository pattern"
            });
            
            StringAssert.Contains("C# code that:\n- Implement repository pattern", result);
        }
    }
} 